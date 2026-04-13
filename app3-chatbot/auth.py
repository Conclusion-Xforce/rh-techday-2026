import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.orm import Session as DBSession

from database import User, Session


def authenticate_user(db: DBSession, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return None
    return user


def create_session(db: DBSession, user_id: int) -> str:
    token = str(uuid.uuid4())
    session = Session(
        token=token,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db.add(session)
    db.commit()
    return token


def validate_session(db: DBSession, token: str) -> int | None:
    """Returns user_id if the session is valid, else None."""
    session = db.query(Session).filter(Session.token == token).first()
    if session is None:
        return None
    if session.expires_at and session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None
    return session.user_id


def invalidate_session(db: DBSession, token: str) -> None:
    db.query(Session).filter(Session.token == token).delete()
    db.commit()
