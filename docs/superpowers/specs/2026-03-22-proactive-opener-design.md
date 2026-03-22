# Proactive Conversation Opener — Design Spec

**Date:** 2026-03-22
**Status:** Draft
**Author:** Davion + Claude

## Overview

Mirror always speaks first. Instead of waiting for the user to initiate, `SessionEngine.handle_session_start()` always returns a greeting — contextual, data-driven, and severity-adaptive. New users get structured onboarding with guided screening. Returning users get an opener based on what Mirror has observed.

## Goals

1. Mirror never sits silent waiting for the user to start
2. New users are guided through onboarding + screening (people often can't self-report without guided questions)
3. Returning users get openers that reflect what Mirror has noticed
4. Directness scales with severity — urgent patterns get direct language, lighter observations get gentle invitations

## Non-Goals

- Changing the existing priority 1-3 greetings (homework, session, screening due)
- Adding new data models
- Changing the LLM system prompt
- Push notification changes

---

## 1. Updated Priority Chain

`SessionEngine.handle_session_start()` returns the first match:

| Priority | Condition | Opener Type |
|----------|-----------|-------------|
| 1 | Pending homework review | "How did [homework] go?" (existing) |
| 2 | Next protocol session ready | "Ready for session N?" (existing) |
| 3 | Screening due (PendingAction) | Start screening flow (existing) |
| 4 | Pattern-based alert detected | Direct or gentle based on severity |
| 5 | Returning user with history | Context-based greeting |
| 6 | First-time user (no conversations) | Onboarding + guided screening |
| 7 | Fallback (should never reach) | "Hey [name]. What's on your mind?" |

**Key change:** The method never returns `None`. Priority 7 is the absolute fallback.

---

## 2. Priority 4: Pattern-Based Alerts

Analyze recent `InferredStateRecord` data (last 7 days) to detect patterns worth mentioning — softer thresholds than screening triggers, meant for conversation openers not clinical screening.

### Alert Conditions (checked in order, first match wins)

| Pattern | Threshold | Tone | Example Opener |
|---------|-----------|------|---------------|
| Mood dropping | 3+ days with mood_valence ≤ 4 (flat threshold — any 3 days below 4, not necessarily trending) | Direct if ≤ 3, gentle if 3-4 | "I've noticed things have felt heavier the last few days. Want to talk about what's going on?" |
| Energy low | 3+ days with energy_level ≤ 3 | Direct if ≤ 2, gentle if 2-3 | "Your energy has been really low lately. That's worth paying attention to." |
| Anxiety emerging | 2+ days with "anxiety" in themes | Gentle | "I've been noticing some worry patterns in what you've shared. Want to explore that?" |
| Positive trend | 3+ days with mood improving (each day higher than previous) | Warm | "Things seem to be shifting in a good direction. I'd love to hear how it's going." |

**Severity-adaptive language:**
- mood_valence ≤ 3 or energy ≤ 2 → Direct: "I've noticed..." / "I want to check in on..."
- mood_valence 3-4 or energy 2-3 → Gentle: "I've been thinking about..." / "Want to explore..."
- Positive trends → Warm: "Things seem to be..." / "I noticed something good..."

### Implementation

New function in `sessions/engine.py`:

```python
async def _detect_pattern_alert(self) -> Optional[dict]:
    """Detect soft patterns for conversation openers. Returns alert dict or None."""
```

Queries `InferredStateRecord` for last 7 days (confidence >= 0.3), groups by day, checks conditions. Returns `{"type": "mood_dropping"|"energy_low"|"anxiety_emerging"|"positive_trend", "severity": "direct"|"gentle"|"warm", "data": {...}}` or `None`.

Does NOT create PendingActions — these are conversation-only signals.

---

## 3. Priority 5: Contextual Returning User Opener

When no patterns are flagged, Mirror still speaks first based on how long it's been and what it knows.

### Recency-Based Greeting

| Days Since Last Message | Opener |
|------------------------|--------|
| 0 (same day) | "Hey again. What's on your mind?" |
| 1-2 | "Hey [name]. How's today going?" |
| 3-6 | "Good to see you, [name]. It's been a few days — how are things?" |
| 7+ | "Hey [name]. It's been a while. No pressure — I'm glad you're here. How are you doing?" |

### Value/Goal Reference (occasional)

If the user has completed a ValuesFlow and has stored values, Mirror occasionally references a value in the greeting (deterministic per day — `hash(user_id + date_str) % 10 < 3` — so it's stable across reconnects):

- "Last time you mentioned [value area] matters to you. How's that going?"
- "You've been working on [habit name]. How's that feeling?"

### Implementation

New function in `sessions/engine.py`:

```python
async def _build_contextual_greeting(self, context: UserContext) -> dict:
    """Build a greeting based on recency and user data."""
```

Queries last `Message` for the user to determine recency. Queries `UserValues` and active `Habit` for personalization.

---

## 4. Priority 6: First-Time Onboarding

New users (no existing conversations) get a structured onboarding experience.

### Flow

1. **Welcome message** sent immediately:
   > "Hey [name]. Welcome to Mirror. I'm here to help you understand yourself better — not to fix you, just to walk alongside you."
   >
   > "I work best when I understand where you are. Mind if I ask you a few questions? It'll take about 5 minutes."

2. **Wait for user acknowledgment** — the user's first reply (anything) is treated as consent to proceed. The welcome message is NOT a screening question, so any reply moves to step 3.

3. **Start PHQ-9 screening** via existing `ScreeningFlow`. The onboarding IS the screening — no separate onboarding flow needed.

4. **If PHQ-9 flags moderate+**, follow up with GAD-7 (queue as PendingAction for next session_start).

5. **Screening completion** flows through existing `_on_screening_complete()` → `SeverityRouter` → offer protocol or close warmly.

### Implementation

The existing welcome message in `chat/router.py` is removed. SessionEngine handles all first-contact logic:

```python
async def _build_onboarding_greeting(self, context: UserContext) -> dict:
    """Welcome new users and start guided screening."""
```

Checks `Conversation.find_one(user_id=self.user_id)` — if None, user is new. Returns welcome message and starts PHQ-9 ScreeningFlow.

---

## 5. Files Modified

| File | Change |
|------|--------|
| `backend/app/sessions/engine.py` | Expand `handle_session_start()` with priorities 4-6-7, add `_detect_pattern_alert()`, `_build_contextual_greeting()`, `_build_onboarding_greeting()` |
| `backend/app/chat/router.py` | Remove the existing new-user welcome message block (SessionEngine handles it) |
| `backend/tests/test_sessions/test_engine.py` | Add tests for new opener behaviors |

No new models, no new files, no new dependencies.

---

## 6. Message Templates

### Pattern Alerts (Priority 4)

**Mood dropping (direct):**
- "I've noticed your mood has been lower the last few days. That's something I want to check in on. How are you feeling right now?"
- "Things seem to have been weighing on you lately. Want to talk about what's going on?"

**Mood dropping (gentle):**
- "I've been noticing some shifts in how you've been feeling. Want to explore that together?"

**Energy low (direct):**
- "Your energy has been really low lately. That's worth paying attention to. What's going on?"

**Energy low (gentle):**
- "I noticed your energy has been on the lower side. How are you holding up?"

**Anxiety emerging (gentle):**
- "I've been picking up on some worry patterns in our recent conversations. Want to dig into that?"

**Positive trend (warm):**
- "Things seem to be moving in a good direction. I'd love to hear what's been different."
- "I noticed your mood has been improving. What do you think is behind that?"

### Contextual Greetings (Priority 5)

- Same day: "Hey again. What's on your mind?"
- 1-2 days: "Hey [name]. How's today going?"
- 3-6 days: "Good to see you, [name]. It's been a few days — how are things?"
- 7+ days: "Hey [name]. It's been a while. No pressure — I'm glad you're here. How are you doing?"
- With value reference: "Hey [name]. You mentioned [area] matters to you — how's that going?"

### Onboarding (Priority 6)

- "Hey [name]. Welcome to Mirror. I'm here to help you understand yourself better — not to fix you, just to walk alongside you.\n\nI work best when I understand where you are. Mind if I ask you a few questions? It'll take about 5 minutes."
