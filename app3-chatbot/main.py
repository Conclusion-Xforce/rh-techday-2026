import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from shared.telemetry import init_telemetry
from shared.llm_client import complete
from sqlalchemy import text
from database import get_db, Conversation, SessionLocal
from auth import authenticate_user, create_session, validate_session, invalidate_session

tracer = init_telemetry()

app = FastAPI(title="AI Chatbot")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str


def get_current_user(authorization: str = Header(None), db: DBSession = Depends(get_db)) -> tuple[int, DBSession]:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.removeprefix("Bearer ").strip()
    user_id = validate_session(db, token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return user_id, db


@app.get("/")
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/health")
async def health():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "disconnected"}


@app.post("/api/login")
async def login(req: LoginRequest, db: DBSession = Depends(get_db)):
    user = authenticate_user(db, req.username, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_session(db, user.id)
    return {"token": token, "display_name": user.display_name}


@app.post("/api/logout")
async def logout(authorization: str = Header(None), db: DBSession = Depends(get_db)):
    if authorization:
        token = authorization.removeprefix("Bearer ").strip()
        invalidate_session(db, token)
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(req: ChatRequest, auth: tuple = Depends(get_current_user)):
    user_id, db = auth

    # Load conversation history
    with tracer.start_as_current_span("load-history"):
        history_rows = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at)
            .all()
        )

    # Assemble prompt
    with tracer.start_as_current_span("assemble-prompt") as span:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant. Be concise and informative. "
                    "You have access to the conversation history below."
                ),
            }
        ]
        for row in history_rows:
            messages.append({"role": row.role, "content": row.content})
        messages.append({"role": "user", "content": req.message})

        span.set_attribute("conversation.length", len(history_rows))
        span.set_attribute("prompt.total_messages", len(messages))

    # Call LLM
    result = await complete(messages)

    # Store the exchange
    with tracer.start_as_current_span("store-exchange"):
        user_msg = Conversation(
            user_id=user_id,
            role="user",
            content=req.message,
            token_count=result["input_tokens"],
        )
        assistant_msg = Conversation(
            user_id=user_id,
            role="assistant",
            content=result["content"],
            token_count=result["output_tokens"],
        )
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()

    return {
        "response": result["content"],
        "model": result["model"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "conversation_length": len(history_rows) + 2,
    }


@app.get("/api/history")
async def history(auth: tuple = Depends(get_current_user)):
    user_id, db = auth
    rows = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.created_at)
        .all()
    )
    return {
        "messages": [
            {"role": r.role, "content": r.content, "token_count": r.token_count}
            for r in rows
        ]
    }


@app.post("/api/clear")
async def clear(auth: tuple = Depends(get_current_user)):
    user_id, db = auth
    db.query(Conversation).filter(Conversation.user_id == user_id).delete()
    db.commit()
    return {"status": "ok"}
