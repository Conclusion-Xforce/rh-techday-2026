# How to use these files

## Setup

1. Create your repo and place `CLAUDE.md` in the root:

```bash
mkdir workshop-otel-ai && cd workshop-otel-ai
git init
cp /path/to/CLAUDE.md .
```

2. Place the plan prompts somewhere accessible (they do not need to be in the repo; they are one-time inputs).

## Build order

Work through the plans in this order. Each builds on the previous.

### Step 1: Shared module + infrastructure
```
claude --mode plan < plan-shared-and-infra.md
```
Review the plan. When satisfied, switch to implementation and execute.
This gives you the OTel setup, the LLM client, Docker Compose, and the database schema that the apps depend on.

### Step 2: App 1 (Recipe Generator)
```
claude --mode plan < plan-app1-recipes.md
```
The simplest app. Get this working end-to-end first: frontend, backend, OTel spans visible in the console exporter. This validates that the shared module works.

### Step 3: App 2 (Gardening Advisor)
```
claude --mode plan < plan-app2-gardening.md
```
Adds the external API call. Verify that both the weather API spans and the LLM spans appear in the trace output.

### Step 4: App 3 (Chatbot)
```
claude --mode plan < plan-app3-chatbot.md
```
The most complex. Requires PostgreSQL running (use `docker compose up db`). Verify auth flow, conversation persistence, and that DB spans appear alongside LLM spans.

## After building

Once all apps work locally:
- Connect to Dynatrace by setting the OTLP endpoint and headers in `.env`
- Run all three apps simultaneously via `docker compose up`
- Generate some traffic across all apps
- Verify traces appear in Dynatrace with the expected span shapes

## Notes

- The plan prompts are designed for Claude Code plan mode. They describe what to build, not how to build it. Claude will propose the implementation.
- The CLAUDE.md stays in the repo permanently. It gives Claude context in every future session when you iterate, fix bugs, or add features.
- Each plan prompt is self-contained but references the shared module. That is why the shared module should be built first.
