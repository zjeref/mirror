"""Journal REST endpoints for daily diary entries."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.models.journal import JournalEntry
from app.models.user import User

router = APIRouter(prefix="/journal", tags=["journal"])


class JournalCreate(BaseModel):
    date: str  # "2026-03-22"
    content: str = ""
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    energy_score: Optional[int] = Field(None, ge=1, le=10)
    tags: list[str] = Field(default_factory=list)
    wins: list[str] = Field(default_factory=list)
    word_count: int = 0


@router.post("/")
async def create_or_update_entry(
    data: JournalCreate, user: User = Depends(get_current_user)
):
    """Create or update a journal entry for a specific date."""
    existing = await JournalEntry.find_one(
        JournalEntry.user_id == str(user.id),
        JournalEntry.date == data.date,
    )

    if existing:
        existing.content = data.content
        existing.mood_score = data.mood_score
        existing.energy_score = data.energy_score
        existing.tags = data.tags
        existing.wins = data.wins
        existing.word_count = data.word_count
        existing.updated_at = datetime.now(timezone.utc)
        await existing.save()
        return existing
    else:
        entry = JournalEntry(
            user_id=str(user.id),
            date=data.date,
            content=data.content,
            mood_score=data.mood_score,
            energy_score=data.energy_score,
            tags=data.tags,
            wins=data.wins,
            word_count=data.word_count,
        )
        await entry.insert()
        return entry


@router.get("/")
async def list_entries(
    limit: int = 30, user: User = Depends(get_current_user)
):
    """List journal entries, most recent first."""
    entries = await JournalEntry.find(
        JournalEntry.user_id == str(user.id)
    ).sort("-date").limit(limit).to_list()
    return entries


@router.get("/{date}")
async def get_entry(date: str, user: User = Depends(get_current_user)):
    """Get a journal entry by date."""
    entry = await JournalEntry.find_one(
        JournalEntry.user_id == str(user.id),
        JournalEntry.date == date,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="No entry for this date")
    return entry


@router.delete("/{date}")
async def delete_entry(date: str, user: User = Depends(get_current_user)):
    """Delete a journal entry."""
    entry = await JournalEntry.find_one(
        JournalEntry.user_id == str(user.id),
        JournalEntry.date == date,
    )
    if not entry:
        raise HTTPException(status_code=404, detail="No entry for this date")
    await entry.delete()
    return {"status": "deleted"}


@router.post("/{date}/reflect")
async def generate_reflection(date: str, user: User = Depends(get_current_user)):
    """Generate an AI reflection for a journal entry."""
    entry = await JournalEntry.find_one(
        JournalEntry.user_id == str(user.id),
        JournalEntry.date == date,
    )
    if not entry or not entry.content:
        raise HTTPException(status_code=404, detail="No entry content to reflect on")

    from app.chat.llm.client import generate_response

    reflection_prompt = (
        f"The user wrote this journal entry for {date}:\n\n"
        f'"{entry.content}"\n\n'
        f"Mood: {entry.mood_score}/10, Energy: {entry.energy_score}/10\n"
        f"Tags: {', '.join(entry.tags) if entry.tags else 'none'}\n"
        f"Wins: {', '.join(entry.wins) if entry.wins else 'none'}\n\n"
        "Write a brief, warm reflection (2-3 sentences) that mirrors back "
        "what you notice — patterns, strengths, or something worth sitting with. "
        "Do NOT give advice unless asked. Just reflect."
    )

    response = await generate_response(
        user_message=reflection_prompt,
        conversation_history=[],
        user_context=f"User's name: {user.name}",
    )

    entry.ai_reflection = response.text
    entry.updated_at = datetime.now(timezone.utc)
    await entry.save()

    return {"reflection": response.text}
