# Proactive Psychology Engine — Design Spec

**Date:** 2026-03-22
**Status:** Draft
**Author:** Davion + Claude

## Overview

Transform Mirror from a reactive chatbot into a proactive psychological support system that leads the user through structured clinical protocols. Mirror identifies issues through validated screening instruments, enrolls users in evidence-based treatment programs, assigns and tracks homework, and reaches out via push notifications — all gated by severity tiers to ensure safety.

## Goals

1. Mirror leads the conversation, not the user
2. Use validated clinical instruments for screening (PHQ-9, GAD-7, PCL-5)
3. Deliver full-depth clinical protocols (CBT for depression, anxiety management, behavioral activation)
4. Proactively reach out with session reminders, homework nudges, and re-engagement messages
5. Gate protocol access by severity — severe cases get therapist referral, not self-guided protocols
6. Adapt pressure to user engagement — never guilt, escalate gentleness on missed work

## Non-Goals

- Native mobile app (web push only for V1)
- In-app therapist directory or booking
- Concurrent protocol or program enrollment (one active at a time — see Section 2 on ProgramEnrollment)
- ML-based screening (validated instruments only)
- Replacing existing reactive chat (new system wraps around it)

---

## 1. Screening Layer

### Instruments

Three validated instruments for V1:

| Instrument | Condition | Items | Score Range |
|-----------|-----------|-------|-------------|
| PHQ-9 | Depression | 9 | 0-27 |
| GAD-7 | Anxiety | 7 | 0-21 |
| PCL-5 (abbreviated) | PTSD screening | 8 | 0-32 |

**PCL-5 approach:** The abbreviated 8-item version is used for screening only. A total score >= 16 (on the 8-item version) is considered a positive screen. PCL-5 does NOT trigger a protocol in V1 — PTSD requires specialized treatment beyond what Mirror offers. A positive PCL-5 screen triggers a therapist referral with PTSD-specific resources, and Mirror enters supportive mode for trauma-related content. Full 20-item PCL-5 is a future addition when/if a trauma-focused protocol is built.

### Trigger Mechanisms

1. **Pattern-based** — State inference detects:
   - Sustained low mood: mood_valence <= 3 for 3+ consecutive days (from `InferredStateRecord`)
   - Elevated anxiety: `"anxiety"` in themes for 3+ days OR sustained high absolutist language count (>= 3 per message for 3+ days)
   - Trauma indicators: `"trauma"` theme detected in 2+ messages within a week
   - Mirror initiates: "I've noticed some things I'd like to understand better. Mind if I ask you some specific questions?"
2. **Scheduled** — Re-screen every 4 weeks (or 2 weeks if in active protocol)
3. **Protocol milestone** — Mid-protocol and end-of-protocol assessments to measure change

### Conversational Delivery

Each instrument question is rephrased naturally but preserves clinical validity. Response options presented as quick-reply buttons mapping to standard scoring (0-3 scale).

Example:
- Clinical: "Over the last 2 weeks, how often have you been bothered by little interest or pleasure in doing things?"
- Mirror: "Over the past couple weeks, how often have you felt like things you usually enjoy just... didn't interest you?"
- Options: Not at all (0) / Several days (1) / More than half the days (2) / Nearly every day (3)

**Interruption handling:** Screenings are stateful — partial progress is saved to the `ScreeningResult` document with `status: "in_progress"`. If the user goes off-topic mid-screening, Mirror acknowledges what they said, responds naturally, then gently returns: "I want to hear about that. Before we continue, can we finish those few questions? We were on question 5 of 9." If the user closes the app mid-screening, resume from where they left off on next visit (within 24 hours). After 24 hours, restart the screening.

### Severity Tiers

| Tier | PHQ-9 | GAD-7 | PCL-5 (8-item) | Action |
|------|-------|-------|-----------------|--------|
| Minimal | 0-4 | 0-4 | 0-7 | No protocol needed, continue regular support |
| Mild | 5-9 | 5-9 | 8-15 | Protocol eligible (PHQ-9/GAD-7 only), offer it |
| Moderate | 10-14 | 10-14 | — | Protocol eligible, recommend proactively |
| Moderately Severe | 15-19 | 15-18 | — | Protocol + therapist referral suggestion |
| Severe | 20-27 | 19-21 | >= 16 | No protocol — therapist referral required, supportive mode only |

### Data Model

`ScreeningResult` (Beanie Document):
- `user_id: UUID`
- `instrument: str` (phq9 | gad7 | pcl5)
- `item_scores: list[int]`
- `total_score: int`
- `severity_tier: str`
- `status: str` (in_progress | completed)
- `current_item: int` (for interrupted screenings)
- `linked_enrollment_id: Optional[UUID]`
- `created_at: datetime`
- `completed_at: Optional[datetime]`

---

## 2. Session Engine Architecture

### Overview

The SessionEngine is a new orchestration layer that manages multi-session clinical protocols. It integrates into the existing `ConversationEngine._route_message()` as a new priority level.

### Integration Point

The SessionEngine is injected **inside** `ConversationEngine._route_message()` as a new routing priority between crisis detection and active-flow checks. This is a surgical change — one new elif block:

```python
# In ConversationEngine._route_message():
async def _route_message(self, user_id, message, conversation):
    # 1. Crisis detection (existing, unchanged)
    if self._detect_crisis(message):
        return await self._handle_crisis(...)

    # 2. SessionEngine (NEW — single insertion point)
    session_response = await self.session_engine.try_handle(user_id, message, conversation)
    if session_response:
        return session_response

    # 3. Active flow (existing, unchanged)
    if conversation.active_flow:
        return await self._continue_flow(...)

    # 4. Intent detection (existing, unchanged)
    # 5. LLM response (existing, unchanged)
```

`SessionEngine.try_handle()` returns a response if it has something to do (active protocol session, screening delivery, homework review), or `None` to fall through to existing routing.

### App Open / Proactive Greeting

When the user opens the app and connects via WebSocket, the frontend sends an initial `{"type": "session_start"}` message (new message type). The SessionEngine intercepts this to deliver proactive greetings:

```
WebSocket connected -> frontend sends {"type": "session_start"}
    -> SessionEngine checks pending actions (priority):
    1. Homework review pending -> "Welcome back. How did [homework] go?"
    2. Next session ready -> "Ready for session 4? Today we're working on..."
    3. Screening due -> "It's been a couple weeks. Mind if I check in?"
    4. Nothing pending -> no proactive message, normal reactive mode
```

The `session_start` message is distinct from regular chat messages. If SessionEngine has nothing pending, no message is sent and the user sees the normal chat interface.

### Relationship to Existing ProgramEnrollment

The existing `ProgramEnrollment` model (used by `ProgramFlow` for the "Belief Reset" 7-day program) coexists with the new `ProtocolEnrollment`. They serve different purposes:

- `ProgramEnrollment` — lightweight, single-flow programs (daily prompts within one conversation)
- `ProtocolEnrollment` — clinical protocols spanning multiple sessions with screening, homework, and adaptation

**Conflict prevention:** A user cannot be in an active protocol AND an active program simultaneously. The SessionEngine checks for active programs before enrolling in a protocol (and vice versa). If a user is mid-program and a screening flags protocol eligibility, Mirror waits until the program completes, then offers the protocol.

Future consideration: migrate existing programs into the protocol system. Not in V1 scope.

### Protocol Definition

Each protocol is a Python class defining:
- **Sessions** — ordered list of session definitions (goals, therapeutic activities, duration guidance)
- **Adaptation rules** — when to repeat, skip, or slow down based on user progress
- **Homework templates** — structured, gentle, and minimal versions per session (see Adaptive Homework)
- **Progress metrics** — what scores/signals indicate improvement or stagnation
- **Entry criteria** — severity tier + screening instrument that qualifies
- **Exit criteria** — target score reached, all sessions done, or user opts out

### Protocol State Machine

```
                                    +-> PAUSED (miss 3+ homework, severe score spike)
                                    |       |
                                    |       v (user re-engages)
ENROLLED -> SESSION_SCHEDULED -> SESSION_ACTIVE -> SESSION_COMPLETE -> HOMEWORK_ASSIGNED
    ^                                                                       |
    |           +-> GRADUATED (exit screening below mild, or all sessions)  |
    |           |                                                           |
    +-----------|-- HOMEWORK_REVIEWED <-- HOMEWORK_DUE <-------------------+
                |
                +-> REFERRED_OUT (severe score mid-protocol)
                +-> USER_OPTED_OUT (user requests to stop)
```

