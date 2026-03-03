"""
Main FastAPI application.

Endpoints:
    GET  /health                    - liveness probe
    GET  /estimate_tokens           - rough token count estimate
    POST /messages                  - record a ChatGPT message exchange (auth required)
    GET  /conversations/messages    - get messages for a conversation URL (auth required)
"""
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import get_current_user_info
from .database import Base, engine, get_db
from .energy_predictor import predict_energy
from .models import Conversation, Message, User
from .schemas import ConversationOut, MessageCreate, MessageOut

load_dotenv()

# Create all tables on startup (idempotent)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sustainability Framework API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"ok": True}


@app.get("/estimate_tokens")
def estimate_tokens(text: str = Query(default="")):
    """Lightweight whitespace-based token estimator (no model required)."""
    tokens = max(1, len(text.split()))
    return {"tokens": tokens, "model": "whitespace", "len": len(text)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_user(db: Session, user_info: dict) -> User:
    sub = user_info.get("sub", "")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
    user = db.query(User).filter(User.keycloak_sub == sub).first()
    if not user:
        user = User(
            keycloak_sub=sub,
            name=(
                user_info.get("name")
                or user_info.get("preferred_username")
                or "Unknown"
            ),
            email=user_info.get("email"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _get_or_create_conversation(db: Session, user: User, url: str) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id, Conversation.url == url)
        .first()
    )
    if not conv:
        conv = Conversation(url=url, user_id=user.id)
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv



# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------

@app.post("/messages", response_model=MessageOut)
def record_message(
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info),
):
    """
    Record a ChatGPT message exchange in the database.
    If no energy value is supplied, it is estimated from token counts.
    """
    user = _get_or_create_user(db, user_info)
    conv = _get_or_create_conversation(db, user, payload.conversation_url)

    # Use ML model to estimate energy (Joules). Only calculated once – stored in DB.
    energy = payload.energy
    if energy is None and payload.input_text:
        energy = predict_energy(
            payload.input_text,
            payload.input_tokens or max(1, len((payload.input_text or "").split())),
        )

    msg = Message(
        conversation_id=conv.id,
        input_text=payload.input_text,
        output_text=payload.output_text,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        energy=energy,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@app.get("/conversations/messages", response_model=list[MessageOut])
def get_conversation_messages(
    url: str = Query(..., description="Conversation URL to look up"),
    db: Session = Depends(get_db),
    user_info: dict = Depends(get_current_user_info),
):
    """Return all recorded messages for the given conversation URL."""
    user = _get_or_create_user(db, user_info)
    conv = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id, Conversation.url == url)
        .first()
    )
    if not conv:
        return []
    return conv.messages
