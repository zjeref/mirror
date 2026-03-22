# Mirror Improvement Plan

## Priority 1: SAFETY (blocks production deployment)

### S1. Crisis detection bypass [CRITICAL]
**Problem**: Keyword-only detection misses "kms", "d1e", "ending things", "don't want to be here", euphemisms, typos.
**Fix**: Use LLM `risk` field from state assessment — if `risk: "high"` or `risk: "crisis"`, trigger crisis flow. Add euphemisms to keyword list. Defense in depth.

### S2. No slow-escalation detection [CRITICAL]
**Problem**: User goes mood 7→5→3→2 over 5 messages. No alert. Risk field stored but never queried.
**Fix**: After saving LLM state, query last 5 states. If mood trending below 3 OR risk "moderate" for 3+ messages, trigger safety check-in.

### S3. Crisis flow exits after ONE reply [CRITICAL]
**Problem**: User says they want to keep talking, crisis flow ends, next message gets normal routing.
**Fix**: Keep crisis flow active for multiple exchanges. Only exit when user explicitly says they're feeling safer.

### S4. No crisis event logging [HIGH]
**Fix**: Log crisis events with timestamp, user_id, message content. Flag user record.

### S5. Fallback not crisis-safe [HIGH]
**Fix**: Add crisis keyword check inside `_fallback_response`.

### S6. No rate limiting [HIGH]
**Fix**: Max 1 message per 2 seconds in WebSocket handler.

### S7. Raw message content in InferredStateRecord [HIGH]
**Fix**: Remove `message_content` field or encrypt. Mood scores are sufficient.

---

## Priority 2: DATA INTEGRITY (things being lost/wrong)

### D1. Emotions array from LLM discarded [HIGH]
**Fix**: Add `emotions: list[str]` to `InferredStateRecord`, save in `_save_llm_state`.

### D4. Duplicate message in LLM context [HIGH]
**Fix**: Current message already in DB history — don't append again in LLM call.

### D2. Sustain talk miscalculated [HIGH]
**Fix**: Ask LLM for separate `change_talk` and `sustain_talk` scores.

### D3. `total_messages` count wrong in dashboard [MEDIUM]
**Fix**: Count actual Message records, not limited InferredStateRecord list.

---

## Priority 3: PROMPT ENGINEERING

### E1. `max_tokens: 700` too low — state JSON gets truncated [HIGH]
**Fix**: Increase to 1000.

### E2. Claude can leak internal tracking if asked [HIGH]
**Fix**: Add "NEVER discuss mirror_state or your assessment process."

### E3. Add "no jargon" rule [MEDIUM]
**Fix**: "NEVER use therapy terms (cognitive defusion, behavioral activation, OARS) in responses."

### E4. Add conversation length management [MEDIUM]
**Fix**: "After 20+ exchanges, gently suggest taking a break."

---

## Priority 4: UX

### U1. No post-flow guidance [HIGH]
**Fix**: After flow completion, offer: "Would you like a suggestion, or just chat?"

### U2. No typing indicator timeout [HIGH]
**Fix**: 30-second timeout → "Mirror is taking longer than usual..."

### U3. Text input active during flow widgets [MEDIUM]
**Fix**: Disable text input when slider/choice widget is showing.

### U4. Dashboard charts have no labels/tooltips [MEDIUM]
### U5. No empty state guidance on dashboard [MEDIUM]
### U6. No "New chat" confirmation [MEDIUM]

---

## Priority 5: PRODUCT (retention killers)

### G1. No proactive outreach / notifications [CRITICAL]
**The #1 retention killer.** App is entirely passive. No daily reminders, no re-engagement, no habit prompts.
**Fix**: Build notification system (email or push). Priority: re-engagement after 3-day silence.

### G2. No "good day" experience [HIGH]
**Fix**: When LLM detects mood ≥ 7, explore what's going well. Savoring, gratitude, "what made today good?"

### G3. No onboarding flow [HIGH]
**Fix**: First-time user gets guided tour of what Mirror can do.

### G4. No goal tracking beyond tiny habits [HIGH]
### G5. No guided session topics [MEDIUM]
### G6. No data export for therapists [MEDIUM]

---

## Priority 6: TECHNICAL

### T1. Flow state lost on server restart [HIGH]
**Fix**: Serialize flow state to DB. Restore on reconnect.

### T2. Dead WebSocket connections never cleaned [HIGH]
**Fix**: Ping/pong health checks, remove unresponsive connections.

### T3. Sync Anthropic client blocks event loop [HIGH]
**Fix**: Use `AsyncAnthropic` for direct API path.

### T4. Server timezone used instead of user timezone [MEDIUM]
### T5. No compound DB indexes [MEDIUM]

---

## Retention Research Key Findings

- Mental health apps: **3.9% retention at 30 days**
- Top 3 abandonment reasons: (1) "I feel better, don't need it" (2) Content repetitiveness (3) No felt relationship
- **#1 retention feature**: Relationship memory — the app remembers you and deepens understanding over time
- Proactive outreach = **2.4x better retention** vs passive-only
- No-guilt re-entry after lapse is critical
- "Good day" value proposition needed (not just a crisis tool)
- Apps that become relationships persist. Tools get put down.
