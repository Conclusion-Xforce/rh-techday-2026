import sys
from pathlib import Path

# Allow importing shared when running outside Docker
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from shared.telemetry import init_telemetry
from shared.llm_client import complete

tracer = init_telemetry()

app = FastAPI(title="Recipe Generator")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


class GenerateRequest(BaseModel):
    ingredients: list[str]


@app.get("/")
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    if not req.ingredients:
        raise HTTPException(status_code=400, detail="At least one ingredient is required")

    ingredients_text = ", ".join(req.ingredients)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a creative recipe generator. Given a list of ingredients, "
                "create a recipe. Respond in JSON with keys: title (string), "
                "ingredients (list of strings with quantities), steps (list of strings). "
                "Only output valid JSON, no extra text."
            ),
        },
        {
            "role": "user",
            "content": f"Create a recipe using these ingredients: {ingredients_text}",
        },
    ]

    result = await complete(messages)
    return {
        "recipe": result["content"],
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }
