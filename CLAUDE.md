# Mirror - Personal Growth Platform

## Architecture
- **Backend**: FastAPI (Python) at `backend/`
- **Frontend**: SvelteKit at `frontend/`
- **CLI**: Typer client at `cli/` (not yet built)
- **Docs**: `docs/` for architecture and psychology engine docs

Read `docs/architecture.md` for full system design.

## Module Map

### Backend (`backend/app/`)
- `main.py` - FastAPI app factory, lifespan events, router mounting
- `config.py` - Pydantic BaseSettings, env-driven configuration
- `dependencies.py` - Dependency injection: db session, current_user
- `auth/` - Email+password auth with bcrypt + JWT
- `chat/engine.py` - **ConversationEngine** - routes messages to flows or LLM
- `chat/flows/` - Structured therapeutic flows (check-in, reframe, tiny habits, crisis)
- `chat/llm/` - Claude API integration with context-aware system prompts
- `psychology/` - Pure domain logic (no HTTP): CBT, tiny habits, energy ladders, patterns, suggestions
- `dashboard/` - Aggregation queries for dashboard data
- `tasks/` - Background jobs: pattern detection, streak calculation
- `models/` - Beanie ODM documents (User, Conversation, Message, CheckIn, etc.) on MongoDB

## Key Design Principles
1. **Never guilt the user.** Validate feelings first, suggest second.
2. **Energy-calibrated actions.** At energy ≤ 2, only suggest rest or micro-actions.
3. **Track outcomes.** Every suggestion gets a worked/didn't signal to self-calibrate.
4. **Minimum data thresholds.** No patterns surfaced until ≥ 5 data points.
5. **Crisis safety first.** CrisisFlow has highest routing priority, always.

## How to Improve This System

### Adding a New Psychology Strategy
1. Create `backend/app/psychology/new_strategy.py`
2. Implement the strategy interface
3. Register in the suggestion engine (`suggestions.py`)
4. Add energy-level constraints
5. Add tests in `backend/tests/test_psychology/`
6. Document in `docs/psychology-engine.md`

### Adding a New Chat Flow
1. Create `backend/app/chat/flows/new_flow.py`
2. Inherit from `BaseFlow` in `flows/base.py`
3. Define steps as a state machine
4. Register in `FlowRegistry` (`flows/registry.py`)
5. Add intent detection keywords in `chat/engine.py`
6. Add tests in `backend/tests/test_chat/test_flows/`

### Adding a New Pattern Rule
1. Add detection logic in `backend/app/psychology/patterns.py`
2. Set `minimum_data_points` (never below 5)
3. Set confidence threshold (minimum 0.6 to surface)
4. Add tests with synthetic data
5. Document in `docs/psychology-engine.md`

### Database Changes
1. Add new Beanie Document models in `backend/app/models/`
2. Register new documents in `backend/app/models/__init__.py` for Beanie init
3. Never remove fields from existing documents, only add (backwards compatibility)
4. MongoDB collections are auto-created by Beanie on first use

## Development
```bash
make dev          # Start FastAPI dev server
make test         # Run pytest
make lint         # Run ruff
```

## Testing
- All tests in `backend/tests/`, mirrors `app/` structure
- mongomock or testcontainers for DB tests
- Mock Claude API by default (`@pytest.mark.llm` for real API tests)
- Scenario tests verify psychological correctness (energy=1 → only MVAs, etc.)
