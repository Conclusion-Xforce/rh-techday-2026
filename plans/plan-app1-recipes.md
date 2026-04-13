# Plan: App 1 - Recipe Generator

Plan the implementation of `app1-recipes/`, the simplest of three workshop demo apps.

## What this app does

A stateless web app where the user enters a few ingredients and gets back a recipe. No auth, no database, no external API calls. This is the observability baseline: its traces should be clean and uniform so the Dynatrace dashboards can contrast it against the more complex apps.

## Desired trace shape

```
[FastAPI request span]
  └── [LLM inference span via openllmetry]
```

2 spans, 1 service. That is it. The simplest possible AI app trace.

## Requirements

### Backend (Python/FastAPI)
- Single POST endpoint: `/api/generate` accepts `{ "ingredients": ["chicken", "lemon", "garlic"] }`
- Constructs a system prompt that instructs the model to return a structured recipe (title, ingredients with quantities, steps)
- Calls vLLM via the openai SDK (OpenAI-compatible endpoint, base URL from env)
- Returns the model response as JSON
- A GET endpoint `/api/health` for readiness checks

### Frontend (static HTML)
- Single `index.html` served by FastAPI at `/`
- Input: text field where user types or comma-separates ingredients
- Button: "Generate Recipe"
- Output: rendered recipe (title, ingredients list, steps)
- Loading state while waiting for the model
- Clean, minimal UI. No framework. Vanilla HTML/CSS/JS.
- The UI should look polished enough for a live demo but not over-designed

### Observability
- FastAPI auto-instrumentation via `opentelemetry-instrumentation-fastapi`
- LLM call instrumented via openllmetry (Traceloop SDK): must capture model name, token counts (input/output), latency
- OTLP export to Dynatrace (endpoint + headers from env)
- Service name: `recipe-generator`

### Project structure
```
app1-recipes/
  main.py              # FastAPI app, routes, OTel setup
  static/
    index.html          # Frontend
  requirements.txt
  README.md
```

## Shared dependencies
- Import OTel initialization from `shared/telemetry.py` (plan this module too if it does not exist yet)
- Import the model client wrapper from `shared/llm_client.py`

## What NOT to build
- No authentication
- No database
- No conversation history
- No streaming responses (keep it simple: wait for full completion)
- No rate limiting (the inference service handles its own queueing)