**Terminal states:** GRADUATED, REFERRED_OUT, USER_OPTED_OUT
**Resumable states:** PAUSED (can transition back to SESSION_SCHEDULED on re-engagement)

### Data Models

All models use Beanie (MongoDB ODM), consistent with existing codebase.

| Model | Purpose |
|-------|---------|
| `ProtocolEnrollment` (Document) | User enrolled in protocol — protocol_id, current_session_number, status (enrolled/active/paused/graduated/referred_out/opted_out), entry_screening_id, screening_scores (list of score snapshots over time), start_date, end_date |
| `ProtocolSession` (Document) | One session instance — enrollment_id, session_number, goals, activities_completed, session_notes, outcome, started_at, completed_at |
| `Homework` (Document) | Assignment — enrollment_id, session_number, description, adaptive_tier (structured/gentle/minimal), due_date, status (assigned/reminded/completed/skipped), user_response, completed_at, reminder_count |
| `ScreeningResult` (Document) | From Section 1 — linked to enrollment for progress tracking |

### Adaptive Homework System

Each protocol session defines three homework tiers:

| Tier | When Used | Example (CBT Session 4) |
|------|-----------|------------------------|
| **Structured** | Default — user completing homework consistently | "Catch 3 automatic thoughts this week using the thought record" |
| **Gentle** | After 1 missed homework | "Just notice one moment this week where a negative thought pops up — no need to write it down" |
| **Minimal** | After 2 missed in a row | "When you notice yourself feeling down, pause for 5 seconds and name the feeling" |

After 3+ consecutive misses across any tier: pause protocol, check in about barriers. Homework tier resets to structured after 2 consecutive completions.

### Adaptive Pacing Summary

- Completes homework consistently -> standard pace, structured homework
- Misses 1 homework -> gentle nudge, no pressure, drop to gentle tier
- Misses 2 in a row -> lighter assignments (minimal tier), check in about barriers
- Misses 3+ -> pause protocol, switch to supportive mode, ask what's going on
- Re-engages -> resume where they left off, no guilt, structured tier

---

## 3. Clinical Protocols

### Protocol 1: CBT for Depression (PHQ-9 triggered, 8 sessions)

**Entry:** PHQ-9 score 5-19 (mild to moderately severe)

| Session | Focus | Homework (Structured) | Homework (Gentle) | Homework (Minimal) |
|---------|-------|-----------------------|--------------------|---------------------|
| 1 | Psychoeducation — depression model, thoughts-feelings-behaviors connection | Mood monitoring for 3 days | Notice your mood once a day, no logging needed | Just notice if your mood changes at all today |
| 2 | Behavioral activation intro — identify dropped activities, use energy ladder | Do 1 pleasurable activity | Think of one thing you used to enjoy | Notice one moment of pleasure this week |
| 3 | Activity scheduling — concrete weekly plan using existing habit/activity system | Follow schedule for 3 days, log mood before/after | Try one scheduled activity this week | When you have a free moment, do something small you enjoy |
| 4 | Thought catching — automatic thought recognition, uses existing ReframeFlow | Catch 3 automatic thoughts using thought record | Notice one negative thought this week | When you feel bad, pause and ask "what was I just thinking?" |
| 5 | Cognitive restructuring — work through caught thoughts, identify distortions (existing CBT module) | Reframe 2 thoughts independently | Try questioning one negative thought | Notice if a thought is a fact or an interpretation |
| 6 | Core beliefs — connect patterns across automatic thoughts, identify underlying beliefs | Notice when a core belief gets activated | Reflect on what theme connects your negative thoughts | No homework — just sit with what we discussed |
| 7 | Behavioral experiments — design experiments to test beliefs | Run one experiment | Think of one small way to test a belief | Notice one moment where reality didn't match your fear |
| 8 | Relapse prevention — review progress (compare PHQ-9), identify warning signs, build coping plan | Exit screening | Exit screening | Exit screening |

### Protocol 2: Anxiety Management (GAD-7 triggered, 7 sessions)

**Entry:** GAD-7 score 5-19

| Session | Focus | Homework (Structured) | Homework (Gentle) | Homework (Minimal) |
|---------|-------|-----------------------|--------------------|---------------------|
| 1 | Psychoeducation — anxiety cycle (trigger-thought-sensation-avoidance-reinforcement) | Track 3 worry episodes | Notice one worry episode this week | Just notice when you feel anxious |
| 2 | Worry awareness — solvable vs hypothetical worries, worry time concept | Postpone worries to 15-min worry window | Try postponing one worry | When you catch yourself worrying, label it: "solvable or hypothetical?" |
| 3 | Cognitive restructuring — catastrophizing, probability overestimation, uncertainty intolerance | Challenge 2 anxious predictions | Question one anxious prediction | Notice when you predict the worst |
| 4 | Relaxation + grounding — breathing, progressive muscle relaxation, 5-4-3-2-1 | Practice one technique daily | Try the technique 3 times this week | When you feel tense, take 3 slow breaths |
| 5 | Exposure hierarchy — rank avoided situations, start with easiest | Approach one low-level avoided situation | Think about approaching one situation | Notice one moment of avoidance |
| 6 | Exposure practice — review experience, plan next step up hierarchy | Next exposure level | Revisit the same level one more time | Sit with discomfort for 30 seconds when it arises |
| 7 | Relapse prevention — review GAD-7 progress, early warning signs, coping toolkit | Exit screening | Exit screening | Exit screening |

### Protocol 3: Behavioral Activation (PHQ-9 triggered, 6 sessions)

**Entry:** PHQ-9 score 5-19, OR adaptive fallback from CBT protocol when cognitive work isn't landing

When switching from CBT: Sessions 1-2 of BA are skipped (psychoeducation and values already covered in CBT sessions 1-3). BA starts at session 3 (activity scheduling). The CBT enrollment is marked `status: "switched"` (subtype of opted_out) with a reference to the new BA enrollment.

| Session | Focus | Homework (Structured) | Homework (Gentle) | Homework (Minimal) |
|---------|-------|-----------------------|--------------------|---------------------|
| 1 | Activity monitoring — track daily activities + mood rating | Log activities for 3 days | Log activities for 1 day | Notice what you do today |
| 2 | Values connection — use existing ValuesFlow, map values to activity categories | Pick 3 values-aligned dropped activities | Pick 1 values-aligned activity | Think about what matters to you |
| 3 | Activity scheduling — 1 activity/day, energy-calibrated via existing energy ladder | Follow schedule for 3 days | Try 1 scheduled activity | Do one small thing tomorrow |
| 4 | Barriers and avoidance — identify patterns, problem-solve barriers | When noticing avoidance, do the 2-minute version | Notice one moment of avoidance | Just notice what you avoid |
| 5 | Expanding repertoire — add variety and social activities, increase gradually | Try one new + one social activity | Try one new activity | Do something slightly different from routine |
| 6 | Review and maintenance — PHQ-9 re-screen, compare activity levels, build sustainable routine | Exit screening | Exit screening | Exit screening |

### Cross-Protocol Rules

- If anxiety protocol user scores high on PHQ-9 mid-protocol, flag and offer CBT after completion
- If CBT user struggles with cognitive work (sessions 4-5), offer switch to Behavioral Activation (skipping BA sessions 1-2)
- One protocol at a time (and no concurrent program enrollment)
- After completing a protocol: 4-week monitoring period with bi-weekly screening before offering another

---

## 4. Proactive Scheduler & Notifications

### Scheduler Service

APScheduler with **MongoDB jobstore** (via `apscheduler.jobstores.mongodb`) for persistence across server restarts. This ensures:
- Scheduled jobs survive server restarts
- Missed jobs are caught up on startup (with deduplication — see below)
- Only one scheduler instance runs even with multiple workers (use `apscheduler.schedulers.background.BackgroundScheduler` with a lock collection in MongoDB)

**Startup behavior:** On server start, the scheduler checks for missed jobs. Missed reminders older than 2 hours are discarded (not sent retroactively). Missed daily checks run immediately.

**Multi-worker safety:** The MongoDB jobstore acts as a distributed lock. Only one worker picks up each job. APScheduler's built-in `replace_existing=True` prevents duplicates.

