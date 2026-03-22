"""Claude API client - supports direct Anthropic API and AWS Bedrock long-term API keys."""

import json
from typing import Optional

import httpx

from app.config import settings

MIRROR_SYSTEM_PROMPT = """You are Mirror, a psychologically intelligent personal growth companion. You talk like a wise friend who genuinely cares — warm, direct, never preachy.

CORE RULES:
- Validate feelings FIRST, always. Never dismiss, minimize, or rush past emotions.
- Never guilt-trip. Words like "you should", "you need to", "you must" are banned.
- Never be a motivational poster. No "just believe in yourself!" or "you got this!" unless earned.
- Match the user's energy. If they're low, be gentle. If they're fired up, match it.
- Keep responses concise — 2-4 sentences for casual chat, longer only when doing exercises.
- Ask ONE question at a time, max. Don't overwhelm.
- Be real. If something sucks, acknowledge it sucks.

WHAT YOU CAN DO:
- Listen and reflect back what you hear
- Spot cognitive distortions gently (all-or-nothing thinking, catastrophizing, etc.)
- Suggest minimum viable actions scaled to energy level
- Help design tiny habits (BJ Fogg: anchor + tiny behavior + celebration)
- Guide CBT thought reframing exercises
- Detect patterns and share insights

WHAT YOU NEVER DO:
- Diagnose mental health conditions
- Replace therapy or medication
- Push harder than the user can handle
- Use toxic positivity
- Give medical advice

ENERGY AWARENESS:
- If user seems low energy (1-3): Only suggest micro-actions (< 2 min). "Just breathe" is valid.
- If user seems mid energy (4-6): Small suggestions are okay (5-15 min).
- If user seems high energy (7+): You can suggest ambitious things.
- When in doubt, go smaller, not bigger.

PERSONALITY:
- Warm but not saccharine
- Direct but not harsh
- Curious, not interrogating
- Honest, not brutal
- Like talking to a friend who happens to know psychology

{user_context}"""


async def generate_response(
    user_message: str,
    conversation_history: list[dict],
    user_context: str = "",
) -> str:
    """Generate a response using Claude (direct API or Bedrock).

    Falls back to simple responses if API is not configured or fails.
    """
    if not settings.anthropic_api_key:
        return _fallback_response(user_message)

    try:
        if settings.is_bedrock_key:
            return await _bedrock_request(user_message, conversation_history, user_context)
        else:
            return await _anthropic_request(user_message, conversation_history, user_context)
    except Exception as e:
        print(f"[Mirror LLM Error] {type(e).__name__}: {e}")
        return _fallback_response(user_message)


async def _bedrock_request(
    user_message: str,
    conversation_history: list[dict],
    user_context: str,
) -> str:
    """Call Claude via AWS Bedrock long-term API key (Bearer token auth)."""
    region = settings.aws_region
    model = settings.bedrock_model
    url = f"https://bedrock-runtime.{region}.amazonaws.com/model/{model}/invoke"

    system = MIRROR_SYSTEM_PROMPT.format(user_context=user_context)

    messages = []
    for msg in conversation_history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.anthropic_api_key}",
            },
            json={
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "system": system,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def _anthropic_request(
    user_message: str,
    conversation_history: list[dict],
    user_context: str,
) -> str:
    """Call Claude via direct Anthropic API."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    system = MIRROR_SYSTEM_PROMPT.format(user_context=user_context)

    messages = []
    for msg in conversation_history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def _fallback_response(content: str) -> str:
    """Simple fallback when Claude API is unavailable."""
    content_lower = content.lower()

    low_energy = ["no energy", "exhausted", "can't do anything", "too tired", "burned out", "drained"]
    if any(p in content_lower for p in low_energy):
        return ("That's completely valid. Having no energy isn't laziness — "
                "your body is telling you something. Right now, the only thing "
                "that matters is being gentle with yourself.")

    overwhelm = ["overwhelmed", "too much", "can't handle", "don't know where to start"]
    if any(p in content_lower for p in overwhelm):
        return ("When everything feels like too much, the answer isn't to do more — "
                "it's to do less, but deliberately. What's the ONE thing that, if you "
                "did it today, would make you feel even slightly better?")

    bored = ["bored", "nothing to do", "stuck", "blah", "meh"]
    if any(p in content_lower for p in bored):
        return ("Boredom can actually be a signal — sometimes it means you need rest, "
                "sometimes you're avoiding something, sometimes you need novelty. "
                "Which feels closest?")

    lazy = ["lazy", "procrastinating", "avoiding", "putting off"]
    if any(p in content_lower for p in lazy):
        return ("Calling yourself lazy is almost never accurate. Usually it's low energy, "
                "unclear next steps, or something emotional underneath. "
                "What's the thing you're avoiding, and what feels hard about starting it?")

    return "Tell me more about that. What's coming up for you right now?"
