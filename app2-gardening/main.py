import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from traceloop.sdk.decorators import workflow

from shared.telemetry import init_telemetry
from shared.llm_client import complete
from weather import geocode, get_weather, get_season

tracer = init_telemetry()

app = FastAPI(title="Gardening Advisor")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


class AdviseRequest(BaseModel):
    location: str
    question: str


@app.get("/")
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/advise")
@workflow(name="gardening-advice")
async def advise(req: AdviseRequest):
    if not req.location.strip():
        raise HTTPException(status_code=400, detail="Location is required")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    # Step 1-2: Geocode and fetch weather
    geo = await geocode(req.location)
    if geo is None:
        raise HTTPException(status_code=404, detail=f"Location '{req.location}' not found")

    weather = await get_weather(geo["latitude"], geo["longitude"])
    season = get_season(geo["latitude"])

    # Step 3: Assemble prompt (manual span)
    with tracer.start_as_current_span("assemble-prompt") as span:
        span.set_attribute("location", geo["name"])
        span.set_attribute("season", season)

        weather_context = (
            f"Location: {geo['name']}, {geo.get('country', '')}\n"
            f"Season: {season}\n"
            f"Temperature: {weather.get('temperature', 'N/A')}°C\n"
            f"Humidity: {weather.get('humidity', 'N/A')}%\n"
            f"Precipitation: {weather.get('precipitation', 'N/A')} mm\n"
            f"Wind speed: {weather.get('wind_speed', 'N/A')} km/h"
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert gardening advisor. Use the provided weather data "
                    "and season to give specific, actionable gardening advice. "
                    "Be practical and consider the local climate conditions."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Current conditions:\n{weather_context}\n\n"
                    f"My question: {req.question}"
                ),
            },
        ]

    # Step 4: Call LLM
    result = await complete(messages)

    return {
        "advice": result["content"],
        "weather": {
            "location": geo["name"],
            "country": geo.get("country", ""),
            "season": season,
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "precipitation": weather.get("precipitation"),
            "wind_speed": weather.get("wind_speed"),
        },
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }
