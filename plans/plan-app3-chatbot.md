# Plan: App 3 - Chatbot with Authentication and Persistence

Plan the implementation of `app3-chatbot/`, the most architecturally complex of three workshop demo apps. This app demonstrates the full production pattern: authentication, database persistence, and growing conversation context.

## What this app does

A conversational chatbot where participants log in with pre-provisioned credentials, chat with the model, and have their conversation history persisted in PostgreSQL. When they refresh or return, their history is loaded. Each turn includes the full conversation history in the prompt, causing input token counts to grow visibly over time. This is the key observability insight: participants can watch their token consumption increase in the Dynatrace dashboard as they chat more.

## Why this app matters for the demo

This is the app that proves AI observability is not a separate discipline. The Dynatrace trace includes auth checks, database reads, database writes, AND model inference, all in one distributed trace. The same tool that shows you DB query latency also shows you token consumption. That is the "single pane of glass" story.

## Desired trace shape

```
[FastAPI request span]
  ├── [DB read: authenticate user / validate session]
  ├── [DB read: load conversation history]
  ├── [prompt assembly (manual span)]
  ├── [LLM inference span via openllmetry]
  └── [DB write: store new exchange]
```

6 spans, 2 services (app + database), 1 external dependency (inference).

## Requirements

### Backend (Python/FastAPI)

#### Authentication
- POST `/api/login` accepts `{ "username": "participant01", "password": "techday2026" }`
- Validates against the users table in PostgreSQL
- Returns a session token (simple UUID-based session, stored in the sessions table)
- All other endpoints require the session token in the Authorization header
- POST `/api/logout` invalidates the session
- No OAuth, no JWT complexity. Simple session tokens. This is a demo, not a production auth system.

#### Chat
- POST `/api/chat` accepts `{ "message": "What is OpenTelemetry?" }` (requires auth)
- Step 1: Validate session token (DB read)
- Step 2: Load conversation history for this user from the conversations table (DB read)
- Step 3: Construct prompt with system message + full conversation history + new user message
- Step 4: Call vLLM via the openai SDK
- Step 5: Store the new user message and assistant response in the conversations table (DB write)
- Step 6: Return the assistant response + updated token count metadata
- GET `/api/history` returns the conversation history for the logged-in user (requires auth)
- POST `/api/clear` clears conversation history for the logged-in user (requires auth)

#### Health
- GET `/api/health` for readiness checks (includes DB connectivity check)

### Database (PostgreSQL)

#### Schema
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100)
);

CREATE TABLE sessions (
    token UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '4 hours'
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    token_count INTEGER,        -- track tokens per message for dashboard
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id, created_at);
CREATE INDEX idx_sessions_token ON sessions(token);
```

#### Seed data
- `infra/init.sql` must create 30 participant accounts: participant01 through participant30, all with the same password (bcrypt hashed)
- Display names: "Participant 1" through "Participant 30"

### Frontend (static HTML)
- Single `index.html` served by FastAPI at `/`
- Login screen: username and password fields, login button
- Chat interface (shown after login):
  - Message history display (scrollable, auto-scroll to bottom)
  - Input field + send button
  - Token counter displayed in the UI: shows cumulative input tokens used in this conversation (this is the key metric participants will watch grow)
  - "Clear history" button
  - Logout button
- Loading state on each message while waiting for the model
- Clean, minimal UI. No framework. Vanilla HTML/CSS/JS.
- Session token stored in sessionStorage (not localStorage, not cookies)

### Observability
- FastAPI auto-instrumentation via `opentelemetry-instrumentation-fastapi`
- psycopg2 auto-instrumentation via `opentelemetry-instrumentation-psycopg2` (captures all DB queries as spans)
- LLM call instrumented via openllmetry: model name, token counts (input + output), latency
- Manual span around prompt assembly: `assemble-prompt`. Add attributes: `conversation.length` (number of turns), `prompt.total_tokens` (estimated input size)
- Manual span attributes on the chat endpoint span: `user.id`, `conversation.turn_number`
- OTLP export to Dynatrace
- Service name: `chatbot`

### Project structure
```
app3-chatbot/
  main.py              # FastAPI app, routes, OTel setup
  auth.py              # Authentication logic (login, session validation)
  database.py          # SQLAlchemy models and DB session management
  static/
    index.html          # Frontend
  requirements.txt
  README.md
```

## Shared dependencies
- Import OTel initialization from `shared/telemetry.py`
- Import the model client wrapper from `shared/llm_client.py`

## Infrastructure dependency
- Requires PostgreSQL. For local dev: `docker compose up db` from `infra/`
- Connection string from `DATABASE_URL` env var

## What NOT to build
- No OAuth, no JWT, no external identity provider. Simple username/password + session token.
- No streaming responses
- No rate limiting
- No password change or user management endpoints
- No WebSocket for real-time updates. Simple request/response.
- No conversation branching or editing. Linear history only.
