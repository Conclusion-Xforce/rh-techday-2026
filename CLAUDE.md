# Red Hat Tech Day Workshop: Observing AI in Production

Monorepo for three demo apps used in a 90-minute hands-on workshop (3 June 2026). All apps call the same centralized vLLM inference service and are instrumented with OpenTelemetry for Dynatrace observability.

## Purpose

Demonstrate escalating architectural complexity across three AI-powered apps so Dynatrace traces tell visibly different stories: from a simple stateless call, to external API dependencies, to full auth + database persistence.

## Architecture

```
workshop-otel-ai/
  app1-recipes/       # Stateless. Ingredients in, recipe out. 2 spans.
  app2-gardening/     # External dep. Calls Open-Meteo weather API. 5 spans.
  app3-chatbot/       # Full production. Auth + PostgreSQL + growing history. 6 spans.
  shared/             # Shared OTel config, model client, utilities
  infra/              # Docker Compose, env templates, DB init scripts
  docs/               # Workshop cheat sheet, architecture diagrams
```

## Stack

- Python 3.12, FastAPI, uvicorn
- openai SDK (vLLM exposes an OpenAI-compatible API)
- opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-httpx, opentelemetry-instrumentation-psycopg2
- openllmetry-sdk (Traceloop) for LLM-specific spans
- httpx for outbound HTTP (App 2 weather API)
- psycopg2 + SQLAlchemy for PostgreSQL (App 3)
- Simple HTML/JS frontends (no framework, no build step)

## Conventions

- Each app is independently runnable: `cd app1-recipes && uvicorn main:app`
- Shared code lives in `shared/` and is imported as a local package
- All env config via .env files; see `infra/.env.example`
- OTel export target is configurable: Dynatrace OTLP endpoint by default, stdout for local dev
- No TypeScript, no React, no npm build steps. Frontends are static HTML served by FastAPI

## Key environment variables

- `VLLM_BASE_URL`: OpenAI-compatible endpoint for the inference service
- `VLLM_MODEL`: Model name (e.g. `ibm-granite/granite-3.1-8b-instruct`)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: Dynatrace or local collector
- `OTEL_EXPORTER_OTLP_HEADERS`: Dynatrace API token header
- `OTEL_SERVICE_NAME`: Set per app (recipe-generator, gardening-advisor, chatbot)
- `DATABASE_URL`: PostgreSQL connection string (App 3 only)

## Testing

- `pytest` per app directory
- `docker compose up` from `infra/` to run everything locally (apps + PostgreSQL + OTel collector)
- Use `OTEL_EXPORTER=console` for local span debugging

## Important constraints

- Apps must work for 30 concurrent users against a single vLLM instance
- Frontends must be dead simple: a single HTML file per app, no build tooling
- All OTel instrumentation must be automatic where possible (FastAPI, httpx, psycopg2 auto-instrumentation), with manual spans only for the LLM call via openllmetry
- Do not add authentication to App 1 or App 2. Only App 3 has auth.
- PostgreSQL schema must be pre-seedable: `infra/init.sql` creates tables and 30 user accounts
