# Proactive Psychology Engine

Mirror's proactive psychology engine transforms the platform from a reactive chatbot into a system that **leads the user** through structured clinical protocols. It screens for mental health issues using validated instruments, enrolls users in evidence-based treatment programs, assigns adaptive homework, and reaches out via push notifications — all gated by severity to ensure safety.

## How It Works (Big Picture)

```
User opens app
    │
    ▼
WebSocket connects → frontend sends {"type": "session_start"}
    │
    ▼
SessionEngine checks what's pending (priority order):
    │
    ├─ Homework due?     → "Welcome back. How did the mood monitoring go?"
    ├─ Session ready?    → "Ready for session 4? Today: thought catching"
    ├─ Screening needed? → Starts PHQ-9/GAD-7 conversationally
    └─ Nothing pending   → Normal reactive chat
```

Meanwhile, in the background:
- **Every message** → LLM infers mood, energy, themes → `InferredStateRecord` saved
- **Pattern detection** → 3 days low mood? → Flag PHQ-9 screening
- **Hourly** → Check for overdue homework → Send push notification
- **Daily** → Check for inactive users → Pause or nudge

---

## Architecture

The engine is built as a layer that wraps around the existing `ConversationEngine`:

```
User message
    │
    ▼
ConversationEngine._route_message()
    │
    ├─ [1] Crisis detection (existing, unchanged)
    ├─ [2] SessionEngine.try_handle()  ← NEW
    │      ├─ Active screening? → Process answer
    │      ├─ Active protocol?  → Fall through (LLM handles)
    │      └─ Nothing active    → Fall through
    ├─ [3] Active flow (existing)
    ├─ [4] Intent detection (existing)
    └─ [5] LLM freeform (existing)
```

Crisis detection always wins. The SessionEngine gets priority after crisis but before everything else. If it has nothing to do, it returns `None` and the existing routing takes over.

---

## Screening Layer

### Instruments

Three validated clinical instruments delivered conversationally through chat:

| Instrument | Condition | Questions | Score Range | Scale |
|-----------|-----------|-----------|-------------|-------|
| **PHQ-9** | Depression | 9 | 0-27 | 4-point (0-3) |
| **GAD-7** | Anxiety | 7 | 0-21 | 4-point (0-3) |
| **PCL-5** (brief) | PTSD screening | 8 | 0-32 | 5-point (0-4) |

Each question has two versions — the clinical wording and a conversational rephrasing that preserves validity:

- **Clinical:** "Little interest or pleasure in doing things"
- **Mirror:** "Over the past couple weeks, how often have you felt like things you usually enjoy just... didn't interest you?"

Responses are presented as quick-reply buttons: *Not at all / Several days / More than half the days / Nearly every day*

### What Triggers a Screening

1. **Pattern detection** — The system analyzes `InferredStateRecord` data from the last 7 days:
   - 3+ consecutive days with mood ≤ 3 → PHQ-9
   - "anxiety" theme for 3+ days → GAD-7
   - Absolutist language (≥3 per message) for 3+ days → PHQ-9
   - "trauma" theme in 2+ messages → PCL-5

2. **Scheduled** — Re-screen every 4 weeks (2 weeks if in active protocol)

3. **Protocol milestone** — Mid-protocol re-screening (e.g., session 4 of CBT)

A screening won't trigger if one was completed in the last 14 days.

### Severity Routing

After screening, the `SeverityRouter` determines what happens:

| Tier | PHQ-9 | GAD-7 | What Mirror Does |
|------|-------|-------|-----------------|
| Minimal | 0-4 | 0-4 | "Things look stable." Continue regular support |
| Mild | 5-9 | 5-9 | Offer protocol, no pressure |
| Moderate | 10-14 | 10-14 | Proactively recommend protocol |
| Moderately Severe | 15-19 | 15-18 | Protocol + therapist referral |
| Severe | 20-27 | 19-21 | **No protocol.** Therapist referral + supportive mode only |

PCL-5 ≥ 16 (positive screen) → Therapist referral, no protocol (no PTSD protocol in V1).

Severe-tier users are never enrolled in self-guided protocols. Mirror stays in supportive mode (validation, crisis resources, micro-actions) and strongly recommends professional help.

---

## Clinical Protocols

### CBT for Depression (8 sessions, PHQ-9 triggered)

**Entry:** PHQ-9 score 5-19

