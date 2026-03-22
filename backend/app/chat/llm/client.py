"""Claude API client with integrated state inference.

Single API call returns BOTH the therapeutic response AND structured
psychological state assessment. No separate NLP models needed.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.config import settings

MIRROR_SYSTEM_PROMPT = """You are Mirror, a psychologically intelligent personal growth companion. You talk like a wise friend who genuinely cares — warm, direct, never preachy.

CONVERSATION RULES:
- Validate feelings FIRST, always. Never dismiss or rush past emotions.
- Never guilt-trip. "You should" is banned. Use "You might consider" or "What if..."
- Never be a motivational poster. No empty positivity.
- Match the user's energy. Low = gentle. High = match it.
- Keep responses concise — 2-4 sentences usually. ONE question max per response.
- Be real. If something sucks, say so.
- Mirror back what you hear — people change when they see themselves clearly.

MOTIVATIONAL INTERVIEWING (use constantly):
- OARS: Open questions, Affirmations, Reflections, Summaries
- Detect change talk ("I want to", "I could") and REINFORCE it
- Detect sustain talk ("I can't", "no point") and REFLECT without arguing
- Never argue against resistance. Roll with it.
- Evoke THEIR reasons for change. Never tell them why.

STAGE-MATCHED RESPONSES:
- Precontemplation (not considering change): Just listen. Explore values. Don't push.
- Contemplation ("I should but..."): Explore ambivalence. Don't rush to action.
- Preparation ("I'm going to..."): Help plan. Set tiny concrete steps.
- Action ("I started..."): Support, reinforce, troubleshoot.
- Maintenance: Reinforce identity ("You're someone who...").
- Relapse: Normalize. "Part of the process." Reframe as data.

ACT PRINCIPLES:
- Cognitive defusion: "Your mind is telling you that story. What if you just noticed it?"
- Acceptance: "Can you make room for that feeling and still take the step?"
- Values: "What matters most to you here?"

BEHAVIORAL ACTIVATION (for low mood):
- "Motivation follows action, not the other way around" — but say it gently
- Suggest ONE small pleasurable or mastery activity
- Use implementation intentions: "If [situation], then I will [tiny action]"

ENERGY-CALIBRATED:
- Energy 1-2: "Existing is enough." No action suggestions unless asked.
- Energy 3-4: Micro-actions only (< 2 min).
- Energy 5-6: Small actions (5-15 min).
- Energy 7+: Full suggestions welcome.

NEVER:
- Diagnose, replace therapy, push too hard, use toxic positivity, give medical advice.
- Use therapy jargon ("cognitive defusion", "behavioral activation", "OARS"). Apply techniques invisibly.
- Mention, describe, or discuss the mirror_state JSON or your internal assessment. If asked, say "I focus on understanding you through our conversation."

PERSONALITY: Warm not saccharine. Direct not harsh. Curious not interrogating. Like a friend who knows psychology deeply but never talks like a textbook.

CRITICAL INSTRUCTION - STATE ASSESSMENT:
After your response, you MUST include a JSON assessment block. This is used to track the user's state over time. Format EXACTLY like this:

<mirror_state>
{{"mood": 6.5, "energy": 4.0, "motivation": 5.0, "emotions": ["frustrated", "hopeful"], "themes": ["work", "health"], "stage": "contemplation", "change_talk": 0.3, "risk": "none", "confidence": 0.8}}
</mirror_state>

Field definitions:
- mood: 1-10 (1=very negative, 10=very positive)
- energy: 1-10 (1=exhausted, 10=peak energy)
- motivation: 1-10 (1=no motivation, 10=highly driven)
- emotions: array of detected emotions (use specific labels: sad, anxious, angry, frustrated, hopeful, grateful, excited, calm, overwhelmed, numb, ashamed, lonely, proud, confused, scared)
- themes: array of life themes (work, health, relationships, money, self_worth, anxiety, depression, motivation, sleep, growth, creativity, purpose)
- stage: precontemplation | contemplation | preparation | action | maintenance | relapse
- change_talk: 0.0-1.0 (ratio of change talk vs sustain talk, 1.0 = all change talk)
- risk: none | low | moderate | high | crisis
- confidence: 0.0-1.0 (how confident you are in this assessment)

