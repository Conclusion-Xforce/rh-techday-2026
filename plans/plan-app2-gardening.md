# Plan: App 2 - Gardening Advisor

Plan the implementation of `app2-gardening/`, the second of three workshop demo apps. This app adds an external API dependency to create a more interesting distributed trace.

## What this app does

The user enters a location (city or region). The app fetches live weather data from the Open-Meteo API, determines the current season from the date, and sends both as context to the model along with the user's gardening question. The result is tailored planting and care advice.

## Why the external API matters

This app exists to show a distributed trace that includes an outbound HTTP call alongside the LLM inference call. In Dynatrace, the facilitator can show external dependency latency, compare it to inference latency, and demonstrate what happens when the external service is slow or fails. This is standard APM territory, applied to an AI app.

## Desired trace shape

```
[FastAPI request span]
  ├── [HTTP GET to Open-Meteo API]
  ├── [prompt assembly (manual span)]
  └── [LLM inference span via openllmetry]
```

5 spans, 2 external dependencies (weather API + inference service).

## Requirements

### Backend (Python/FastAPI)
- POST endpoint: `/api/advise` accepts `{ "location": "Utrecht", "question": "What can I plant now?" }`
- Step 1: Geocode the location to lat/lon using Open-Meteo's geocoding API (`https://geocoding-api.open-meteo.com/v1/search?name={location}`)
- Step 2: Fetch current weather using Open-Meteo weather API (`https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m`)
- Step 3: Determine season from current date and hemisphere (latitude sign)
- Step 4: Construct a prompt that includes: location name, current weather conditions (temperature, humidity, precipitation, wind), season, and the user's question
- Step 5: Call vLLM via the openai SDK
- Step 6: Return the model response as JSON along with the weather data used (so the frontend can display it)
- A GET endpoint `/api/health` for readiness checks
- Use httpx (async) for all outbound HTTP calls

### Frontend (static HTML)
- Single `index.html` served by FastAPI at `/`
- Input: text field for location, text field for gardening question (with placeholder examples)
- Button: "Get Advice"
- Output area split into two parts:
  - Weather context box: shows the fetched weather data (temperature, humidity, season) so the participant can see what context the model received
  - Advice area: the model's response
- Loading state while waiting
- Clean, minimal UI. No framework. Vanilla HTML/CSS/JS.

### Observability
- FastAPI auto-instrumentation via `opentelemetry-instrumentation-fastapi`
- httpx auto-instrumentation via `opentelemetry-instrumentation-httpx` (captures the Open-Meteo calls)
- LLM call instrumented via openllmetry: model name, token counts, latency
- Add a manual span around the prompt assembly step (after weather fetch, before LLM call) to make the trace more readable. Span name: `assemble-prompt`
- OTLP export to Dynatrace
- Service name: `gardening-advisor`

### Error handling
- If geocoding fails (location not found): return a clear error, do not call the model
- If weather API fails: return advice anyway but note that weather data was unavailable. Add an error attribute to the weather span.
- If model call fails: return error with the weather data that was successfully fetched

### Project structure
```
app2-gardening/
  main.py              # FastAPI app, routes, OTel setup
  weather.py           # Open-Meteo client (geocoding + weather)
  static/
    index.html          # Frontend
  requirements.txt
  README.md
```

## Shared dependencies
- Import OTel initialization from `shared/telemetry.py`
- Import the model client wrapper from `shared/llm_client.py`

## What NOT to build
- No authentication
- No database or persistence
- No conversation history
- No caching of weather responses (we want every request to hit the API so it shows up in traces)
- No streaming responses
