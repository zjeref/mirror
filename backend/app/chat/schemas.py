from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ChatMessageIn(BaseModel):
    type: str  # "message" | "flow_response" | "ping"
    content: Optional[str] = None
    conversation_id: Optional[str] = None
    flow_id: Optional[str] = None
    step: Optional[str] = None
    value: Optional[Any] = None


class ChatMessageOut(BaseModel):
    type: str  # "message" | "flow_prompt" | "stream_start" | "stream_chunk" | "stream_end" | "pong" | "error"
    content: Optional[str] = None
    sender: Optional[str] = None
    timestamp: Optional[str] = None
    message_id: Optional[str] = None
    metadata: Optional[dict] = None
    # Flow-specific fields
    flow_id: Optional[str] = None
    step: Optional[str] = None
    prompt: Optional[str] = None
    input_type: Optional[str] = None  # "text" | "slider" | "choice" | "mood_picker"
    options: Optional[list[str]] = None
    min_val: Optional[int] = None
    max_val: Optional[int] = None


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    conversation_type: str
    is_active: bool
    created_at: datetime
    message_count: int


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    message_type: str
    created_at: datetime
    metadata: Optional[dict] = None