| Session | Focus | Existing Flow Used |
|---------|-------|--------------------|
| 1 | Psychoeducation — depression model, CBT triangle | — |
| 2 | Behavioral activation — identify dropped activities | — |
| 3 | Activity scheduling — weekly plan with mood tracking | — |
| 4 | Thought catching — automatic thought recognition | ReframeFlow |
| 5 | Cognitive restructuring — identify distortions, reframe | — |
| 6 | Core beliefs — connect patterns across thoughts | — |
| 7 | Behavioral experiments — test beliefs with small experiments | — |
| 8 | Relapse prevention — review PHQ-9 progress, build coping plan | — |

**Mid-protocol screening:** Session 4 (PHQ-9 re-administered to track progress)

### Anxiety Management (7 sessions, GAD-7 triggered)

**Entry:** GAD-7 score 5-19

| Session | Focus |
|---------|-------|
| 1 | Psychoeducation — anxiety cycle |
| 2 | Worry awareness — solvable vs hypothetical, worry time |
| 3 | Cognitive restructuring — catastrophizing, probability |
| 4 | Relaxation + grounding — breathing, PMR, 5-4-3-2-1 |
| 5 | Exposure hierarchy — rank avoided situations |
| 6 | Exposure practice — attempt lowest, process, advance |
| 7 | Relapse prevention — review GAD-7, build toolkit |

### Behavioral Activation (6 sessions, PHQ-9 triggered)

**Entry:** PHQ-9 score 5-19, OR fallback from CBT when cognitive work isn't landing

| Session | Focus | Existing Flow Used |
|---------|-------|--------------------|
| 1 | Activity monitoring — track activities + mood | — |
| 2 | Values connection — identify core values | ValuesFlow |
| 3 | Activity scheduling — energy-calibrated plan | — |
| 4 | Barriers and avoidance — identify patterns | — |
| 5 | Expanding repertoire — variety + social activities | — |
| 6 | Review and maintenance — PHQ-9 re-screen, build routine | — |

**Protocol switching:** If a user in CBT struggles with cognitive work (sessions 4-5), they can switch to Behavioral Activation starting at session 3 (sessions 1-2 are skipped since they overlap with early CBT).

### Cross-Protocol Rules

- One protocol at a time (and no concurrent program enrollment)
- After completing a protocol: 4-week monitoring period with bi-weekly screening
- If an anxiety protocol user scores high on PHQ-9 mid-protocol, flag for CBT after completion
- Protocols don't run simultaneously

---

## Adaptive Homework

Every session assigns homework with three difficulty tiers:

| Tier | When | Example (CBT Session 4) |
|------|------|------------------------|
| **Structured** | Default — completing homework | "Catch 3 automatic thoughts using the thought record" |
| **Gentle** | After 1 missed homework | "Notice one negative thought this week" |
| **Minimal** | After 2 missed in a row | "When you feel bad, pause and ask 'what was I just thinking?'" |

### Adaptive Pressure Rules

- **0 misses** → Structured homework, standard pace
- **1 miss** → Drop to gentle tier, no pressure
- **2 misses** → Drop to minimal tier, check in about barriers
- **3+ misses** → Pause protocol, switch to supportive mode
- **Re-engages** → Resume where they left off, no guilt
- **2 consecutive completions** → Reset back to structured tier

The system **never guilts the user.** Missed homework is met with gentleness, not pressure.

---

## Proactive Notifications

### Push Notifications (Web Push API)

Users opt in during onboarding. Max 2 per day, quiet hours enforced.

| Trigger | Message |
|---------|---------|
| Session ready | "Your session is ready when you are" |
| Homework reminder (1st) | "Quick check — how's the mood monitoring going?" |
| Homework reminder (2nd) | "No pressure. I'm here when you're ready." |
| Homework reminder (3rd) | "Just checking in." |
| 3 days inactive (in protocol) | "Your next session is ready when you are." |
| 7 days inactive | "No pressure, but I'm here when you need me." |
| 14 days inactive | Protocol paused + "We've paused your program. No rush." |

### In-App Proactive Greetings

When the user opens the app, Mirror speaks first. The `session_start` WebSocket message triggers `SessionEngine.handle_session_start()` which checks (in priority order):

1. **Homework review** → "Welcome back. How did [assignment] go?"
2. **Next session ready** → "Ready for session 4? Today we're working on thought catching."
3. **Screening due** → Starts the screening conversationally
4. **Nothing pending** → Normal chat, user leads

---

## Data Models

### ScreeningResult
Tracks each screening administration — instrument, per-item scores, total, severity tier, completion status. Supports interrupted screenings (status: "in_progress" with current_item index).

