# Plan: Shared Module and Infrastructure

Plan the implementation of `shared/` (common code used by all three apps) and `infra/` (Docker Compose and database initialization).

## shared/

### shared/telemetry.py
A single function that all three apps call at startup to initialize OpenTelemetry.

- Configures OTLP exporter (endpoint and headers from env vars)
- Sets up TracerProvider with the service name from `OTEL_SERVICE_NAME`
- Registers auto-instrumentors: FastAPI, httpx, psycopg2 (each only if the relevant package is installed, so App 1 does not fail because psycopg2 is not in its requirements)
- Initializes openllmetry (Traceloop) for LLM span capture
- Supports a `console` exporter mode for local development (`OTEL_EXPORTER=console`)
- Returns a tracer instance for manual span creation

Usage in each app:
```python
from shared.telemetry import init_telemetry
tracer = init_telemetry()
```

### shared/llm_client.py
A thin wrapper around the openai SDK configured for vLLM.

- Reads `VLLM_BASE_URL` and `VLLM_MODEL` from env
- Exposes an async function: `async def complete(messages: list[dict], temperature: float = 0.7) -> dict`
- Returns a dict with: `content` (the response text), `input_tokens`, `output_tokens`, `model`
- Handles timeouts and retries (one retry with backoff)
- Does NOT do its own OTel instrumentation (openllmetry handles that)

Usage in each app:
```python
from shared.llm_client import complete
result = await complete(messages=[
    {"role": "system", "content": "You are a recipe generator."},
    {"role": "user", "content": "Make a recipe with chicken, lemon, garlic"}
])
```

### shared/pyproject.toml or shared/setup.py
Make `shared` installable as a local package so apps can `pip install -e ../shared` or use `pip install -e ".[dev]"` from the root.

### Project structure
```
shared/
  __init__.py
  telemetry.py
  llm_client.py
  pyproject.toml
```

## infra/

### infra/docker-compose.yml
Runs the full workshop stack locally for development and testing.

Services:
- `db`: PostgreSQL 16, port 5432, with `infra/init.sql` mounted as init script
- `app1`: App 1 (Recipe Generator), port 8001
- `app2`: App 2 (Gardening Advisor), port 8002
- `app3`: App 3 (Chatbot), port 8003, depends on `db`
- `otel-collector` (optional): OpenTelemetry Collector for local span debugging, port 4317 (gRPC) and 4318 (HTTP). Receives OTLP and exports to stdout. Only needed for local dev; in the workshop, apps export directly to Dynatrace.

All app services:
- Build from their respective directories
- Mount `shared/` as a volume or install it in the Dockerfile
- Load env from `infra/.env` (with overrides in `infra/.env.local`)

### infra/.env.example
Template with all required env vars, commented with descriptions.

### infra/init.sql
- Creates the database schema (users, sessions, conversations tables)
- Seeds 30 participant accounts (participant01 through participant30)
- All passwords: `techday2026` (bcrypt hashed)
- Display names: "Participant 1" through "Participant 30"

### infra/Dockerfile.app
A single multi-stage Dockerfile that works for all three apps. Accepts a build arg for which app to build:
```dockerfile
ARG APP_DIR=app1-recipes
COPY ${APP_DIR}/requirements.txt .
COPY shared/ ./shared/
COPY ${APP_DIR}/ ./app/
```

### Project structure
```
infra/
  docker-compose.yml
  Dockerfile.app
  .env.example
  init.sql
  otel-collector-config.yml   # Config for the local OTel collector
```

## Root files

### README.md
- Project overview (one paragraph)
- Quickstart: `cp infra/.env.example infra/.env`, edit the vLLM URL, `docker compose up`
- Links to each app's README for details
- Architecture diagram (reference docs/architecture.md)

### pyproject.toml or requirements-dev.txt
- Dev dependencies: pytest, httpx (for test client), ruff (linting)

### .gitignore
- Standard Python: __pycache__, *.pyc, .venv, .env
- infra/.env and infra/.env.local
