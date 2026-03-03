"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------- Message ----------

class MessageCreate(BaseModel):
    """Payload sent by the extension when a new ChatGPT message completes."""
    conversation_url: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    # Estimated energy in Wh; computed client-side or by the API
    energy: Optional[float] = None


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    energy: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Conversation ----------

class ConversationOut(BaseModel):
    id: int
    url: str
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}