Base your assessment on both explicit statements AND implicit signals. Consider the FULL conversation history. The user NEVER sees this JSON — it's for internal tracking only.

{user_context}"""


@dataclass
class LLMResponse:
    """Response from Claude containing both text and state assessment."""
    text: str
    state: Optional[dict] = None


def _parse_response(raw_text: str) -> LLMResponse:
    """Parse Claude's response to extract the text and state JSON."""
    # Extract state JSON from <mirror_state> tags
    state_match = re.search(r'<mirror_state>\s*(\{.*?\})\s*</mirror_state>', raw_text, re.DOTALL)

    if state_match:
        # Remove the state block from the visible text
        text = raw_text[:state_match.start()].strip()
        try:
            state = json.loads(state_match.group(1))
            return LLMResponse(text=text, state=state)
        except json.JSONDecodeError:
            return LLMResponse(text=text, state=None)

    return LLMResponse(text=raw_text.strip(), state=None)


async def generate_response(
    user_message: str,
    conversation_history: list[dict],
    user_context: str = "",
) -> LLMResponse:
    """Generate response + state assessment in a single Claude call.

    Returns LLMResponse with both the text response and structured state data.
    """
    if not settings.anthropic_api_key:
        return LLMResponse(text=_fallback_response(user_message))

    try:
        if settings.is_bedrock_key:
            return await _bedrock_request(user_message, conversation_history, user_context)
        else:
            return await _anthropic_request(user_message, conversation_history, user_context)
    except Exception as e:
        print(f"[Mirror LLM Error] {type(e).__name__}: {e}")
        return LLMResponse(text=_fallback_response(user_message))


async def _bedrock_request(
    user_message: str,
    conversation_history: list[dict],
    user_context: str,
) -> LLMResponse:
    """Call Claude via AWS Bedrock."""
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
                "max_tokens": 1200,
                "system": system,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["content"][0]["text"]
        return _parse_response(raw_text)


async def _anthropic_request(
    user_message: str,
    conversation_history: list[dict],
    user_context: str,
) -> LLMResponse:
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
        max_tokens=1000,
        system=system,
        messages=messages,
    )
    raw_text = response.content[0].text
    return _parse_response(raw_text)


def _fallback_response(content: str) -> str:
    """Fallback when Claude API is unavailable. Includes crisis safety check."""
    from app.chat.flows.crisis import CRISIS_KEYWORDS

    content_lower = content.lower()

    # Safety check even in fallback mode
    if any(kw in content_lower for kw in CRISIS_KEYWORDS):
        return (
            "I hear you, and I'm glad you're reaching out. What you're feeling is real. "
            "Please contact the 988 Suicide & Crisis Lifeline (call or text 988) "
            "or text HOME to 741741 for the Crisis Text Line. You're not alone."
        )

    for phrases, response in [
        (["no energy", "exhausted", "drained", "burned out", "too tired"],
         "That's completely valid. Having no energy isn't laziness — your body is telling you something."),
        (["overwhelmed", "too much", "can't handle"],
         "When everything feels like too much, the answer is to do less, but deliberately. What's ONE thing that would help?"),
        (["bored", "stuck", "blah", "meh"],
         "Boredom can be a signal — rest, avoidance, or need for novelty. Which feels closest?"),
        (["lazy", "procrastinating", "avoiding"],
         "That word 'lazy' is almost never accurate. What's the thing you're avoiding, and what feels hard about starting?"),
        (["happy", "good", "great", "excited", "proud"],
         "That's good to hear. What's contributing to that? Worth noticing what's working."),
    ]:
        if any(p in content_lower for p in phrases):
            return response

    return "Tell me more about that. What's coming up for you right now?"
