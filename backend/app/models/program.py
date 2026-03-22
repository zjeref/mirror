"""Structured programs (QuitSure-inspired time-boxed journeys).

Each program is a multi-day structured experience with daily content.
Users progress through one day at a time.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ProgramEnrollment(Document):
    """Tracks a user's progress through a structured program."""
    user_id: Indexed(str)
    program_id: str  # e.g., "belief_reset_7d", "energy_sprint_14d"
    current_day: int = 0  # 0 = not started, 1 = day 1, etc.
    total_days: int = 7
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_active: bool = True

    # Daily completion tracking
    days_completed: list[int] = Field(default_factory=list)

    # Program-specific data collected during the journey
    collected_insights: list[dict] = Field(default_factory=list)
    # e.g., [{"day": 1, "belief": "I'm lazy", "reframe": "I'm conserving energy"}, ...]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "program_enrollments"
        indexes = [
            [("user_id", 1), ("program_id", 1)],
        ]


# Program definitions (static content, not in DB)
PROGRAMS = {
    "belief_reset_7d": {
        "id": "belief_reset_7d",
        "name": "The Belief Reset",
        "description": "7 days to dismantle the beliefs keeping you stuck. No behavior change required — just observe and understand.",
        "total_days": 7,
        "tagline": "You don't need willpower. You need clarity.",
        "days": {
            1: {
                "title": "The Map of Your Beliefs",
                "theme": "awareness",
                "prompt": (
                    "Today is about seeing clearly — no judgment, no fixing.\n\n"
                    "Think about something you've been wanting to change but haven't. "
                    "What story do you tell yourself about why you haven't changed it yet?\n\n"
                    "Don't filter. Just say what comes up."
                ),
                "technique": "belief_identification",
            },
            2: {
                "title": "Where Did That Belief Come From?",
                "theme": "origin",
                "prompt": (
                    "Yesterday you shared a belief that's been keeping you stuck.\n\n"
                    "Let's trace it back. When did you first start believing this? "
                    "Was there a moment, a person, or an experience that planted it?\n\n"
                    "Beliefs feel like facts, but they're usually just old stories."
                ),
                "technique": "origin_tracing",
            },
            3: {
                "title": "The Cost of Keeping It",
                "theme": "discrepancy",
                "prompt": (
                    "Let's look at what this belief has cost you.\n\n"
                    "If you keep believing this for another year — same story, same pattern — "
                    "what does your life look like? Be specific.\n\n"
                    "And what would be different if you didn't carry this belief?"
                ),
                "technique": "develop_discrepancy",
            },
            4: {
                "title": "The Evidence Test",
                "theme": "testing",
                "prompt": (
                    "Beliefs that control us usually can't survive scrutiny.\n\n"
                    "Your belief — is it actually true? Can you think of even ONE time "
                    "it wasn't true? One moment where you DID show up, or WERE capable?\n\n"
                    "We're not replacing the belief yet. We're just checking if it holds up."
                ),
                "technique": "evidence_examination",
            },
            5: {
                "title": "Who Would You Be Without It?",
                "theme": "identity",
                "prompt": (
                    "Imagine waking up tomorrow and this belief is just... gone. "
                    "Not replaced with toxic positivity — just absent.\n\n"
                    "What would you do differently? How would you carry yourself? "
                    "What would you try?\n\n"
                    "Describe that person."
                ),
                "technique": "identity_exploration",
            },
            6: {
                "title": "The New Story",
                "theme": "reconstruction",
                "prompt": (
                    "You've spent five days examining an old belief. "
                    "You've seen where it came from, what it costs, and that it doesn't "
                    "hold up to evidence.\n\n"
                    "Now — what's a more honest story? Not the opposite extreme, "
                    "not 'I'm amazing.' Something real that you actually believe.\n\n"
                    "Start with: 'The truth is...'"
                ),
                "technique": "belief_reconstruction",
            },
            7: {
                "title": "One Step From the New Story",
                "theme": "committed_action",
                "prompt": (
                    "Day 7. You have a new, truer story about yourself.\n\n"
                    "What is ONE thing — just one — that the person with this new belief "
                    "would do today? Not a big goal. A single action that proves "
                    "the new story is real.\n\n"
                    "When will you do it? Let's make it specific."
                ),
                "technique": "implementation_intention",
            },
        },
    },
}
