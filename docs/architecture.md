# Mirror Architecture

## System Overview

```
┌──────────────┐     WebSocket/REST      ┌──────────────────┐
│  SvelteKit   │ ◄──────────────────────► │    FastAPI        │
│  Frontend    │     /api/* proxied       │    Backend        │
│  :5173       │                          │    :8000          │
└──────────────┘                          └────────┬─────────┘
                                                   │
┌──────────────┐     REST/WebSocket                │
│  Typer CLI   │ ◄─────────────────────────────────┘
│  mirror cmd  │
└──────────────┘                          ┌──────────────────┐
                                          │  SQLite / Postgres│
                                          │  (via SQLAlchemy)  │
                                          └──────────────────┘
```

## Backend Modules

### Chat System (`app/chat/`)
- **engine.py** - ConversationEngine: routes messages to flows or generates responses
- **manager.py** - WebSocket ConnectionManager (per-user connections)
- **flows/** - Structured therapeutic flows (state machines)
  - `base.py` - BaseFlow ABC
  - `check_in.py` - Daily check-in (mood, energy, tags, intention)
  - `crisis.py` - Crisis detection + resources (HIGHEST PRIORITY)
  - `reframe.py` - CBT thought challenging exercise
  - `tiny_habit.py` - BJ Fogg habit design wizard
  - `registry.py` - Flow registration and lookup

### Psychology Engine (`app/psychology/`)
Pure domain logic, no HTTP. Each module is independently testable.

- **cbt.py** - Cognitive distortion detection (9 types) + template-based reframing
- **energy.py** - Energy ladders per life area (4 areas × 8 levels) + MVA generation
- **tiny_habits.py** - Anchor-behavior-celebration framework + energy scaling
- **suggestions.py** - Strategy selection engine (energy-matched, tracks effectiveness)
- **patterns.py** - Statistical pattern detection (temporal, mood-energy, streaks, strategy effectiveness)
- **life_areas.py** - Multi-dimensional scoring across physical/mental/career/habits

### Data Layer (`app/models/`)
SQLAlchemy 2.0 models with UUID PKs, timestamp mixins, JSON columns.

10 models: User, Conversation, Message, CheckIn, ThoughtRecord, Habit, HabitLog, LifeAreaScore, DetectedPattern, Suggestion, EnergyReading

## Message Flow

```
User message arrives via WebSocket
        │
        ▼
ConversationEngine._route_message()
        │
        ├─ Priority 1: Crisis detection → CrisisFlow (always)
        ├─ Priority 2: Active flow → flow.process()
        ├─ Priority 3: Intent detection → start matching flow
        └─ Priority 4: Smart response (distortion detection, energy validation, overwhelm handling)
        │
        ▼
Save user + assistant messages to DB
```

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Psychology module = pure Python | No HTTP in psychology/ | Independently testable, reusable |
| Flows = state machines | BaseFlow ABC with steps | Predictable, testable, no LLM needed |
| Crisis = highest priority | Always checked first | Safety critical, non-negotiable |
| Energy ladders = per-area | 4 areas × 8 levels | Different areas need different actions |
| Pattern min threshold = 5 | No patterns < 5 data points | Prevent false patterns from sparse data |
| JWT auth | Stateless, refresh tokens | Scales to multi-user, no session store |
