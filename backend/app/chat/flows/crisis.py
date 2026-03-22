"""Crisis safety flow - highest priority, always activates first.

Defense in depth:
1. Keyword detection (instant, catches explicit language)
2. LLM risk assessment (catches implicit/euphemistic signals)
3. Slow escalation detection (mood trending down over messages)

This flow does NOT attempt therapy. It provides empathetic acknowledgment
and connects users to professional crisis resources.
"""

import logging
from typing import Any

from app.chat.flows.base import BaseFlow, FlowPrompt, FlowResult, UserContext
from app.chat.flows.registry import register_flow

logger = logging.getLogger("mirror.crisis")

# Expanded keyword list including euphemisms, typos, coded language
CRISIS_KEYWORDS = [
    # Direct
    "suicide", "kill myself", "end it all", "want to die", "self harm",
    "self-harm", "don't want to live", "no reason to live",
    "better off dead", "ending my life", "hurt myself",
    "not worth living", "take my life", "jump off", "overdose",
    "cut myself", "cutting myself",
    # Euphemisms and coded language
    "end things", "ending things", "don't want to be here",
    "can't do this anymore", "can't go on", "no way out",
    "rather not be alive", "wish i wasn't born", "wish i was dead",
    "disappear forever", "want to disappear", "make it stop",
    "no point in living", "tired of living", "done with life",
    "tired of existing", "can't take it anymore",
    # Common internet abbreviations
    "kms", "kys", "ctb",
    # Typo variants
    "k1ll", "su1cide", "d1e",
]

CRISIS_RESPONSE = (
    "I hear you, and I'm really glad you're talking about this. "
    "What you're feeling is real and valid.\n\n"
    "Please reach out to people who can help right now:\n\n"
    "**988 Suicide & Crisis Lifeline** — Call or text **988** (US)\n"
    "**Crisis Text Line** — Text **HOME** to **741741**\n"
    "**International Association for Suicide Prevention** — https://www.iasp.info/resources/Crisis_Centres/\n\n"
    "You don't have to go through this alone. "
    "I'm here to talk, but these professionals are trained to help in ways I can't.\n\n"
    "Would you like to keep talking? I'm listening."
)


def contains_crisis_keywords(text: str) -> bool:
    """Check if text contains crisis-related keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in CRISIS_KEYWORDS)


async def check_llm_risk(user_id: str) -> bool:
    """Check if recent LLM assessments flagged high risk."""
    from app.models.inferred_state import InferredStateRecord

    recent = await InferredStateRecord.find(
        InferredStateRecord.user_id == user_id,
    ).sort("-created_at").limit(1).to_list()

    if recent:
        risk = recent[0].stage_signals.get("risk", "none")
        if risk in ("high", "crisis"):
            return True
    return False


async def check_slow_escalation(user_id: str) -> bool:
    """Detect mood deteriorating over recent messages."""
    from app.models.inferred_state import InferredStateRecord

    recent = await InferredStateRecord.find(
        InferredStateRecord.user_id == user_id,
        InferredStateRecord.mood_valence != None,
    ).sort("-created_at").limit(5).to_list()

    if len(recent) < 3:
        return False

    moods = [s.mood_valence for s in recent if s.mood_valence is not None]
    if not moods:
        return False

    # Check if mood is consistently below 3 for last 3+ messages
    low_count = sum(1 for m in moods[:3] if m <= 3)
    if low_count >= 3:
        return True

    # Check for declining trend
    if len(moods) >= 3 and all(moods[i] >= moods[i + 1] for i in range(min(3, len(moods) - 1))):
        if moods[0] <= 3:
            return True

    return False


async def log_crisis_event(user_id: str, message: str, trigger: str):
    """Log crisis events for safety auditing."""
    logger.warning(f"CRISIS EVENT | user={user_id} | trigger={trigger} | message={message[:100]}")
    # In production: send admin notification, flag user record


@register_flow
class CrisisFlow(BaseFlow):
    flow_id = "crisis"
    display_name = "Crisis Support"

    def get_steps(self) -> list[str]:
        return ["respond", "follow_up", "check_safety", "closing"]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        await log_crisis_event(context.user_id, "", "keyword_or_risk")
        return FlowResult(
            next_step="follow_up",
            response_message=CRISIS_RESPONSE,
            prompt=FlowPrompt(prompt="", input_type="text"),
        )

    async def handle_input(
        self, step: str, value: Any, context: UserContext
    ) -> FlowResult:
        text = str(value).lower().strip()

        if step == "follow_up":
            # Check if they're still in crisis
            if contains_crisis_keywords(text):
                return FlowResult(
                    next_step="follow_up",
                    response_message=(
                        "I'm here with you. You don't have to face this alone. "
                        "Please consider reaching out to 988 right now — "
                        "they're available 24/7 and trained for exactly this.\n\n"
                        "Is there someone you trust who you could call or text right now?"
                    ),
                    prompt=FlowPrompt(prompt="", input_type="text"),
                )

            # Check for signs they're feeling safer
            safe_signals = ["better", "okay", "fine", "safe", "calm", "thank"]
            if any(s in text for s in safe_signals):
                return FlowResult(
                    next_step="check_safety",
                    response_message=(
                        "I'm glad to hear that. Before we move on, I want to check — "
                        "are you feeling safe right now?"
                    ),
                    prompt=FlowPrompt(
                        prompt="Are you feeling safe?",
                        input_type="choice",
                        options=["Yes, I'm feeling safer", "I'm not sure", "No, I'm still struggling"],
                    ),
                )

            # Continue listening
            return FlowResult(
                next_step="follow_up",
                response_message=(
                    "I'm here. Take all the time you need. "
                    "There's no pressure to say anything specific.\n\n"
                    "Remember: 988 is always available if you need to talk to someone trained in crisis support."
                ),
                prompt=FlowPrompt(prompt="", input_type="text"),
            )

        elif step == "check_safety":
            if "yes" in text or "safer" in text:
                return FlowResult(next_step=None)
            elif "not sure" in text or "no" in text or "struggling" in text:
                return FlowResult(
                    next_step="follow_up",
                    response_message=(
                        "That's okay. There's no rush. I'm here as long as you need.\n\n"
                        "If you're able to, please reach out to 988 — they can help more than I can. "
                        "What would feel most helpful right now?"
                    ),
                    prompt=FlowPrompt(prompt="", input_type="text"),
                )
            return FlowResult(
                next_step="follow_up",
                response_message="I'm still here. What do you need right now?",
                prompt=FlowPrompt(prompt="", input_type="text"),
            )

        return FlowResult(next_step=None)

    async def on_complete(self, context: UserContext) -> str:
        return (
            "I'm glad you're feeling safer. Remember: 988 is always there, 24/7. "
            "And I'm here whenever you want to talk. There's no wrong reason to come back."
        )