| Job | Frequency | Logic |
|-----|-----------|-------|
| Session reminder | Hourly check | If session scheduled and user hasn't opened app (no `session_start` in last 12h), send push: "Your session is ready when you are" |
| Homework reminder | Daily at user's preferred time | Adaptive: 1st reminder warm, 2nd lighter, 3rd just checks in without mentioning homework |
| Screening interval | Daily check | If 4 weeks since last screening (2 weeks if in protocol), queue screening on next visit |
| Re-engagement | Daily check | 3 days inactive during protocol: gentle nudge. 7 days: "No pressure, I'm here." 14 days: pause protocol, supportive message |
| Pattern-triggered screening | On each state inference (not scheduled — triggered synchronously) | 3+ days of mood_valence <= 3 or anxiety theme for 3+ days without active screening -> flag for screening |

### Notification Channels (V1)

1. **In-app banner** — On app open (`session_start` message), Mirror greets with highest-priority pending action (session ready > homework due > screening due). Stored as `PendingAction` queue in MongoDB.
2. **Web Push** — Web Push API (VAPID keys), user opts in during onboarding. Short, warm messages. Max 2 per day. Quiet hours enforced.

### User Notification Preferences

Stored as fields on the `User` document (not a separate model):

| Setting | Default |
|---------|---------|
| `preferred_session_time` | evening |
| `notification_enabled` | false (opt-in) |
| `max_notifications_per_day` | 2 |
| `quiet_hours_start` | 22:00 |
| `quiet_hours_end` | 08:00 |

---

## 5. Severity Router & Safety

### Routing Decision

```
ScreeningResult -> SeverityRouter -> RoutingDecision
    - tier: minimal | mild | moderate | moderately_severe | severe
    - action: monitor | offer_protocol | recommend_protocol | protocol_plus_referral | referral_only
    - eligible_protocols: list
    - referral_required: bool
    - message: what Mirror says
```

### Tier Behavior

| Tier | Mirror's Behavior |
|------|-------------------|
| Minimal (0-4) | "Things look stable. I'm here if anything comes up." Re-screen in 4 weeks |
| Mild (5-9) | Offer protocol, no pressure |
| Moderate (10-14) | Proactively recommend protocol |
| Moderately Severe (15-19) | Offer protocol AND suggest professional help |
| Severe (20+) | No protocol. Therapist referral + supportive mode (validation, crisis safety, gentle check-ins, MVAs) |
| PCL-5 positive (>= 16) | No protocol (no PTSD protocol in V1). Therapist referral with trauma-specific resources + supportive mode |

### Mid-Protocol Safety

- Every session: mini safety check (mood + risk keywords via existing crisis detection)
- Mid-protocol score jumps to severe -> pause protocol (status: REFERRED_OUT), supportive mode + referral
- Score improved below mild -> celebrate, offer early graduation (status: GRADUATED)
- Score plateaus 3+ sessions -> acknowledge, suggest different approach or therapist

### Supportive Mode (Severe Tier)

Mirror continues to:
- Do daily check-ins if user wants
- Provide crisis resources
- Validate feelings
- Suggest micro-actions (existing MVA system)
- Track mood

Mirror does NOT run structured protocols for severe-tier users without a professional involved.

### Therapist Referral Resources (V1)

Static resource list:
- Crisis lines (existing in CrisisFlow)
- "Ask your doctor for a referral"
- Psychology Today therapist finder
- Open Path Collective (affordable therapy)
- SAMHSA helpline

---

## 6. File Structure

```
backend/app/
+-- screening/
|   +-- instruments.py        # PHQ-9, GAD-7, PCL-5 question definitions, scoring
|   +-- delivery.py           # Conversational rephrasing + quick-reply formatting
|   +-- router.py             # API endpoints for screening results/history
|
+-- protocols/
|   +-- base.py               # BaseProtocol ABC
|   +-- cbt_depression.py     # 8-session CBT protocol
|   +-- anxiety.py            # 7-session anxiety protocol
|   +-- behavioral_activation.py  # 6-session BA protocol
|   +-- registry.py           # Maps screening results to eligible protocols
|
+-- sessions/
|   +-- engine.py             # SessionEngine orchestration + try_handle()
|   +-- homework.py           # Homework assignment + adaptive pressure logic
|   +-- router.py             # API endpoints for session state, protocol progress
|
+-- notifications/
|   +-- service.py            # Web Push (VAPID) + in-app PendingAction delivery
|   +-- router.py             # API endpoints for notification preferences, push subscription
|
+-- tasks/
|   +-- scheduler.py          # APScheduler setup with MongoDB jobstore
|   +-- reminders.py          # Session, homework, re-engagement reminder logic
|   +-- screening_triggers.py # Pattern-based screening trigger checks
|
+-- psychology/
|   +-- severity.py           # SeverityRouter — tier classification + routing
|
+-- models/
|   +-- screening.py          # ScreeningResult (Beanie Document)
|   +-- protocol.py           # ProtocolEnrollment, ProtocolSession (Beanie Documents)
|   +-- homework.py           # Homework (Beanie Document)
|   +-- notification.py       # PendingAction (Beanie Document)
```