### ProtocolEnrollment
Tracks a user's enrollment in a protocol — current session number, status (enrolled/active/paused/graduated/switched/opted_out/referred_out), entry screening reference, score history over time, consecutive homework misses.

### ProtocolSession
One session within a protocol — goals, activities completed, notes, outcome, timestamps.

### Homework
A between-session assignment — description, adaptive tier, due date, completion status, user response, reminder count.

### PendingAction
Queue of proactive actions waiting for the user — screening due, homework review, etc. Priority-ordered, dismissable.

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/screening/history` | GET | User's completed screening results |
| `/api/screening/{id}` | GET | Single screening detail |
| `/api/protocols/current` | GET | Active protocol enrollment |
| `/api/protocols/history` | GET | Past protocol enrollments |
| `/api/protocols/{id}/sessions` | GET | Sessions for a protocol |
| `/api/homework/pending` | GET | Current pending homework |
| `/api/homework/{id}/complete` | POST | Mark homework done |
| `/api/notifications/preferences` | GET/PUT | Notification settings |
| `/api/notifications/subscribe` | POST | Register push subscription |
| `/api/notifications/pending-actions` | GET | Pending proactive actions |

All endpoints require authentication (Bearer token).

---

## File Structure

```
backend/app/
├── screening/
│   ├── instruments.py      # PHQ-9, GAD-7, PCL-5 definitions + scoring
│   ├── delivery.py         # ScreeningFlow — conversational chat delivery
│   └── router.py           # API endpoints
│
├── protocols/
│   ├── base.py             # BaseProtocol ABC, SessionDefinition, HomeworkTier
│   ├── cbt_depression.py   # 8-session CBT protocol
│   ├── anxiety.py          # 7-session anxiety protocol
│   ├── behavioral_activation.py  # 6-session BA protocol
│   └── registry.py         # Protocol lookup + eligibility matching
│
├── sessions/
│   ├── engine.py           # SessionEngine — orchestration layer
│   ├── homework.py         # HomeworkManager — adaptive tier logic
│   └── router.py           # API endpoints
│
├── notifications/
│   ├── service.py          # Push notifications + PendingAction queue
│   └── router.py           # API endpoints
│
├── tasks/
│   ├── scheduler.py        # APScheduler setup
│   ├── reminders.py        # Homework + re-engagement reminder jobs
│   └── screening_triggers.py  # Pattern-based screening detection
│
├── psychology/
│   └── severity.py         # SeverityRouter — tier classification
│
├── models/
│   ├── screening.py        # ScreeningResult
│   ├── protocol.py         # ProtocolEnrollment, ProtocolSession
│   ├── homework.py         # Homework
│   └── notification.py     # PendingAction
│
├── chat/
│   ├── engine.py           # ConversationEngine (modified — SessionEngine integration)
│   └── router.py           # WebSocket handler (modified — session_start)
```

---

## Key Thresholds

| Parameter | Value |
|-----------|-------|
| Screening cooldown | 14 days |
| Pattern analysis window | 7 days |
| Low mood threshold | mood_valence ≤ 3 |
| Low mood consecutive days for trigger | 3 |
| Anxiety theme days for trigger | 3 of 7 |
| Trauma messages for trigger | 2 |
| Homework miss → gentle tier | 1 miss |
| Homework miss → minimal tier | 2 misses |
| Homework miss → pause protocol | 3 misses |
| Re-engagement gentle nudge | 3 days inactive |
| Re-engagement stronger nudge | 7 days inactive |
| Re-engagement pause | 14 days inactive |
| Max push notifications per day | 2 |
| Inferred state confidence minimum | 0.3 |

---

## Adding a New Protocol

1. Create `backend/app/protocols/new_protocol.py`
2. Inherit from `BaseProtocol`
3. Set `protocol_id`, `display_name`, `instrument`, `min_score`, `max_score`, `mid_screening_session`
4. Define `sessions` property with `SessionDefinition` list (each with 3 homework tiers)
5. Register in `backend/app/protocols/registry.py`
6. Add eligible protocol ID to appropriate tier in `backend/app/psychology/severity.py`
7. Add tests in `backend/tests/test_protocols/`

## Adding a New Screening Instrument

1. Define the `Instrument` in `backend/app/screening/instruments.py` with items, thresholds, and response options
2. Add to `_INSTRUMENTS` registry
3. Add routing logic in `backend/app/psychology/severity.py`
4. Add trigger conditions in `backend/app/tasks/screening_triggers.py`
5. Add tests
