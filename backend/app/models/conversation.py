from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field


class Conversation(Document):
    user_id: Indexed(str)
    title: Optional[str] = None
    conversation_type: str = "freeform"  # freeform | check_in | exercise | journal
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "conversations"


class Message(Document):
    conversation_id: Indexed(str)
    role: str  # user | assistant | system
    content: str
    message_type: str = "text"  # text | flow_prompt | flow_response
    metadata_: Optional[dict] = Field(default=None, alias="metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "messages"