### Integration with Existing Code

- `ConversationEngine._route_message()` — single new elif block after crisis detection, calling `SessionEngine.try_handle()`
- `ConversationEngine` WebSocket handler — new `session_start` message type for proactive greetings
- `ReframeFlow`, `ValuesFlow` — reused as in-session activities within protocols
- `state_inference.py` — continues running on every message, feeds screening triggers synchronously
- `energy.py` — used for homework energy calibration
- `patterns.py` — continues independently
- `suggestions.py` — still active for non-protocol interactions
- `User` model — add notification preference fields
- `ProgramEnrollment` — coexists, mutual exclusion enforced by SessionEngine

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/screening/history` | GET | User's screening history with scores over time |
| `/api/screening/{id}` | GET | Single screening result detail |
| `/api/protocols/current` | GET | Current active protocol enrollment + session state |
| `/api/protocols/history` | GET | Past protocol enrollments with outcomes |
| `/api/protocols/{id}/sessions` | GET | Sessions for a protocol enrollment |
| `/api/sessions/{id}` | GET | Single session detail with homework |
| `/api/homework/pending` | GET | Current pending homework assignments |
| `/api/homework/{id}/complete` | POST | Mark homework as completed with user response |
| `/api/notifications/preferences` | GET/PUT | Notification settings |
| `/api/notifications/subscribe` | POST | Register web push subscription |
| `/api/notifications/pending-actions` | GET | Current pending actions for in-app banner |

---

## 7. Data Flow Example

```
Day 1: State inference detects low mood for 3rd consecutive day
    -> screening_triggers.py checks InferredStateRecord: mood_valence <= 3 for 3 days
    -> Flags PHQ-9 screening needed (creates PendingAction)
    -> Next app open: frontend sends {"type": "session_start"}
    -> SessionEngine.try_handle() sees pending screening
    -> Delivers PHQ-9 conversationally (9 questions as chat messages with quick-reply buttons)
    -> User scores 12 (moderate)
    -> ScreeningResult saved, SeverityRouter returns: recommend CBT for depression
    -> Mirror: "I'd recommend we work through a structured program together..."
    -> User accepts -> ProtocolEnrollment created (status: ENROLLED)
    -> Session 1 scheduled -> status: SESSION_SCHEDULED

Day 2: Push notification: "Your first session is ready"
    -> User opens app, sends session_start
    -> SessionEngine: "Today we're going to talk about what depression actually is..."
    -> Session 1 runs (psychoeducation) -> ProtocolSession created
    -> Homework assigned: mood monitoring for 3 days (tier: structured)
    -> Homework document created, status: assigned

Day 3-4: Daily reminder at preferred time (from scheduler)
    -> User logs moods through existing check-in system
    -> Homework marked completed via /api/homework/{id}/complete

Day 5: User opens app, sends session_start
    -> SessionEngine: "Welcome back. Before session 2, how did the mood monitoring go?"
    -> Reviews homework response -> Session 2 begins (behavioral activation intro)
    -> New homework assigned

... 8-session cycle ...

Session 4 mid-protocol: PHQ-9 re-screen
    -> Score: 12 -> 9 (improving)
    -> Continue protocol

Session 8: Exit PHQ-9 re-screening
    -> Score: 12 -> 6
    -> Mirror: "When we started, your score was 12. Now it's 6. That's real progress."
    -> ProtocolEnrollment status: GRADUATED
    -> 4-week monitoring period begins with bi-weekly screening
```
