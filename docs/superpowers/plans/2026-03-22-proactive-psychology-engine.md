# Proactive Psychology Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Mirror from a reactive chatbot into a proactive psychological support system with validated screening, clinical protocols, adaptive homework, and push notifications.

**Architecture:** A new SessionEngine orchestration layer integrates into the existing ConversationEngine as a single routing priority between crisis detection and flow routing. Screening instruments, clinical protocols, and homework are modeled as Beanie Documents on MongoDB. APScheduler with MongoDB jobstore handles background reminders.

**Tech Stack:** FastAPI, Beanie/MongoDB, APScheduler, Web Push API (py-vapid + pywebpush), mongomock-motor for tests

**Spec:** `docs/superpowers/specs/2026-03-22-proactive-psychology-engine-design.md`

---

## File Map

### New Files

| File | Responsibility |
|------|---------------|
| `backend/app/models/screening.py` | ScreeningResult Beanie Document |
| `backend/app/models/protocol.py` | ProtocolEnrollment, ProtocolSession Documents |
| `backend/app/models/homework.py` | Homework Document |
| `backend/app/models/notification.py` | PendingAction Document |
| `backend/app/screening/__init__.py` | Package init |
| `backend/app/screening/instruments.py` | PHQ-9, GAD-7, PCL-5 question definitions + scoring |
| `backend/app/screening/delivery.py` | ScreeningFlow — conversational delivery as a BaseFlow |
| `backend/app/screening/router.py` | API endpoints for screening history |
| `backend/app/psychology/severity.py` | SeverityRouter — tier classification + routing decisions |
| `backend/app/protocols/__init__.py` | Package init |
| `backend/app/protocols/base.py` | BaseProtocol ABC — session definitions, homework tiers |
| `backend/app/protocols/cbt_depression.py` | 8-session CBT protocol |
| `backend/app/protocols/anxiety.py` | 7-session anxiety protocol |
| `backend/app/protocols/behavioral_activation.py` | 6-session BA protocol |
| `backend/app/protocols/registry.py` | Maps screening results to eligible protocols |
| `backend/app/sessions/__init__.py` | Package init |
| `backend/app/sessions/engine.py` | SessionEngine — try_handle() orchestration |
| `backend/app/sessions/homework.py` | Homework assignment + adaptive pressure logic |
| `backend/app/sessions/router.py` | API endpoints for protocol/session/homework state |
| `backend/app/notifications/__init__.py` | Package init |
| `backend/app/notifications/service.py` | PendingAction queue + Web Push delivery |
| `backend/app/notifications/router.py` | API endpoints for preferences + push subscription |
| `backend/app/tasks/__init__.py` | Package init |
| `backend/app/tasks/scheduler.py` | APScheduler setup with MongoDB jobstore |
| `backend/app/tasks/reminders.py` | Session, homework, re-engagement reminder logic |
| `backend/app/tasks/screening_triggers.py` | Pattern-based screening trigger checks |
| `backend/tests/test_screening/__init__.py` | Test package |
| `backend/tests/test_screening/test_instruments.py` | Tests for instrument scoring |
| `backend/tests/test_screening/test_delivery.py` | Tests for screening flow |
| `backend/tests/test_screening/test_severity.py` | Tests for severity router |
| `backend/tests/test_protocols/__init__.py` | Test package |
| `backend/tests/test_protocols/test_base.py` | Tests for protocol base |
| `backend/tests/test_protocols/test_cbt.py` | Tests for CBT protocol definition |
| `backend/tests/test_protocols/test_registry.py` | Tests for protocol registry |
| `backend/tests/test_sessions/__init__.py` | Test package |
| `backend/tests/test_sessions/test_engine.py` | Tests for SessionEngine |
| `backend/tests/test_sessions/test_homework.py` | Tests for adaptive homework |
| `backend/tests/test_notifications/__init__.py` | Test package |
| `backend/tests/test_notifications/test_service.py` | Tests for notification service |
| `backend/tests/test_tasks/__init__.py` | Test package |
| `backend/tests/test_tasks/test_screening_triggers.py` | Tests for pattern-based triggers |
| `backend/tests/test_tasks/test_reminders.py` | Tests for reminder logic |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/models/__init__.py` | Register new document models |
| `backend/app/models/base.py` | Add new models to `init_beanie()` call |
| `backend/app/models/user.py` | Add notification preference fields |
| `backend/app/chat/engine.py` | Add SessionEngine routing priority + session_start handling |
| `backend/app/chat/router.py` | Handle `session_start` WebSocket message type |
| `backend/app/main.py` | Mount new routers, start scheduler in lifespan |
| `backend/pyproject.toml` | Add APScheduler, pywebpush, py-vapid dependencies |
| `backend/app/config.py` | Add VAPID key settings |
| `backend/tests/conftest.py` | Add new models to ALL_MODELS list |

---

## Task 1: Data Models

**Files:**
- Create: `backend/app/models/screening.py`
- Create: `backend/app/models/protocol.py`
- Create: `backend/app/models/homework.py`
- Create: `backend/app/models/notification.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/base.py`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/test_models/test_new_models.py`

- [ ] **Step 1: Write tests for new models**

Create `backend/tests/test_models/__init__.py` (empty) and `backend/tests/test_models/test_new_models.py`:

```python
import pytest
from datetime import datetime, timezone, timedelta

from app.models.screening import ScreeningResult
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.homework import Homework
from app.models.notification import PendingAction


class TestScreeningResult:
    @pytest.mark.asyncio
    async def test_create_screening_result(self):
        sr = ScreeningResult(
            user_id="user-1",
            instrument="phq9",
            item_scores=[1, 2, 1, 0, 3, 2, 1, 0, 1],
            total_score=11,
            severity_tier="moderate",
            status="completed",
            current_item=9,
        )
        await sr.insert()
        found = await ScreeningResult.get(sr.id)
        assert found.instrument == "phq9"
        assert found.total_score == 11
        assert found.severity_tier == "moderate"

    @pytest.mark.asyncio
    async def test_in_progress_screening(self):
        sr = ScreeningResult(
            user_id="user-1",
            instrument="gad7",
            item_scores=[2, 1],
            total_score=3,
            severity_tier="",
            status="in_progress",
            current_item=2,
        )
        await sr.insert()
        found = await ScreeningResult.get(sr.id)
        assert found.status == "in_progress"
        assert found.current_item == 2

    @pytest.mark.asyncio
    async def test_find_user_screenings(self):
        for i in range(3):
            await ScreeningResult(
                user_id="user-1",
                instrument="phq9",
                item_scores=[1] * 9,
                total_score=9,
                severity_tier="mild",
                status="completed",
                current_item=9,
            ).insert()
        results = await ScreeningResult.find(
            ScreeningResult.user_id == "user-1"
        ).to_list()
        assert len(results) == 3


class TestProtocolEnrollment:
    @pytest.mark.asyncio
    async def test_create_enrollment(self):
        pe = ProtocolEnrollment(
            user_id="user-1",
            protocol_id="cbt_depression",
            current_session_number=1,
            status="enrolled",
        )
        await pe.insert()
        found = await ProtocolEnrollment.get(pe.id)
        assert found.protocol_id == "cbt_depression"
        assert found.status == "enrolled"

    @pytest.mark.asyncio
    async def test_find_active_enrollment(self):
        await ProtocolEnrollment(
            user_id="user-1",
            protocol_id="cbt_depression",
            current_session_number=3,
            status="active",
        ).insert()
        active = await ProtocolEnrollment.find_one(
            ProtocolEnrollment.user_id == "user-1",
            ProtocolEnrollment.status.is_in(["enrolled", "active", "paused"]),
        )
        assert active is not None
        assert active.status == "active"


class TestHomework:
    @pytest.mark.asyncio
    async def test_create_homework(self):
        hw = Homework(
            user_id="user-1",
            enrollment_id="enroll-1",
            session_number=1,
            description="Mood monitoring for 3 days",
            adaptive_tier="structured",
        )
        await hw.insert()
        found = await Homework.get(hw.id)
        assert found.adaptive_tier == "structured"
        assert found.status == "assigned"


class TestPendingAction:
    @pytest.mark.asyncio
    async def test_create_pending_action(self):
        pa = PendingAction(
            user_id="user-1",
            action_type="screening_due",
            priority=3,
            data={"instrument": "phq9"},
        )
        await pa.insert()
        found = await PendingAction.get(pa.id)
        assert found.action_type == "screening_due"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_models/test_new_models.py -v 2>&1 | head -30
```

Expected: ImportError — modules don't exist yet.

- [ ] **Step 3: Create ScreeningResult model**

Create `backend/app/models/screening.py`:

```python
from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ScreeningResult(Document):
    user_id: Indexed(str)
    instrument: str  # phq9 | gad7 | pcl5
    item_scores: list[int] = Field(default_factory=list)
    total_score: int = 0
    severity_tier: str = ""  # minimal | mild | moderate | moderately_severe | severe
    status: str = "in_progress"  # in_progress | completed
    current_item: int = 0
    linked_enrollment_id: Optional[str] = None
    created_at: Indexed(datetime) = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = None

    class Settings:
        name = "screening_results"
        indexes = [
            [("user_id", 1), ("created_at", -1)],
            [("user_id", 1), ("instrument", 1), ("status", 1)],
        ]
```

- [ ] **Step 4: Create ProtocolEnrollment and ProtocolSession models**

Create `backend/app/models/protocol.py`:

```python
from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class ProtocolEnrollment(Document):
    user_id: Indexed(str)
    protocol_id: str  # cbt_depression | anxiety | behavioral_activation
    current_session_number: int = 0
    status: str = "enrolled"  # enrolled | active | paused | graduated | referred_out | opted_out | switched
    entry_screening_id: Optional[str] = None
    screening_scores: list[dict] = Field(default_factory=list)  # [{score, date, instrument}]
    switched_to_enrollment_id: Optional[str] = None
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None
    consecutive_homework_misses: int = 0

    class Settings:
        name = "protocol_enrollments"
        indexes = [
            [("user_id", 1), ("status", 1)],
        ]


class ProtocolSession(Document):
    enrollment_id: Indexed(str)
    user_id: str
    session_number: int
    goals: list[str] = Field(default_factory=list)
    activities_completed: list[str] = Field(default_factory=list)
    session_notes: str = ""
    outcome: str = ""  # completed | skipped
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    class Settings:
        name = "protocol_sessions"
        indexes = [
            [("enrollment_id", 1), ("session_number", 1)],
        ]
```

- [ ] **Step 5: Create Homework model**

Create `backend/app/models/homework.py`:

```python
from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class Homework(Document):
    user_id: Indexed(str)
    enrollment_id: str
    session_number: int
    description: str
    adaptive_tier: str = "structured"  # structured | gentle | minimal
    due_date: Optional[datetime] = None
    status: str = "assigned"  # assigned | reminded | completed | skipped
    user_response: Optional[str] = None
    completed_at: Optional[datetime] = None
    reminder_count: int = 0

    class Settings:
        name = "homework"
        indexes = [
            [("user_id", 1), ("status", 1)],
            [("enrollment_id", 1), ("session_number", 1)],
        ]
```

- [ ] **Step 6: Create PendingAction model**

Create `backend/app/models/notification.py`:

```python
from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class PendingAction(Document):
    user_id: Indexed(str)
    action_type: str  # homework_review | session_ready | screening_due
    priority: int = 5  # 1 = highest
    data: dict = Field(default_factory=dict)
    dismissed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    class Settings:
        name = "pending_actions"
        indexes = [
            [("user_id", 1), ("dismissed", 1), ("priority", 1)],
        ]
```

- [ ] **Step 7: Add notification preferences to User model**

In `backend/app/models/user.py`, add these fields to the User class:

```python
# Notification preferences
preferred_session_time: str = "evening"  # morning | afternoon | evening
notification_enabled: bool = False
max_notifications_per_day: int = 2
quiet_hours_start: str = "22:00"
quiet_hours_end: str = "08:00"
push_subscription: Optional[dict] = None  # Web Push subscription JSON
```

- [ ] **Step 8: Register new models in base.py and __init__.py**

In `backend/app/models/base.py`, add to the `init_beanie()` document_models list:

```python
from app.models.screening import ScreeningResult
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.homework import Homework
from app.models.notification import PendingAction
```

Add all 5 to the list: `ScreeningResult, ProtocolEnrollment, ProtocolSession, Homework, PendingAction`

In `backend/app/models/__init__.py`, add the same imports and export names.

- [ ] **Step 9: Update tests/conftest.py**

Add to ALL_MODELS list:

```python
from app.models.screening import ScreeningResult
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.homework import Homework
from app.models.notification import PendingAction
```

Add all 5 to ALL_MODELS.

- [ ] **Step 10: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_models/test_new_models.py -v
```

Expected: All tests pass.

- [ ] **Step 11: Commit**

```bash
git add backend/app/models/screening.py backend/app/models/protocol.py backend/app/models/homework.py backend/app/models/notification.py backend/app/models/user.py backend/app/models/base.py backend/app/models/__init__.py backend/tests/conftest.py backend/tests/test_models/
git commit -m "feat: add data models for screening, protocols, homework, notifications"
```

---

## Task 2: Screening Instruments + Severity Router

**Files:**
- Create: `backend/app/screening/__init__.py`
- Create: `backend/app/screening/instruments.py`
- Create: `backend/app/psychology/severity.py`
- Test: `backend/tests/test_screening/test_instruments.py`
- Test: `backend/tests/test_screening/test_severity.py`

- [ ] **Step 1: Write tests for instruments**

Create `backend/tests/test_screening/__init__.py` (empty) and `backend/tests/test_screening/test_instruments.py`:

```python
import pytest
from app.screening.instruments import (
    get_instrument,
    score_instrument,
    PHQ9,
    GAD7,
    PCL5,
)


class TestPHQ9:
    def test_has_9_items(self):
        assert len(PHQ9.items) == 9

    def test_score_minimal(self):
        result = score_instrument("phq9", [0, 0, 0, 0, 0, 0, 0, 0, 0])
        assert result["total_score"] == 0
        assert result["severity_tier"] == "minimal"

    def test_score_mild(self):
        result = score_instrument("phq9", [1, 1, 1, 1, 1, 0, 0, 0, 0])
        assert result["total_score"] == 5
        assert result["severity_tier"] == "mild"

    def test_score_moderate(self):
        result = score_instrument("phq9", [2, 1, 1, 1, 1, 1, 1, 1, 1])
        assert result["total_score"] == 10
        assert result["severity_tier"] == "moderate"

    def test_score_moderately_severe(self):
        result = score_instrument("phq9", [2, 2, 2, 2, 2, 2, 1, 1, 1])
        assert result["total_score"] == 15
        assert result["severity_tier"] == "moderately_severe"

    def test_score_severe(self):
        result = score_instrument("phq9", [3, 3, 3, 3, 3, 2, 2, 2, 2])
        assert result["total_score"] == 23
        assert result["severity_tier"] == "severe"

    def test_conversational_phrasing_exists(self):
        for item in PHQ9.items:
            assert item.conversational
            assert item.clinical


class TestGAD7:
    def test_has_7_items(self):
        assert len(GAD7.items) == 7

    def test_score_severe(self):
        result = score_instrument("gad7", [3, 3, 3, 3, 3, 2, 2])
        assert result["total_score"] == 19
        assert result["severity_tier"] == "severe"


class TestPCL5:
    def test_has_8_items(self):
        assert len(PCL5.items) == 8

    def test_positive_screen(self):
        result = score_instrument("pcl5", [2, 2, 2, 2, 2, 2, 2, 2])
        assert result["total_score"] == 16
        assert result["severity_tier"] == "severe"

    def test_negative_screen(self):
        result = score_instrument("pcl5", [1, 1, 1, 1, 1, 1, 1, 1])
        assert result["total_score"] == 8
        assert result["severity_tier"] == "mild"


class TestGetInstrument:
    def test_get_phq9(self):
        inst = get_instrument("phq9")
        assert inst is not None
        assert inst.name == "phq9"

    def test_get_unknown(self):
        assert get_instrument("unknown") is None
```

- [ ] **Step 2: Write tests for severity router**

Create `backend/tests/test_screening/test_severity.py`:

```python
import pytest
from app.psychology.severity import SeverityRouter


class TestSeverityRouter:
    def test_phq9_minimal(self):
        result = SeverityRouter.route("phq9", 3)
        assert result.tier == "minimal"
        assert result.action == "monitor"
        assert result.referral_required is False

    def test_phq9_mild(self):
        result = SeverityRouter.route("phq9", 7)
        assert result.tier == "mild"
        assert result.action == "offer_protocol"
        assert "cbt_depression" in result.eligible_protocols

    def test_phq9_moderate(self):
        result = SeverityRouter.route("phq9", 12)
        assert result.tier == "moderate"
        assert result.action == "recommend_protocol"

    def test_phq9_moderately_severe(self):
        result = SeverityRouter.route("phq9", 17)
        assert result.tier == "moderately_severe"
        assert result.action == "protocol_plus_referral"
        assert result.referral_required is True

    def test_phq9_severe(self):
        result = SeverityRouter.route("phq9", 22)
        assert result.tier == "severe"
        assert result.action == "referral_only"
        assert result.eligible_protocols == []

    def test_gad7_moderate(self):
        result = SeverityRouter.route("gad7", 12)
        assert result.tier == "moderate"
        assert "anxiety" in result.eligible_protocols

    def test_pcl5_positive(self):
        result = SeverityRouter.route("pcl5", 18)
        assert result.tier == "severe"
        assert result.action == "referral_only"
        assert result.eligible_protocols == []

    def test_pcl5_negative(self):
        result = SeverityRouter.route("pcl5", 10)
        assert result.tier == "mild"
        assert result.action == "monitor"  # No PTSD protocol in V1

    def test_ba_eligible_from_phq9(self):
        result = SeverityRouter.route("phq9", 8)
        assert "behavioral_activation" in result.eligible_protocols
```

- [ ] **Step 3: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_screening/ -v 2>&1 | head -20
```

- [ ] **Step 4: Implement instruments.py**

Create `backend/app/screening/__init__.py` (empty) and `backend/app/screening/instruments.py`:

```python
from dataclasses import dataclass


@dataclass
class InstrumentItem:
    index: int
    clinical: str
    conversational: str


@dataclass
class Instrument:
    name: str
    display_name: str
    items: list[InstrumentItem]
    thresholds: dict[str, tuple[int, int]]  # tier -> (min, max) inclusive
    response_options: list[dict]  # [{label, value}]


_LIKERT_4 = [
    {"label": "Not at all", "value": 0},
    {"label": "Several days", "value": 1},
    {"label": "More than half the days", "value": 2},
    {"label": "Nearly every day", "value": 3},
]


PHQ9 = Instrument(
    name="phq9",
    display_name="PHQ-9",
    items=[
        InstrumentItem(0,
            "Little interest or pleasure in doing things",
            "Over the past couple weeks, how often have you felt like things you usually enjoy just... didn't interest you?"),
        InstrumentItem(1,
            "Feeling down, depressed, or hopeless",
            "How often have you felt down, low, or like things wouldn't get better?"),
        InstrumentItem(2,
            "Trouble falling or staying asleep, or sleeping too much",
            "How has your sleep been? Too much, too little, or just restless?"),
        InstrumentItem(3,
            "Feeling tired or having little energy",
            "How often have you felt drained — like you just didn't have the energy for things?"),
        InstrumentItem(4,
            "Poor appetite or overeating",
            "How about your appetite — eating more than usual, or less, or no change?"),
        InstrumentItem(5,
            "Feeling bad about yourself — or that you are a failure",
            "How often have you been hard on yourself — feeling like you're not enough, or that you've let people down?"),
        InstrumentItem(6,
            "Trouble concentrating on things",
            "Have you noticed trouble focusing — reading, watching something, or staying on task?"),
        InstrumentItem(7,
            "Moving or speaking so slowly that others could notice, or being fidgety/restless",
            "Have people around you noticed you being slower than usual, or more restless?"),
        InstrumentItem(8,
            "Thoughts that you would be better off dead, or of hurting yourself",
            "This one is important and I want to ask it with care. Have you had thoughts that you'd be better off not being here, or of hurting yourself?"),
    ],
    thresholds={
        "minimal": (0, 4),
        "mild": (5, 9),
        "moderate": (10, 14),
        "moderately_severe": (15, 19),
        "severe": (20, 27),
    },
    response_options=_LIKERT_4,
)


GAD7 = Instrument(
    name="gad7",
    display_name="GAD-7",
    items=[
        InstrumentItem(0,
            "Feeling nervous, anxious, or on edge",
            "Over the past two weeks, how often have you felt nervous, anxious, or like you couldn't settle?"),
        InstrumentItem(1,
            "Not being able to stop or control worrying",
            "How often have you found yourself worrying and not being able to stop — even when you tried?"),
        InstrumentItem(2,
            "Worrying too much about different things",
            "How often have you worried about a lot of different things at once?"),
        InstrumentItem(3,
            "Trouble relaxing",
            "How often have you had trouble actually relaxing — like your mind or body just wouldn't let you?"),
        InstrumentItem(4,
            "Being so restless that it's hard to sit still",
            "How often have you felt so restless that sitting still felt impossible?"),
        InstrumentItem(5,
            "Becoming easily annoyed or irritable",
            "How often have you felt more irritable or snappy than usual?"),
        InstrumentItem(6,
            "Feeling afraid, as if something awful might happen",
            "How often have you felt a sense of dread — like something bad was about to happen?"),
    ],
    thresholds={
        "minimal": (0, 4),
        "mild": (5, 9),
        "moderate": (10, 14),
        "moderately_severe": (15, 18),
        "severe": (19, 21),
    },
    response_options=_LIKERT_4,
)


PCL5 = Instrument(
    name="pcl5",
    display_name="PCL-5 (Brief)",
    items=[
        InstrumentItem(0,
            "Repeated, disturbing, and unwanted memories of a stressful experience",
            "In the past month, how often have unwanted memories of something stressful popped into your head — even when you didn't want them to?"),
        InstrumentItem(1,
            "Repeated, disturbing dreams of a stressful experience",
            "How often have you had bad dreams or nightmares about something stressful that happened?"),
        InstrumentItem(2,
            "Avoiding memories, thoughts, or feelings related to a stressful experience",
            "How often have you tried to avoid thinking about or feeling things related to a stressful experience?"),
        InstrumentItem(3,
            "Avoiding external reminders of a stressful experience",
            "How often have you avoided people, places, or situations that reminded you of something stressful?"),
        InstrumentItem(4,
            "Having strong negative beliefs about yourself, others, or the world",
            "How often have you had strong negative thoughts like 'I can't trust anyone' or 'The world is dangerous'?"),
        InstrumentItem(5,
            "Feeling jumpy or easily startled",
            "How often have you felt jumpy or easily startled — like by a sudden noise?"),
        InstrumentItem(6,
            "Having difficulty concentrating",
            "How often have you had trouble concentrating or keeping your mind on things?"),
        InstrumentItem(7,
            "Trouble falling or staying asleep",
            "How has your sleep been — trouble falling asleep, or waking up during the night?"),
    ],
    thresholds={
        "minimal": (0, 7),
        "mild": (8, 15),
        "severe": (16, 32),  # Positive screen — no moderate tier for PCL-5 brief
    },
    response_options=[
        {"label": "Not at all", "value": 0},
        {"label": "A little bit", "value": 1},
        {"label": "Moderately", "value": 2},
        {"label": "Quite a bit", "value": 3},
        {"label": "Extremely", "value": 4},
    ],
)


_INSTRUMENTS: dict[str, Instrument] = {
    "phq9": PHQ9,
    "gad7": GAD7,
    "pcl5": PCL5,
}


def get_instrument(name: str) -> Instrument | None:
    return _INSTRUMENTS.get(name)


def score_instrument(name: str, item_scores: list[int]) -> dict:
    instrument = _INSTRUMENTS[name]
    total = sum(item_scores)
    tier = "minimal"
    for tier_name, (low, high) in instrument.thresholds.items():
        if low <= total <= high:
            tier = tier_name
            break
    return {
        "total_score": total,
        "severity_tier": tier,
    }
```

- [ ] **Step 5: Implement severity.py**

Create `backend/app/psychology/severity.py`:

```python
from dataclasses import dataclass, field


@dataclass
class RoutingDecision:
    tier: str
    action: str  # monitor | offer_protocol | recommend_protocol | protocol_plus_referral | referral_only
    eligible_protocols: list[str] = field(default_factory=list)
    referral_required: bool = False
    message: str = ""


# Therapist referral resources (V1 — static list)
REFERRAL_RESOURCES = (
    "Here are some resources that can help:\n"
    "- **988 Suicide & Crisis Lifeline** — call or text 988\n"
    "- **Crisis Text Line** — text HOME to 741741\n"
    "- **Psychology Today** — psychologytoday.com/us/therapists (find a therapist)\n"
    "- **Open Path Collective** — openpathcollective.org (affordable therapy)\n"
    "- **SAMHSA Helpline** — 1-800-662-4357 (free referrals)"
)


class SeverityRouter:
    @staticmethod
    def route(instrument: str, total_score: int) -> RoutingDecision:
        if instrument == "pcl5":
            return SeverityRouter._route_pcl5(total_score)
        elif instrument == "phq9":
            return SeverityRouter._route_phq9(total_score)
        elif instrument == "gad7":
            return SeverityRouter._route_gad7(total_score)
        return RoutingDecision(tier="minimal", action="monitor")

    @staticmethod
    def _route_phq9(score: int) -> RoutingDecision:
        protocols = ["cbt_depression", "behavioral_activation"]
        if score <= 4:
            return RoutingDecision(
                tier="minimal", action="monitor",
                message="Things look stable. I'm here if anything comes up.",
            )
        elif score <= 9:
            return RoutingDecision(
                tier="mild", action="offer_protocol",
                eligible_protocols=protocols,
                message="I noticed some things we could work on together. Want me to walk you through a program that might help?",
            )
        elif score <= 14:
            return RoutingDecision(
                tier="moderate", action="recommend_protocol",
                eligible_protocols=protocols,
                message="Based on what you've shared, I think a structured program would really help. I'd recommend we start working together on this. What do you think?",
            )
        elif score <= 19:
            return RoutingDecision(
                tier="moderately_severe", action="protocol_plus_referral",
                eligible_protocols=protocols,
                referral_required=True,
                message=(
                    "I want to be honest — what you're experiencing is significant. "
                    "I can work with you on this, and I'd also recommend connecting with a therapist. "
                    "Want me to help you think about finding one?\n\n" + REFERRAL_RESOURCES
                ),
            )
        else:
            return RoutingDecision(
                tier="severe", action="referral_only",
                referral_required=True,
                message=(
                    "What you're going through deserves more support than I can provide on my own. "
                    "I really want to help you find a therapist who can work with you directly. "
                    "I'll keep being here for you in the meantime.\n\n" + REFERRAL_RESOURCES
                ),
            )

    @staticmethod
    def _route_gad7(score: int) -> RoutingDecision:
        protocols = ["anxiety"]
        if score <= 4:
            return RoutingDecision(
                tier="minimal", action="monitor",
                message="Things look stable. I'm here if anything comes up.",
            )
        elif score <= 9:
            return RoutingDecision(
                tier="mild", action="offer_protocol",
                eligible_protocols=protocols,
                message="I noticed some patterns around worry and anxiety. I have a structured program that could help — interested?",
            )
        elif score <= 14:
            return RoutingDecision(
                tier="moderate", action="recommend_protocol",
                eligible_protocols=protocols,
                message="Based on what you've shared, I'd recommend we work through an anxiety management program together. What do you think?",
            )
        elif score <= 18:
            return RoutingDecision(
                tier="moderately_severe", action="protocol_plus_referral",
                eligible_protocols=protocols,
                referral_required=True,
                message=(
                    "I want to be honest — the anxiety you're experiencing is significant. "
                    "I can work with you on this, and I'd also recommend talking to a professional. "
                    "Want me to help you think about that?\n\n" + REFERRAL_RESOURCES
                ),
            )
        else:
            return RoutingDecision(
                tier="severe", action="referral_only",
                referral_required=True,
                message=(
                    "What you're going through with anxiety deserves more support than I can offer alone. "
                    "Let me help you find a therapist.\n\n" + REFERRAL_RESOURCES
                ),
            )

    @staticmethod
    def _route_pcl5(score: int) -> RoutingDecision:
        if score <= 7:
            return RoutingDecision(tier="minimal", action="monitor")
        elif score <= 15:
            return RoutingDecision(
                tier="mild", action="monitor",  # No PTSD protocol in V1
                message="Thanks for sharing that with me. I'll keep it in mind as we talk.",
            )
        else:
            return RoutingDecision(
                tier="severe", action="referral_only",
                referral_required=True,
                message=(
                    "What you've shared tells me you might benefit from working with someone "
                    "who specializes in trauma. That kind of support can make a real difference. "
                    "I'm still here for you day to day.\n\n" + REFERRAL_RESOURCES
                ),
            )
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_screening/ -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/screening/ backend/app/psychology/severity.py backend/tests/test_screening/
git commit -m "feat: add screening instruments (PHQ-9, GAD-7, PCL-5) and severity router"
```

---

## Task 3: Protocol Definitions

**Files:**
- Create: `backend/app/protocols/__init__.py`
- Create: `backend/app/protocols/base.py`
- Create: `backend/app/protocols/cbt_depression.py`
- Create: `backend/app/protocols/anxiety.py`
- Create: `backend/app/protocols/behavioral_activation.py`
- Create: `backend/app/protocols/registry.py`
- Test: `backend/tests/test_protocols/test_base.py`
- Test: `backend/tests/test_protocols/test_cbt.py`
- Test: `backend/tests/test_protocols/test_registry.py`

- [ ] **Step 1: Write tests for protocol base and registry**

Create `backend/tests/test_protocols/__init__.py` (empty) and `backend/tests/test_protocols/test_base.py`:

```python
import pytest
from app.protocols.base import BaseProtocol, SessionDefinition, HomeworkTier


class TestSessionDefinition:
    def test_has_all_homework_tiers(self):
        sd = SessionDefinition(
            number=1,
            focus="Psychoeducation",
            goals=["Understand depression model"],
            homework=HomeworkTier(
                structured="Mood monitoring for 3 days",
                gentle="Notice your mood once a day",
                minimal="Just notice if your mood changes",
            ),
        )
        assert sd.homework.structured
        assert sd.homework.gentle
        assert sd.homework.minimal
```

Create `backend/tests/test_protocols/test_cbt.py`:

```python
import pytest
from app.protocols.cbt_depression import CBTDepressionProtocol


class TestCBTDepression:
    def test_has_8_sessions(self):
        proto = CBTDepressionProtocol()
        assert len(proto.sessions) == 8

    def test_entry_criteria(self):
        proto = CBTDepressionProtocol()
        assert proto.instrument == "phq9"
        assert proto.min_score == 5
        assert proto.max_score == 19

    def test_all_sessions_have_homework(self):
        proto = CBTDepressionProtocol()
        for session in proto.sessions:
            assert session.homework.structured
            assert session.homework.gentle
            assert session.homework.minimal

    def test_session_numbers_sequential(self):
        proto = CBTDepressionProtocol()
        for i, session in enumerate(proto.sessions):
            assert session.number == i + 1

    def test_mid_protocol_screening_at_session_4(self):
        proto = CBTDepressionProtocol()
        assert proto.mid_screening_session == 4

    def test_is_eligible_for_score(self):
        proto = CBTDepressionProtocol()
        assert proto.is_eligible(score=12, instrument="phq9")
        assert not proto.is_eligible(score=22, instrument="phq9")
        assert not proto.is_eligible(score=3, instrument="phq9")
        assert not proto.is_eligible(score=12, instrument="gad7")
```

Create `backend/tests/test_protocols/test_registry.py`:

```python
import pytest
from app.protocols.registry import get_protocol, get_eligible_protocols


class TestRegistry:
    def test_get_cbt(self):
        proto = get_protocol("cbt_depression")
        assert proto is not None
        assert proto.protocol_id == "cbt_depression"

    def test_get_anxiety(self):
        proto = get_protocol("anxiety")
        assert proto is not None

    def test_get_ba(self):
        proto = get_protocol("behavioral_activation")
        assert proto is not None

    def test_get_unknown(self):
        assert get_protocol("unknown") is None

    def test_eligible_for_phq9_moderate(self):
        protocols = get_eligible_protocols("phq9", 12)
        ids = [p.protocol_id for p in protocols]
        assert "cbt_depression" in ids
        assert "behavioral_activation" in ids

    def test_eligible_for_gad7_moderate(self):
        protocols = get_eligible_protocols("gad7", 12)
        ids = [p.protocol_id for p in protocols]
        assert "anxiety" in ids
        assert "cbt_depression" not in ids

    def test_not_eligible_for_severe(self):
        protocols = get_eligible_protocols("phq9", 25)
        assert len(protocols) == 0
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_protocols/ -v 2>&1 | head -20
```

- [ ] **Step 3: Implement base.py**

Create `backend/app/protocols/__init__.py` (empty) and `backend/app/protocols/base.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class HomeworkTier:
    structured: str
    gentle: str
    minimal: str


@dataclass
class SessionDefinition:
    number: int
    focus: str
    goals: list[str] = field(default_factory=list)
    homework: HomeworkTier = field(default_factory=lambda: HomeworkTier("", "", ""))
    uses_existing_flow: str | None = None  # e.g., "reframe", "values"


class BaseProtocol(ABC):
    protocol_id: str
    display_name: str
    instrument: str  # Which screening instrument triggers this
    min_score: int
    max_score: int
    mid_screening_session: int  # Which session to re-screen at

    @property
    @abstractmethod
    def sessions(self) -> list[SessionDefinition]:
        ...

    @property
    def total_sessions(self) -> int:
        return len(self.sessions)

    def get_session(self, number: int) -> SessionDefinition | None:
        for s in self.sessions:
            if s.number == number:
                return s
        return None

    def is_eligible(self, score: int, instrument: str) -> bool:
        return instrument == self.instrument and self.min_score <= score <= self.max_score

    def get_homework(self, session_number: int, tier: str = "structured") -> str:
        session = self.get_session(session_number)
        if not session:
            return ""
        return getattr(session.homework, tier, session.homework.structured)
```

- [ ] **Step 4: Implement cbt_depression.py**

Create `backend/app/protocols/cbt_depression.py`:

```python
from app.protocols.base import BaseProtocol, SessionDefinition, HomeworkTier


class CBTDepressionProtocol(BaseProtocol):
    protocol_id = "cbt_depression"
    display_name = "CBT for Depression"
    instrument = "phq9"
    min_score = 5
    max_score = 19
    mid_screening_session = 4

    @property
    def sessions(self) -> list[SessionDefinition]:
        return [
            SessionDefinition(
                number=1,
                focus="Psychoeducation — depression model, thoughts-feelings-behaviors connection",
                goals=["Understand how depression works", "Learn the CBT triangle"],
                homework=HomeworkTier(
                    structured="Mood monitoring for 3 days",
                    gentle="Notice your mood once a day, no logging needed",
                    minimal="Just notice if your mood changes at all today",
                ),
            ),
            SessionDefinition(
                number=2,
                focus="Behavioral activation intro — identify dropped activities, use energy ladder",
                goals=["Identify activities you've stopped doing", "Match activities to energy level"],
                homework=HomeworkTier(
                    structured="Do 1 pleasurable activity",
                    gentle="Think of one thing you used to enjoy",
                    minimal="Notice one moment of pleasure this week",
                ),
            ),
            SessionDefinition(
                number=3,
                focus="Activity scheduling — concrete weekly plan using existing habit/activity system",
                goals=["Create a realistic activity schedule", "Link activities to mood tracking"],
                homework=HomeworkTier(
                    structured="Follow schedule for 3 days, log mood before/after",
                    gentle="Try one scheduled activity this week",
                    minimal="When you have a free moment, do something small you enjoy",
                ),
            ),
            SessionDefinition(
                number=4,
                focus="Thought catching — automatic thought recognition",
                goals=["Learn to notice automatic thoughts", "Practice thought records"],
                uses_existing_flow="reframe",
                homework=HomeworkTier(
                    structured="Catch 3 automatic thoughts using thought record",
                    gentle="Notice one negative thought this week",
                    minimal="When you feel bad, pause and ask 'what was I just thinking?'",
                ),
            ),
            SessionDefinition(
                number=5,
                focus="Cognitive restructuring — identify distortions, practice reframes",
                goals=["Identify cognitive distortions in your thoughts", "Practice generating alternative thoughts"],
                homework=HomeworkTier(
                    structured="Reframe 2 thoughts independently",
                    gentle="Try questioning one negative thought",
                    minimal="Notice if a thought is a fact or an interpretation",
                ),
            ),
            SessionDefinition(
                number=6,
                focus="Core beliefs — connect patterns across automatic thoughts",
                goals=["Identify underlying core beliefs", "See patterns in automatic thoughts"],
                homework=HomeworkTier(
                    structured="Notice when a core belief gets activated",
                    gentle="Reflect on what theme connects your negative thoughts",
                    minimal="No homework — just sit with what we discussed",
                ),
            ),
            SessionDefinition(
                number=7,
                focus="Behavioral experiments — design experiments to test beliefs",
                goals=["Design a small experiment to test a belief", "Learn from the result"],
                homework=HomeworkTier(
                    structured="Run one experiment",
                    gentle="Think of one small way to test a belief",
                    minimal="Notice one moment where reality didn't match your fear",
                ),
            ),
            SessionDefinition(
                number=8,
                focus="Relapse prevention — review progress, identify warning signs, build coping plan",
                goals=["Review PHQ-9 progress", "Build a personal coping plan", "Identify early warning signs"],
                homework=HomeworkTier(
                    structured="Exit screening",
                    gentle="Exit screening",
                    minimal="Exit screening",
                ),
            ),
        ]
```

- [ ] **Step 5: Implement anxiety.py and behavioral_activation.py**

Create `backend/app/protocols/anxiety.py` with 7 sessions following the spec table for Anxiety Management.

Create `backend/app/protocols/behavioral_activation.py` with 6 sessions following the spec table for Behavioral Activation. Include `skip_sessions_on_switch: list[int] = [1, 2]` attribute for CBT-to-BA switching.

- [ ] **Step 6: Implement registry.py**

Create `backend/app/protocols/registry.py`:

```python
from app.protocols.base import BaseProtocol
from app.protocols.cbt_depression import CBTDepressionProtocol
from app.protocols.anxiety import AnxietyProtocol
from app.protocols.behavioral_activation import BehavioralActivationProtocol


_PROTOCOLS: dict[str, BaseProtocol] = {
    "cbt_depression": CBTDepressionProtocol(),
    "anxiety": AnxietyProtocol(),
    "behavioral_activation": BehavioralActivationProtocol(),
}


def get_protocol(protocol_id: str) -> BaseProtocol | None:
    return _PROTOCOLS.get(protocol_id)


def get_eligible_protocols(instrument: str, score: int) -> list[BaseProtocol]:
    return [p for p in _PROTOCOLS.values() if p.is_eligible(score, instrument)]
```

- [ ] **Step 7: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_protocols/ -v
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/protocols/ backend/tests/test_protocols/
git commit -m "feat: add protocol definitions (CBT, anxiety, behavioral activation) with registry"
```

---

## Task 4: Screening Flow (Conversational Delivery)

**Files:**
- Create: `backend/app/screening/delivery.py`
- Test: `backend/tests/test_screening/test_delivery.py`

- [ ] **Step 1: Write tests for ScreeningFlow**

Create `backend/tests/test_screening/test_delivery.py`:

```python
import pytest
from app.screening.delivery import ScreeningFlow
from app.chat.flows.base import UserContext


@pytest.fixture
def context():
    return UserContext(user_id="test-user", user_name="Test")


class TestScreeningFlow:
    @pytest.mark.asyncio
    async def test_phq9_starts_with_intro(self):
        flow = ScreeningFlow(instrument_name="phq9")
        result = await flow.start(context())
        assert "specific questions" in result.response_message.lower() or "check in" in result.response_message.lower()
        assert result.prompt is not None
        assert result.prompt.input_type == "choice"

    @pytest.mark.asyncio
    async def test_phq9_full_completion(self):
        flow = ScreeningFlow(instrument_name="phq9")
        ctx = context()
        await flow.start(ctx)

        # Answer all 9 questions with score 1 each
        for i in range(9):
            result = await flow.process("Several days", ctx)

        assert flow.is_complete
        assert flow.collected_data["total_score"] == 9
        assert flow.collected_data["severity_tier"] == "mild"

    @pytest.mark.asyncio
    async def test_gad7_full_completion(self):
        flow = ScreeningFlow(instrument_name="gad7")
        ctx = context()
        await flow.start(ctx)

        for i in range(7):
            result = await flow.process("Not at all", ctx)

        assert flow.is_complete
        assert flow.collected_data["total_score"] == 0

    @pytest.mark.asyncio
    async def test_score_mapping(self):
        flow = ScreeningFlow(instrument_name="phq9")
        ctx = context()
        await flow.start(ctx)

        result = await flow.process("Nearly every day", ctx)
        assert flow.collected_data.get("item_scores", [None])[-1] == 3

    @pytest.mark.asyncio
    async def test_get_steps_returns_item_steps(self):
        flow = ScreeningFlow(instrument_name="phq9")
        steps = flow.get_steps()
        assert len(steps) == 9  # One step per PHQ-9 item
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_screening/test_delivery.py -v 2>&1 | head -20
```

- [ ] **Step 3: Implement ScreeningFlow**

Create `backend/app/screening/delivery.py`:

```python
from typing import Any, Optional

from app.chat.flows.base import BaseFlow, FlowResult, FlowPrompt, UserContext
from app.screening.instruments import get_instrument, Instrument


class ScreeningFlow(BaseFlow):
    """Delivers a screening instrument conversationally."""

    def __init__(self, instrument_name: str):
        super().__init__()
        self.flow_id = f"screening_{instrument_name}"
        self.display_name = "Screening"
        self.instrument: Instrument = get_instrument(instrument_name)
        if not self.instrument:
            raise ValueError(f"Unknown instrument: {instrument_name}")
        self.collected_data["instrument"] = instrument_name
        self.collected_data["item_scores"] = []

    def get_steps(self) -> list[str]:
        return [f"item_{i}" for i in range(len(self.instrument.items))]

    async def get_initial_prompt(self, context: UserContext) -> FlowResult:
        item = self.instrument.items[0]
        options = [opt["label"] for opt in self.instrument.response_options]
        return FlowResult(
            next_step="item_0",
            response_message=(
                f"I'd like to check in on something more specific, {context.user_name}. "
                "I'm going to ask you a few questions — just answer honestly, there's no wrong answer."
            ),
            prompt=FlowPrompt(
                prompt=item.conversational,
                input_type="choice",
                options=options,
            ),
        )

    async def handle_input(
        self, step: str, value: Any, context: UserContext
    ) -> FlowResult:
        # Parse current item index
        item_idx = int(step.split("_")[1])

        # Map response to score
        score = self._parse_response(value)
        self.collected_data["item_scores"].append(score)

        next_idx = item_idx + 1

        # Check if we've completed all items
        if next_idx >= len(self.instrument.items):
            # Score and finalize
            total = sum(self.collected_data["item_scores"])
            self.collected_data["total_score"] = total

            # Determine severity tier
            tier = "minimal"
            for tier_name, (low, high) in self.instrument.thresholds.items():
                if low <= total <= high:
                    tier = tier_name
                    break
            self.collected_data["severity_tier"] = tier
            return FlowResult(next_step=None)

        # Next question
        next_item = self.instrument.items[next_idx]
        options = [opt["label"] for opt in self.instrument.response_options]

        # Warm transition between questions
        transition = self._get_transition(item_idx)

        return FlowResult(
            next_step=f"item_{next_idx}",
            response_message=transition,
            prompt=FlowPrompt(
                prompt=next_item.conversational,
                input_type="choice",
                options=options,
            ),
        )

    async def on_complete(self, context: UserContext) -> str:
        total = self.collected_data["total_score"]
        tier = self.collected_data["severity_tier"]
        instrument = self.collected_data["instrument"]
        n_items = len(self.instrument.items)
        return (
            f"Thank you for answering those {n_items} questions, {context.user_name}. "
            "That takes courage, and it helps me understand what you're going through."
        )

    def _parse_response(self, value: Any) -> int:
        value_str = str(value).strip().lower()
        for opt in self.instrument.response_options:
            if opt["label"].lower() == value_str:
                return opt["value"]
        # Try parsing as int directly
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _get_transition(self, current_idx: int) -> str:
        transitions = [
            "Got it.",
            "Thank you.",
            "Noted.",
            "I appreciate you sharing that.",
            "Okay.",
            "Thank you for being honest about that.",
            "Got it, thank you.",
            "Okay, just a couple more.",
            "Almost done.",
        ]
        return transitions[current_idx % len(transitions)]
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_screening/test_delivery.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/screening/delivery.py backend/tests/test_screening/test_delivery.py
git commit -m "feat: add conversational screening flow delivery"
```

---

## Task 5: Adaptive Homework System

**Files:**
- Create: `backend/app/sessions/__init__.py`
- Create: `backend/app/sessions/homework.py`
- Test: `backend/tests/test_sessions/__init__.py`
- Test: `backend/tests/test_sessions/test_homework.py`

- [ ] **Step 1: Write tests for homework logic**

Create `backend/tests/test_sessions/__init__.py` (empty) and `backend/tests/test_sessions/test_homework.py`:

```python
import pytest
from app.sessions.homework import HomeworkManager
from app.protocols.cbt_depression import CBTDepressionProtocol
from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment


@pytest.fixture
def protocol():
    return CBTDepressionProtocol()


class TestHomeworkManager:
    @pytest.mark.asyncio
    async def test_assign_structured_by_default(self, protocol):
        enrollment = ProtocolEnrollment(
            user_id="user-1",
            protocol_id="cbt_depression",
            current_session_number=1,
            status="active",
            consecutive_homework_misses=0,
        )
        await enrollment.insert()

        hw = await HomeworkManager.assign(enrollment, protocol, session_number=1)
        assert hw.adaptive_tier == "structured"
        assert "3 days" in hw.description

    @pytest.mark.asyncio
    async def test_assign_gentle_after_1_miss(self, protocol):
        enrollment = ProtocolEnrollment(
            user_id="user-1",
            protocol_id="cbt_depression",
            current_session_number=2,
            status="active",
            consecutive_homework_misses=1,
        )
        await enrollment.insert()

        hw = await HomeworkManager.assign(enrollment, protocol, session_number=2)
        assert hw.adaptive_tier == "gentle"

    @pytest.mark.asyncio
    async def test_assign_minimal_after_2_misses(self, protocol):
        enrollment = ProtocolEnrollment(
            user_id="user-1",
            protocol_id="cbt_depression",
            current_session_number=3,
            status="active",
            consecutive_homework_misses=2,
        )
        await enrollment.insert()

        hw = await HomeworkManager.assign(enrollment, protocol, session_number=3)
        assert hw.adaptive_tier == "minimal"

    def test_determine_tier_structured(self):
        assert HomeworkManager.determine_tier(0) == "structured"

    def test_determine_tier_gentle(self):
        assert HomeworkManager.determine_tier(1) == "gentle"

    def test_determine_tier_minimal(self):
        assert HomeworkManager.determine_tier(2) == "minimal"

    def test_should_pause_at_3_misses(self):
        assert HomeworkManager.should_pause(3) is True
        assert HomeworkManager.should_pause(2) is False
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_sessions/test_homework.py -v 2>&1 | head -20
```

- [ ] **Step 3: Implement HomeworkManager**

Create `backend/app/sessions/__init__.py` (empty) and `backend/app/sessions/homework.py`:

```python
from datetime import datetime, timezone, timedelta

from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment
from app.protocols.base import BaseProtocol


class HomeworkManager:
    @staticmethod
    def determine_tier(consecutive_misses: int) -> str:
        if consecutive_misses == 0:
            return "structured"
        elif consecutive_misses == 1:
            return "gentle"
        else:
            return "minimal"

    @staticmethod
    def should_pause(consecutive_misses: int) -> bool:
        return consecutive_misses >= 3

    @staticmethod
    async def assign(
        enrollment: ProtocolEnrollment,
        protocol: BaseProtocol,
        session_number: int,
    ) -> Homework:
        tier = HomeworkManager.determine_tier(enrollment.consecutive_homework_misses)
        description = protocol.get_homework(session_number, tier)

        hw = Homework(
            user_id=enrollment.user_id,
            enrollment_id=str(enrollment.id),
            session_number=session_number,
            description=description,
            adaptive_tier=tier,
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
        )
        await hw.insert()
        return hw

    @staticmethod
    async def complete(homework: Homework, user_response: str) -> Homework:
        homework.status = "completed"
        homework.user_response = user_response
        homework.completed_at = datetime.now(timezone.utc)
        await homework.save()
        return homework

    @staticmethod
    async def skip(homework: Homework, enrollment: ProtocolEnrollment) -> bool:
        """Mark homework as skipped. Returns True if protocol should pause."""
        homework.status = "skipped"
        await homework.save()

        enrollment.consecutive_homework_misses += 1
        await enrollment.save()

        return HomeworkManager.should_pause(enrollment.consecutive_homework_misses)

    @staticmethod
    async def get_pending(user_id: str) -> Homework | None:
        return await Homework.find_one(
            Homework.user_id == user_id,
            Homework.status.is_in(["assigned", "reminded"]),
        )
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_sessions/test_homework.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/sessions/ backend/tests/test_sessions/
git commit -m "feat: add adaptive homework system with tiered assignments"
```

---

## Task 6: SessionEngine

**Files:**
- Create: `backend/app/sessions/engine.py`
- Test: `backend/tests/test_sessions/test_engine.py`

- [ ] **Step 1: Write tests for SessionEngine**

Create `backend/tests/test_sessions/test_engine.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta

from app.sessions.engine import SessionEngine
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.homework import Homework
from app.models.notification import PendingAction
from app.models.screening import ScreeningResult
from app.models.user import User
from app.models.conversation import Conversation
from app.chat.flows.base import UserContext


@pytest.fixture
def context():
    return UserContext(user_id="test-user", user_name="Test")


class TestSessionEngineNoActiveProtocol:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_protocol(self, test_user, context):
        engine = SessionEngine(test_user)
        result = await engine.try_handle("hello", context)
        assert result is None


class TestSessionEngineSessionStart:
    @pytest.mark.asyncio
    async def test_session_start_with_pending_homework(self, test_user, context):
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=2,
            status="active",
        )
        await enrollment.insert()
        hw = Homework(
            user_id=str(test_user.id),
            enrollment_id=str(enrollment.id),
            session_number=1,
            description="Mood monitoring",
            adaptive_tier="structured",
            status="assigned",
        )
        await hw.insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(context)
        assert result is not None
        assert "homework" in result["content"].lower() or "mood" in result["content"].lower()

    @pytest.mark.asyncio
    async def test_session_start_with_pending_screening(self, test_user, context):
        pa = PendingAction(
            user_id=str(test_user.id),
            action_type="screening_due",
            priority=3,
            data={"instrument": "phq9"},
        )
        await pa.insert()

        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_session_start_nothing_pending(self, test_user, context):
        engine = SessionEngine(test_user)
        result = await engine.handle_session_start(context)
        assert result is None


class TestSessionEngineEnrollment:
    @pytest.mark.asyncio
    async def test_cannot_enroll_with_active_program(self, test_user):
        from app.models.program import ProgramEnrollment
        pe = ProgramEnrollment(
            user_id=str(test_user.id),
            program_id="belief_reset",
            is_active=True,
            current_day=3,
            days_completed=[1, 2],
        )
        await pe.insert()

        engine = SessionEngine(test_user)
        result = await engine.enroll(
            protocol_id="cbt_depression",
            screening_id="screen-1",
        )
        assert result is None  # Blocked by active program
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_sessions/test_engine.py -v 2>&1 | head -20
```

- [ ] **Step 3: Implement SessionEngine**

Create `backend/app/sessions/engine.py`:

```python
from datetime import datetime, timezone
from typing import Optional

from app.chat.flows.base import UserContext
from app.models.homework import Homework
from app.models.notification import PendingAction
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.screening import ScreeningResult
from app.models.user import User
from app.protocols.registry import get_protocol
from app.sessions.homework import HomeworkManager
from app.screening.delivery import ScreeningFlow


class SessionEngine:
    def __init__(self, user: User):
        self.user = user
        self.user_id = str(user.id)
        self._active_screening_flow: Optional[ScreeningFlow] = None

    async def try_handle(
        self, content: str, context: UserContext
    ) -> Optional[dict]:
        """
        Try to handle the message within a protocol context.
        Returns a response dict if handled, None to fall through.
        """
        # Check for active screening flow
        if self._active_screening_flow and not self._active_screening_flow.is_complete:
            result = await self._active_screening_flow.process(content, context)
            if self._active_screening_flow.is_complete:
                return await self._on_screening_complete(context)
            return self._flow_result_to_response(result)

        # Check for active protocol with pending session
        enrollment = await self._get_active_enrollment()
        if not enrollment:
            return None

        protocol = get_protocol(enrollment.protocol_id)
        if not protocol:
            return None

        # If session is active, the LLM handles the therapeutic content
        # SessionEngine handles state transitions, not session content
        return None

    async def handle_session_start(self, context: UserContext) -> Optional[dict]:
        """Handle proactive greeting on app open. Returns None if nothing pending."""
        # Priority 1: Pending homework review
        pending_hw = await HomeworkManager.get_pending(self.user_id)
        if pending_hw:
            return self._make_response(
                f"Welcome back, {context.user_name}. "
                f"Last time I asked you to try: \"{pending_hw.description}\"\n\n"
                "How did that go? (Tell me about it, or say 'skip' if you didn't get to it)"
            )

        # Priority 2: Next session ready
        enrollment = await self._get_active_enrollment()
        if enrollment:
            protocol = get_protocol(enrollment.protocol_id)
            if protocol:
                session_def = protocol.get_session(enrollment.current_session_number)
                if session_def:
                    return self._make_response(
                        f"Ready for session {session_def.number}, {context.user_name}? "
                        f"Today we're working on: {session_def.focus}"
                    )

        # Priority 3: Screening due
        pending_action = await PendingAction.find_one(
            PendingAction.user_id == self.user_id,
            PendingAction.dismissed == False,
            PendingAction.action_type == "screening_due",
        )
        if pending_action:
            instrument = pending_action.data.get("instrument", "phq9")
            self._active_screening_flow = ScreeningFlow(instrument_name=instrument)
            result = await self._active_screening_flow.start(context)
            pending_action.dismissed = True
            await pending_action.save()
            return self._flow_result_to_response(result)

        return None

    async def enroll(
        self, protocol_id: str, screening_id: str
    ) -> Optional[ProtocolEnrollment]:
        """Enroll user in a protocol. Returns None if blocked."""
        # Check for active program (mutual exclusion)
        from app.models.program import ProgramEnrollment
        active_program = await ProgramEnrollment.find_one(
            ProgramEnrollment.user_id == self.user_id,
            ProgramEnrollment.is_active == True,
        )
        if active_program:
            return None

        # Check for active protocol
        active = await self._get_active_enrollment()
        if active:
            return None

        protocol = get_protocol(protocol_id)
        if not protocol:
            return None

        enrollment = ProtocolEnrollment(
            user_id=self.user_id,
            protocol_id=protocol_id,
            current_session_number=1,
            status="enrolled",
            entry_screening_id=screening_id,
        )
        await enrollment.insert()
        return enrollment

    async def _get_active_enrollment(self) -> Optional[ProtocolEnrollment]:
        return await ProtocolEnrollment.find_one(
            ProtocolEnrollment.user_id == self.user_id,
            ProtocolEnrollment.status.is_in(["enrolled", "active", "paused"]),
        )

    async def _on_screening_complete(self, context: UserContext) -> dict:
        """Handle completed screening — route through severity router."""
        from app.psychology.severity import SeverityRouter

        data = self._active_screening_flow.collected_data
        instrument = data["instrument"]
        total_score = data["total_score"]
        severity_tier = data["severity_tier"]

        # Save screening result
        sr = ScreeningResult(
            user_id=self.user_id,
            instrument=instrument,
            item_scores=data["item_scores"],
            total_score=total_score,
            severity_tier=severity_tier,
            status="completed",
            current_item=len(data["item_scores"]),
            completed_at=datetime.now(timezone.utc),
        )
        await sr.insert()

        # Route
        decision = SeverityRouter.route(instrument, total_score)
        self._active_screening_flow = None

        summary = (
            f"Thank you for answering those questions, {context.user_name}. "
            "That takes courage.\n\n"
        )
        return self._make_response(summary + decision.message)

    def _make_response(self, content: str) -> dict:
        return {
            "type": "message",
            "content": content,
            "sender": "mirror",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        }

    def _flow_result_to_response(self, result) -> dict:
        response = self._make_response(result.response_message or "")
        if result.prompt:
            response["flow_prompt"] = {
                "type": "flow_prompt",
                "flow_id": self._active_screening_flow.flow_id if self._active_screening_flow else "",
                "step": result.next_step,
                "prompt": result.prompt.prompt,
                "input_type": result.prompt.input_type,
                "options": result.prompt.options,
            }
        return response
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_sessions/test_engine.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/sessions/engine.py backend/tests/test_sessions/test_engine.py
git commit -m "feat: add SessionEngine orchestration with proactive greetings"
```

---

## Task 7: ConversationEngine Integration

**Files:**
- Modify: `backend/app/chat/engine.py`
- Modify: `backend/app/chat/router.py`

- [ ] **Step 1: Add SessionEngine to ConversationEngine**

In `backend/app/chat/engine.py`, in `__init__`:

```python
from app.sessions.engine import SessionEngine

class ConversationEngine:
    def __init__(self, user: User):
        self.user = user
        self.active_flows: dict[str, BaseFlow] = {}
        self._message_count: int = 0
        self.session_engine = SessionEngine(user)
```

In `_route_message`, add after Priority 3 (slow escalation) and before Priority 4 (active flow). **Use the existing `context` parameter** already passed into `_route_message()`:

```python
    # Priority 4 (NEW): SessionEngine — protocols, screenings, homework
    session_response = await self.session_engine.try_handle(content, context)
    if session_response:
        return session_response

    # Priority 5: Active flow (was Priority 4)
```

**Note:** `_route_message()` already receives a `UserContext` built by `handle_message()` via `self._build_user_context()`. Do not create a new one.

- [ ] **Step 2: Add session_start handling to WebSocket router**

In `backend/app/chat/router.py`, in the message loop, add before `if msg_type == "message":`:

```python
            if msg_type == "session_start":
                context = UserContext(
                    user_id=str(user.id),
                    user_name=user.name,
                )
                greeting = await engine.session_engine.handle_session_start(context)
                if greeting:
                    await manager.send_to_connection(websocket, greeting)
                continue
```

Add the import at the top: `from app.chat.flows.base import UserContext`

- [ ] **Step 3: Run existing tests to verify nothing broken**

```bash
cd backend && python -m pytest tests/ -v --timeout=30
```

Expected: All existing tests still pass.

- [ ] **Step 4: Commit**

```bash
git add backend/app/chat/engine.py backend/app/chat/router.py
git commit -m "feat: integrate SessionEngine into ConversationEngine routing"
```

---

## Task 8: Screening Triggers

**Files:**
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/screening_triggers.py`
- Test: `backend/tests/test_tasks/__init__.py`
- Test: `backend/tests/test_tasks/test_screening_triggers.py`

- [ ] **Step 1: Write tests for screening triggers**

Create `backend/tests/test_tasks/__init__.py` (empty) and `backend/tests/test_tasks/test_screening_triggers.py`:

```python
import pytest
from datetime import datetime, timezone, timedelta
from app.tasks.screening_triggers import check_screening_triggers
from app.models.inferred_state import InferredStateRecord
from app.models.screening import ScreeningResult
from app.models.notification import PendingAction


class TestScreeningTriggers:
    @pytest.mark.asyncio
    async def test_low_mood_3_days_triggers_phq9(self, test_user):
        user_id = str(test_user.id)
        # Create 3 days of low mood
        for i in range(3):
            await InferredStateRecord(
                user_id=user_id,
                mood_valence=2.5,
                energy_level=4.0,
                themes=[],
                confidence=0.8,
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
            ).insert()

        result = await check_screening_triggers(user_id)
        assert result == "phq9"

        # Verify PendingAction was created
        pa = await PendingAction.find_one(
            PendingAction.user_id == user_id,
            PendingAction.action_type == "screening_due",
        )
        assert pa is not None
        assert pa.data["instrument"] == "phq9"

    @pytest.mark.asyncio
    async def test_anxiety_theme_3_days_triggers_gad7(self, test_user):
        user_id = str(test_user.id)
        for i in range(3):
            await InferredStateRecord(
                user_id=user_id,
                mood_valence=5.0,
                energy_level=5.0,
                themes=["anxiety"],
                confidence=0.8,
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
            ).insert()

        result = await check_screening_triggers(user_id)
        assert result == "gad7"

    @pytest.mark.asyncio
    async def test_no_trigger_if_recent_screening(self, test_user):
        user_id = str(test_user.id)
        # Low mood for 3 days
        for i in range(3):
            await InferredStateRecord(
                user_id=user_id,
                mood_valence=2.0,
                themes=[],
                confidence=0.8,
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
            ).insert()
        # But screening was done recently
        await ScreeningResult(
            user_id=user_id,
            instrument="phq9",
            item_scores=[1]*9,
            total_score=9,
            severity_tier="mild",
            status="completed",
            current_item=9,
            completed_at=datetime.now(timezone.utc) - timedelta(days=1),
        ).insert()

        result = await check_screening_triggers(user_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_trigger_with_insufficient_data(self, test_user):
        user_id = str(test_user.id)
        # Only 2 days of low mood (need 3)
        for i in range(2):
            await InferredStateRecord(
                user_id=user_id,
                mood_valence=2.0,
                themes=[],
                confidence=0.8,
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
            ).insert()

        result = await check_screening_triggers(user_id)
        assert result is None
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_tasks/test_screening_triggers.py -v 2>&1 | head -20
```

- [ ] **Step 3: Implement screening triggers**

Create `backend/app/tasks/__init__.py` (empty) and `backend/app/tasks/screening_triggers.py`:

```python
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.models.inferred_state import InferredStateRecord
from app.models.screening import ScreeningResult
from app.models.notification import PendingAction


async def check_screening_triggers(user_id: str) -> Optional[str]:
    """
    Check if user's recent state warrants a screening.
    Returns instrument name (phq9/gad7/pcl5) or None.
    """
    # Skip if screening was completed in last 14 days
    recent_screening = await ScreeningResult.find_one(
        ScreeningResult.user_id == user_id,
        ScreeningResult.status == "completed",
        ScreeningResult.completed_at >= datetime.now(timezone.utc) - timedelta(days=14),
    )
    if recent_screening:
        return None

    # Skip if there's already a pending screening action
    existing_action = await PendingAction.find_one(
        PendingAction.user_id == user_id,
        PendingAction.action_type == "screening_due",
        PendingAction.dismissed == False,
    )
    if existing_action:
        return None

    # Get recent inferred states (last 7 days, one per day max)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_states = await InferredStateRecord.find(
        InferredStateRecord.user_id == user_id,
        InferredStateRecord.created_at >= week_ago,
        InferredStateRecord.confidence >= 0.3,
    ).sort("-created_at").to_list()

    if len(recent_states) < 3:
        return None

    # Group by day
    days = {}
    for state in recent_states:
        day_key = state.created_at.date()
        if day_key not in days:
            days[day_key] = state

    day_states = sorted(days.values(), key=lambda s: s.created_at, reverse=True)

    # Check: 3+ consecutive days of low mood -> PHQ-9
    low_mood_streak = 0
    for state in day_states:
        if state.mood_valence is not None and state.mood_valence <= 3:
            low_mood_streak += 1
        else:
            break
    if low_mood_streak >= 3:
        await _create_pending_action(user_id, "phq9")
        return "phq9"

    # Check: 3+ days with anxiety theme -> GAD-7
    anxiety_days = sum(
        1 for s in day_states[:7]
        if "anxiety" in (s.themes or [])
    )
    if anxiety_days >= 3:
        await _create_pending_action(user_id, "gad7")
        return "gad7"

    # Check: 3+ days with high absolutist language -> PHQ-9
    absolutist_days = sum(
        1 for s in day_states[:7]
        if s.absolutist_count >= 3
    )
    if absolutist_days >= 3:
        await _create_pending_action(user_id, "phq9")
        return "phq9"

    # Check: trauma theme in 2+ messages in a week -> PCL-5
    trauma_count = sum(
        1 for s in recent_states
        if "trauma" in (s.themes or [])
    )
    if trauma_count >= 2:
        await _create_pending_action(user_id, "pcl5")
        return "pcl5"

    return None


async def _create_pending_action(user_id: str, instrument: str):
    pa = PendingAction(
        user_id=user_id,
        action_type="screening_due",
        priority=3,
        data={"instrument": instrument},
    )
    await pa.insert()
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_tasks/test_screening_triggers.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/tasks/ backend/tests/test_tasks/
git commit -m "feat: add pattern-based screening triggers from inferred state"
```

---

## Task 9: Notification Service + Scheduler

**Files:**
- Create: `backend/app/notifications/__init__.py`
- Create: `backend/app/notifications/service.py`
- Create: `backend/app/notifications/router.py`
- Create: `backend/app/tasks/scheduler.py`
- Create: `backend/app/tasks/reminders.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_notifications/__init__.py`
- Test: `backend/tests/test_notifications/test_service.py`
- Test: `backend/tests/test_tasks/test_reminders.py`

- [ ] **Step 1: Add dependencies to pyproject.toml**

Add to `[project] dependencies`:

```toml
"APScheduler>=3.10",
"pywebpush>=2.0",
"py-vapid>=1.9",
```

Run: `cd backend && pip install -e ".[dev]"`

- [ ] **Step 2: Add VAPID settings to config.py**

In `backend/app/config.py`, add to Settings class:

```python
# Web Push (VAPID)
vapid_private_key: str = ""
vapid_public_key: str = ""
vapid_email: str = "mailto:admin@mirror.app"
```

- [ ] **Step 3: Write tests for notification service**

Create `backend/tests/test_notifications/__init__.py` (empty) and `backend/tests/test_notifications/test_service.py`:

```python
import pytest
from app.notifications.service import NotificationService
from app.models.notification import PendingAction
from app.models.user import User


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_get_top_pending_action(self, test_user):
        user_id = str(test_user.id)
        await PendingAction(
            user_id=user_id,
            action_type="screening_due",
            priority=3,
        ).insert()
        await PendingAction(
            user_id=user_id,
            action_type="homework_review",
            priority=1,
        ).insert()

        action = await NotificationService.get_top_pending_action(user_id)
        assert action.action_type == "homework_review"  # Higher priority (lower number)

    @pytest.mark.asyncio
    async def test_no_pending_actions(self, test_user):
        action = await NotificationService.get_top_pending_action(str(test_user.id))
        assert action is None

    @pytest.mark.asyncio
    async def test_dismissed_actions_excluded(self, test_user):
        user_id = str(test_user.id)
        await PendingAction(
            user_id=user_id,
            action_type="screening_due",
            priority=3,
            dismissed=True,
        ).insert()

        action = await NotificationService.get_top_pending_action(user_id)
        assert action is None

    def test_is_quiet_hours(self):
        from datetime import time
        assert NotificationService.is_quiet_hours(
            current_hour=23, quiet_start="22:00", quiet_end="08:00"
        ) is True
        assert NotificationService.is_quiet_hours(
            current_hour=12, quiet_start="22:00", quiet_end="08:00"
        ) is False
        assert NotificationService.is_quiet_hours(
            current_hour=7, quiet_start="22:00", quiet_end="08:00"
        ) is True
```

- [ ] **Step 4: Implement notification service**

Create `backend/app/notifications/__init__.py` (empty) and `backend/app/notifications/service.py`:

```python
from typing import Optional

from app.models.notification import PendingAction
from app.models.user import User


class NotificationService:
    @staticmethod
    async def get_top_pending_action(user_id: str) -> Optional[PendingAction]:
        return await PendingAction.find_one(
            PendingAction.user_id == user_id,
            PendingAction.dismissed == False,
        sort_expression=[("priority", 1), ("created_at", 1)])

    @staticmethod
    async def create_action(
        user_id: str, action_type: str, priority: int, data: dict = None
    ) -> PendingAction:
        pa = PendingAction(
            user_id=user_id,
            action_type=action_type,
            priority=priority,
            data=data or {},
        )
        await pa.insert()
        return pa

    @staticmethod
    def is_quiet_hours(current_hour: int, quiet_start: str, quiet_end: str) -> bool:
        start_h = int(quiet_start.split(":")[0])
        end_h = int(quiet_end.split(":")[0])
        if start_h > end_h:  # Crosses midnight (e.g., 22:00 - 08:00)
            return current_hour >= start_h or current_hour < end_h
        return start_h <= current_hour < end_h

    @staticmethod
    async def send_push(user: User, title: str, body: str) -> bool:
        """Send web push notification. Returns False if user has no subscription."""
        if not user.notification_enabled or not user.push_subscription:
            return False

        try:
            from pywebpush import webpush
            from app.config import settings
            import json

            if not settings.vapid_private_key:
                return False

            webpush(
                subscription_info=user.push_subscription,
                data=json.dumps({"title": title, "body": body}),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_email},
            )
            return True
        except Exception:
            return False
```

- [ ] **Step 5: Write tests for reminders**

Create `backend/tests/test_tasks/test_reminders.py`:

```python
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.tasks.reminders import (
    check_homework_reminders,
    check_reengagement,
)
from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment
from app.models.user import User


class TestHomeworkReminders:
    @pytest.mark.asyncio
    async def test_increments_reminder_count(self, test_user):
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=1,
            status="active",
        )
        await enrollment.insert()
        hw = Homework(
            user_id=str(test_user.id),
            enrollment_id=str(enrollment.id),
            session_number=1,
            description="Mood monitoring",
            adaptive_tier="structured",
            status="assigned",
            due_date=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        await hw.insert()

        with patch("app.tasks.reminders.NotificationService.send_push", new_callable=AsyncMock) as mock_push:
            await check_homework_reminders()

        updated = await Homework.get(hw.id)
        assert updated.reminder_count == 1
        assert updated.status == "reminded"


class TestReengagement:
    @pytest.mark.asyncio
    async def test_pauses_after_14_days_inactive(self, test_user):
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=3,
            status="active",
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
        )
        await enrollment.insert()

        # Last session was 15 days ago
        from app.models.protocol import ProtocolSession
        await ProtocolSession(
            enrollment_id=str(enrollment.id),
            user_id=str(test_user.id),
            session_number=2,
            started_at=datetime.now(timezone.utc) - timedelta(days=15),
            completed_at=datetime.now(timezone.utc) - timedelta(days=15),
        ).insert()

        with patch("app.tasks.reminders.NotificationService.send_push", new_callable=AsyncMock):
            await check_reengagement()

        updated = await ProtocolEnrollment.get(enrollment.id)
        assert updated.status == "paused"
```

- [ ] **Step 6: Implement reminders**

Create `backend/app/tasks/reminders.py`:

```python
from datetime import datetime, timezone, timedelta

from app.models.homework import Homework
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.user import User
from app.notifications.service import NotificationService


async def check_homework_reminders():
    """Check for homework that needs reminding."""
    overdue = await Homework.find(
        Homework.status.is_in(["assigned", "reminded"]),
        Homework.due_date <= datetime.now(timezone.utc),
    ).to_list()

    for hw in overdue:
        user = await User.get(hw.user_id)
        if not user:
            continue

        # NOTE: V1 uses UTC for quiet hours. Users set quiet hours in UTC.
        # Future: add user.timezone field and convert.
        now_hour = datetime.now(timezone.utc).hour
        if NotificationService.is_quiet_hours(
            now_hour, user.quiet_hours_start, user.quiet_hours_end
        ):
            continue

        hw.reminder_count += 1
        hw.status = "reminded"
        await hw.save()

        # Adaptive message based on reminder count
        if hw.reminder_count == 1:
            body = f"Quick check — how's \"{hw.description}\" going?"
        elif hw.reminder_count == 2:
            body = "No pressure. I'm here when you're ready."
        else:
            body = "Just checking in."

        await NotificationService.send_push(user, "Mirror", body)


async def check_reengagement():
    """Check for users who haven't engaged with their protocol."""
    active_enrollments = await ProtocolEnrollment.find(
        ProtocolEnrollment.status == "active",
    ).to_list()

    for enrollment in active_enrollments:
        # Find last session activity
        last_session = await ProtocolSession.find_one(
            ProtocolSession.enrollment_id == str(enrollment.id),
        sort_expression=[("completed_at", -1)])

        if not last_session or not last_session.completed_at:
            last_activity = enrollment.start_date
        else:
            last_activity = last_session.completed_at

        days_inactive = (datetime.now(timezone.utc) - last_activity).days
        user = await User.get(enrollment.user_id)
        if not user:
            continue

        if days_inactive >= 14:
            enrollment.status = "paused"
            await enrollment.save()
            await NotificationService.send_push(
                user, "Mirror",
                "It's been a while. No pressure at all — I'm here whenever you're ready to continue, "
                "or we can just chat."
            )
        elif days_inactive >= 7:
            await NotificationService.send_push(
                user, "Mirror", "No pressure, but I'm here when you need me."
            )
        elif days_inactive >= 3:
            await NotificationService.send_push(
                user, "Mirror", "Your next session is ready when you are."
            )
```

- [ ] **Step 7: Implement scheduler**

Create `backend/app/tasks/scheduler.py`:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

scheduler: AsyncIOScheduler | None = None


def setup_scheduler():
    """Configure and start the scheduler with MongoDB jobstore. Call from app lifespan."""
    global scheduler

    jobstore = MongoDBJobStore(
        database=settings.mongodb_db_name,
        collection="apscheduler_jobs",
        host=settings.mongodb_url,
    )
    scheduler = AsyncIOScheduler(
        jobstores={"default": jobstore},
        job_defaults={"misfire_grace_time": 7200},  # 2 hours — discard older missed jobs
    )

    from app.tasks.reminders import check_homework_reminders, check_reengagement

    scheduler.add_job(
        check_homework_reminders,
        IntervalTrigger(hours=1),
        id="homework_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        check_reengagement,
        IntervalTrigger(hours=24),
        id="reengagement_check",
        replace_existing=True,
    )
    scheduler.start()


def shutdown_scheduler():
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
```

- [ ] **Step 8: Update main.py lifespan to start scheduler**

In `backend/app/main.py`, in the lifespan function:

```python
from app.tasks.scheduler import setup_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    setup_scheduler()
    yield
    shutdown_scheduler()
    await close_db()
```

- [ ] **Step 9: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_notifications/ tests/test_tasks/ -v
```

- [ ] **Step 10: Commit**

```bash
git add backend/app/notifications/ backend/app/tasks/ backend/tests/test_notifications/ backend/tests/test_tasks/ backend/pyproject.toml backend/app/config.py backend/app/main.py
git commit -m "feat: add notification service, scheduler, and reminder system"
```

---

## Task 10: API Routers

**Files:**
- Create: `backend/app/screening/router.py`
- Create: `backend/app/sessions/router.py`
- Create: `backend/app/notifications/router.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Implement screening router**

Create `backend/app/screening/router.py`:

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User
from app.models.screening import ScreeningResult

router = APIRouter()


@router.get("/history")
async def screening_history(user: User = Depends(get_current_user)):
    results = await ScreeningResult.find(
        ScreeningResult.user_id == str(user.id),
        ScreeningResult.status == "completed",
    ).sort("-created_at").to_list()
    return [
        {
            "id": str(r.id),
            "instrument": r.instrument,
            "total_score": r.total_score,
            "severity_tier": r.severity_tier,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in results
    ]


@router.get("/{screening_id}")
async def screening_detail(screening_id: str, user: User = Depends(get_current_user)):
    result = await ScreeningResult.get(screening_id)
    if not result or result.user_id != str(user.id):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Screening not found")
    return {
        "id": str(result.id),
        "instrument": result.instrument,
        "item_scores": result.item_scores,
        "total_score": result.total_score,
        "severity_tier": result.severity_tier,
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
    }
```

- [ ] **Step 2: Implement sessions router**

Create `backend/app/sessions/router.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.models.user import User
from app.models.protocol import ProtocolEnrollment, ProtocolSession
from app.models.homework import Homework

router = APIRouter()


@router.get("/protocols/current")
async def current_protocol(user: User = Depends(get_current_user)):
    enrollment = await ProtocolEnrollment.find_one(
        ProtocolEnrollment.user_id == str(user.id),
        ProtocolEnrollment.status.is_in(["enrolled", "active", "paused"]),
    )
    if not enrollment:
        return None
    return {
        "id": str(enrollment.id),
        "protocol_id": enrollment.protocol_id,
        "current_session_number": enrollment.current_session_number,
        "status": enrollment.status,
        "start_date": enrollment.start_date.isoformat(),
        "screening_scores": enrollment.screening_scores,
    }


@router.get("/protocols/history")
async def protocol_history(user: User = Depends(get_current_user)):
    enrollments = await ProtocolEnrollment.find(
        ProtocolEnrollment.user_id == str(user.id),
    ).sort("-start_date").to_list()
    return [
        {
            "id": str(e.id),
            "protocol_id": e.protocol_id,
            "status": e.status,
            "start_date": e.start_date.isoformat(),
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "screening_scores": e.screening_scores,
        }
        for e in enrollments
    ]


@router.get("/protocols/{enrollment_id}/sessions")
async def protocol_sessions(enrollment_id: str, user: User = Depends(get_current_user)):
    sessions = await ProtocolSession.find(
        ProtocolSession.enrollment_id == enrollment_id,
        ProtocolSession.user_id == str(user.id),
    ).sort("session_number").to_list()
    return [
        {
            "id": str(s.id),
            "session_number": s.session_number,
            "goals": s.goals,
            "outcome": s.outcome,
            "started_at": s.started_at.isoformat(),
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in sessions
    ]


@router.get("/homework/pending")
async def pending_homework(user: User = Depends(get_current_user)):
    hw = await Homework.find_one(
        Homework.user_id == str(user.id),
        Homework.status.is_in(["assigned", "reminded"]),
    )
    if not hw:
        return None
    return {
        "id": str(hw.id),
        "description": hw.description,
        "adaptive_tier": hw.adaptive_tier,
        "due_date": hw.due_date.isoformat() if hw.due_date else None,
        "reminder_count": hw.reminder_count,
    }


@router.post("/homework/{homework_id}/complete")
async def complete_homework(
    homework_id: str,
    body: dict,
    user: User = Depends(get_current_user),
):
    hw = await Homework.get(homework_id)
    if not hw or hw.user_id != str(user.id):
        raise HTTPException(status_code=404, detail="Homework not found")

    from app.sessions.homework import HomeworkManager
    from datetime import datetime, timezone

    hw = await HomeworkManager.complete(hw, body.get("response", ""))

    # Update enrollment miss counter
    enrollment = await ProtocolEnrollment.get(hw.enrollment_id)
    if enrollment:
        enrollment.consecutive_homework_misses = 0
        await enrollment.save()

    return {"status": "completed"}
```

- [ ] **Step 3: Implement notifications router**

Create `backend/app/notifications/router.py`:

```python
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User
from app.models.notification import PendingAction

router = APIRouter()


@router.get("/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    return {
        "preferred_session_time": user.preferred_session_time,
        "notification_enabled": user.notification_enabled,
        "max_notifications_per_day": user.max_notifications_per_day,
        "quiet_hours_start": user.quiet_hours_start,
        "quiet_hours_end": user.quiet_hours_end,
    }


@router.put("/preferences")
async def update_preferences(body: dict, user: User = Depends(get_current_user)):
    allowed = {
        "preferred_session_time", "notification_enabled",
        "max_notifications_per_day", "quiet_hours_start", "quiet_hours_end",
    }
    for key, value in body.items():
        if key in allowed:
            setattr(user, key, value)
    await user.save()
    return {"status": "updated"}


@router.post("/subscribe")
async def subscribe_push(body: dict, user: User = Depends(get_current_user)):
    user.push_subscription = body.get("subscription")
    user.notification_enabled = True
    await user.save()
    return {"status": "subscribed"}


@router.get("/pending-actions")
async def pending_actions(user: User = Depends(get_current_user)):
    actions = await PendingAction.find(
        PendingAction.user_id == str(user.id),
        PendingAction.dismissed == False,
    ).sort("priority").to_list()
    return [
        {
            "id": str(a.id),
            "action_type": a.action_type,
            "priority": a.priority,
            "data": a.data,
        }
        for a in actions
    ]
```

- [ ] **Step 4: Mount routers in main.py**

In `backend/app/main.py`, add:

```python
from app.screening.router import router as screening_router
from app.sessions.router import router as sessions_router
from app.notifications.router import router as notifications_router

app.include_router(screening_router, prefix="/api/screening", tags=["screening"])
app.include_router(sessions_router, prefix="/api", tags=["sessions"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])
```

- [ ] **Step 5: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v --timeout=30
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/screening/router.py backend/app/sessions/router.py backend/app/notifications/router.py backend/app/main.py
git commit -m "feat: add API routers for screening, sessions, homework, notifications"
```

---

## Task 11: Frontend session_start Integration

**Files:**
- Modify: `frontend/src/lib/stores/chat.ts`
- Modify: `frontend/src/lib/api/client.ts`

- [ ] **Step 1: Send session_start on WebSocket connect**

In `frontend/src/lib/stores/chat.ts`, in the WebSocket `onopen` handler, add after connection is established:

```typescript
ws.send(JSON.stringify({ type: "session_start" }));
```

This triggers the proactive greeting flow on the backend.

- [ ] **Step 2: Add notification preferences API methods**

In `frontend/src/lib/api/client.ts`, add:

```typescript
// Notifications
async getNotificationPreferences() {
    return this.fetch('/notifications/preferences');
}

async updateNotificationPreferences(prefs: Record<string, any>) {
    return this.fetch('/notifications/preferences', {
        method: 'PUT',
        body: JSON.stringify(prefs),
    });
}

async subscribePush(subscription: PushSubscriptionJSON) {
    return this.fetch('/notifications/subscribe', {
        method: 'POST',
        body: JSON.stringify({ subscription }),
    });
}

// Screening
async getScreeningHistory() {
    return this.fetch('/screening/history');
}

// Protocol
async getCurrentProtocol() {
    return this.fetch('/protocols/current');
}

async getPendingHomework() {
    return this.fetch('/homework/pending');
}

async completeHomework(homeworkId: string, response: string) {
    return this.fetch(`/homework/${homeworkId}/complete`, {
        method: 'POST',
        body: JSON.stringify({ response }),
    });
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/stores/chat.ts frontend/src/lib/api/client.ts
git commit -m "feat: add session_start WebSocket message and protocol API methods"
```

---

## Task 12: Mid-Protocol Screening + Protocol Switching

**Files:**
- Modify: `backend/app/sessions/engine.py`
- Test: `backend/tests/test_sessions/test_mid_protocol.py`

- [ ] **Step 1: Write tests for mid-protocol screening and switching**

Create `backend/tests/test_sessions/test_mid_protocol.py`:

```python
import pytest
from app.sessions.engine import SessionEngine
from app.models.protocol import ProtocolEnrollment
from app.models.user import User
from app.chat.flows.base import UserContext
from app.protocols.cbt_depression import CBTDepressionProtocol


@pytest.fixture
def context():
    return UserContext(user_id="test-user", user_name="Test")


class TestMidProtocolScreening:
    @pytest.mark.asyncio
    async def test_mid_screening_triggered_at_session_4(self, test_user, context):
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=4,
            status="active",
        )
        await enrollment.insert()

        engine = SessionEngine(test_user)
        needs_screening = await engine.check_mid_protocol_screening(enrollment)
        assert needs_screening is True

    @pytest.mark.asyncio
    async def test_no_mid_screening_at_session_2(self, test_user, context):
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=2,
            status="active",
        )
        await enrollment.insert()

        engine = SessionEngine(test_user)
        needs_screening = await engine.check_mid_protocol_screening(enrollment)
        assert needs_screening is False


class TestProtocolSwitching:
    @pytest.mark.asyncio
    async def test_switch_cbt_to_ba(self, test_user, context):
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=4,
            status="active",
        )
        await enrollment.insert()

        engine = SessionEngine(test_user)
        new_enrollment = await engine.switch_protocol(
            enrollment, "behavioral_activation"
        )
        assert new_enrollment is not None
        assert new_enrollment.protocol_id == "behavioral_activation"
        assert new_enrollment.current_session_number == 3  # Skip sessions 1-2

        # Old enrollment marked as switched
        old = await ProtocolEnrollment.get(enrollment.id)
        assert old.status == "switched"
        assert old.switched_to_enrollment_id == str(new_enrollment.id)
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/test_sessions/test_mid_protocol.py -v 2>&1 | head -20
```

- [ ] **Step 3: Add mid-protocol screening and switching to SessionEngine**

In `backend/app/sessions/engine.py`, add these methods to `SessionEngine`:

```python
    async def check_mid_protocol_screening(
        self, enrollment: ProtocolEnrollment
    ) -> bool:
        """Check if current session number matches protocol's mid-screening point."""
        protocol = get_protocol(enrollment.protocol_id)
        if not protocol:
            return False
        return enrollment.current_session_number == protocol.mid_screening_session

    async def switch_protocol(
        self,
        current_enrollment: ProtocolEnrollment,
        new_protocol_id: str,
    ) -> Optional[ProtocolEnrollment]:
        """Switch from current protocol to a new one (e.g., CBT -> BA)."""
        new_protocol = get_protocol(new_protocol_id)
        if not new_protocol:
            return None

        # Determine starting session (skip overlap sessions)
        start_session = 1
        if hasattr(new_protocol, 'skip_sessions_on_switch'):
            skippable = new_protocol.skip_sessions_on_switch
            start_session = max(skippable) + 1 if skippable else 1

        # Create new enrollment
        new_enrollment = ProtocolEnrollment(
            user_id=current_enrollment.user_id,
            protocol_id=new_protocol_id,
            current_session_number=start_session,
            status="enrolled",
            entry_screening_id=current_enrollment.entry_screening_id,
            screening_scores=current_enrollment.screening_scores,
        )
        await new_enrollment.insert()

        # Mark old as switched
        current_enrollment.status = "switched"
        current_enrollment.switched_to_enrollment_id = str(new_enrollment.id)
        current_enrollment.end_date = datetime.now(timezone.utc)
        await current_enrollment.save()

        return new_enrollment
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_sessions/test_mid_protocol.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/sessions/engine.py backend/tests/test_sessions/test_mid_protocol.py
git commit -m "feat: add mid-protocol re-screening and protocol switching (CBT->BA)"
```

---

## Task 13: API Router Tests

**Files:**
- Test: `backend/tests/test_screening/test_router.py`
- Test: `backend/tests/test_sessions/test_router.py`
- Test: `backend/tests/test_notifications/test_router.py`

- [ ] **Step 1: Write API tests for screening router**

Create `backend/tests/test_screening/test_router.py`:

```python
import pytest
from app.models.screening import ScreeningResult
from datetime import datetime, timezone


class TestScreeningRouter:
    @pytest.mark.asyncio
    async def test_screening_history(self, auth_client, test_user):
        await ScreeningResult(
            user_id=str(test_user.id),
            instrument="phq9",
            item_scores=[1]*9,
            total_score=9,
            severity_tier="mild",
            status="completed",
            current_item=9,
            completed_at=datetime.now(timezone.utc),
        ).insert()

        res = await auth_client.get("/api/screening/history")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["instrument"] == "phq9"

    @pytest.mark.asyncio
    async def test_screening_history_empty(self, auth_client):
        res = await auth_client.get("/api/screening/history")
        assert res.status_code == 200
        assert res.json() == []
```

- [ ] **Step 2: Write API tests for sessions router**

Create `backend/tests/test_sessions/test_router.py`:

```python
import pytest
from app.models.protocol import ProtocolEnrollment
from app.models.homework import Homework


class TestSessionsRouter:
    @pytest.mark.asyncio
    async def test_current_protocol_none(self, auth_client):
        res = await auth_client.get("/api/protocols/current")
        assert res.status_code == 200
        assert res.json() is None

    @pytest.mark.asyncio
    async def test_current_protocol_active(self, auth_client, test_user):
        await ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=3,
            status="active",
        ).insert()

        res = await auth_client.get("/api/protocols/current")
        assert res.status_code == 200
        data = res.json()
        assert data["protocol_id"] == "cbt_depression"

    @pytest.mark.asyncio
    async def test_complete_homework(self, auth_client, test_user):
        enrollment = ProtocolEnrollment(
            user_id=str(test_user.id),
            protocol_id="cbt_depression",
            current_session_number=1,
            status="active",
        )
        await enrollment.insert()
        hw = Homework(
            user_id=str(test_user.id),
            enrollment_id=str(enrollment.id),
            session_number=1,
            description="Mood monitoring",
            adaptive_tier="structured",
            status="assigned",
        )
        await hw.insert()

        res = await auth_client.post(
            f"/api/homework/{str(hw.id)}/complete",
            json={"response": "I tracked my mood for 3 days"},
        )
        assert res.status_code == 200

        updated = await Homework.get(hw.id)
        assert updated.status == "completed"
```

- [ ] **Step 3: Write API tests for notifications router**

Create `backend/tests/test_notifications/test_router.py`:

```python
import pytest


class TestNotificationsRouter:
    @pytest.mark.asyncio
    async def test_get_preferences(self, auth_client):
        res = await auth_client.get("/api/notifications/preferences")
        assert res.status_code == 200
        data = res.json()
        assert data["notification_enabled"] is False
        assert data["preferred_session_time"] == "evening"

    @pytest.mark.asyncio
    async def test_update_preferences(self, auth_client):
        res = await auth_client.put(
            "/api/notifications/preferences",
            json={"notification_enabled": True, "preferred_session_time": "morning"},
        )
        assert res.status_code == 200

        res = await auth_client.get("/api/notifications/preferences")
        data = res.json()
        assert data["notification_enabled"] is True
        assert data["preferred_session_time"] == "morning"
```

- [ ] **Step 4: Run all API tests**

```bash
cd backend && python -m pytest tests/test_screening/test_router.py tests/test_sessions/test_router.py tests/test_notifications/test_router.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_screening/test_router.py backend/tests/test_sessions/test_router.py backend/tests/test_notifications/test_router.py
git commit -m "test: add API router tests for screening, sessions, notifications"
```

---

## Task 14: Integration Test — Full Flow

**Files:**
- Test: `backend/tests/test_integration/test_full_protocol_flow.py`

- [ ] **Step 1: Write end-to-end integration test**

Create `backend/tests/test_integration/__init__.py` (empty) and `backend/tests/test_integration/test_full_protocol_flow.py`:

```python
import pytest
from datetime import datetime, timezone, timedelta

from app.sessions.engine import SessionEngine
from app.models.user import User
from app.models.protocol import ProtocolEnrollment
from app.models.screening import ScreeningResult
from app.models.notification import PendingAction
from app.models.homework import Homework
from app.chat.flows.base import UserContext
from app.psychology.severity import SeverityRouter
from app.tasks.screening_triggers import check_screening_triggers
from app.models.inferred_state import InferredStateRecord


class TestFullProtocolFlow:
    @pytest.mark.asyncio
    async def test_mood_triggers_screening_triggers_enrollment(self, test_user):
        """
        Simulate: 3 days low mood -> screening triggered -> PHQ-9 moderate ->
        CBT protocol offered -> user enrolls -> session 1 greeting
        """
        user_id = str(test_user.id)
        ctx = UserContext(user_id=user_id, user_name=test_user.name)

        # Day 1-3: Low mood detected
        for i in range(3):
            await InferredStateRecord(
                user_id=user_id,
                mood_valence=2.5,
                energy_level=4.0,
                themes=["work"],
                confidence=0.8,
                created_at=datetime.now(timezone.utc) - timedelta(days=i),
            ).insert()

        # Trigger check should flag PHQ-9
        result = await check_screening_triggers(user_id)
        assert result == "phq9"

        # Verify pending action created
        pa = await PendingAction.find_one(
            PendingAction.user_id == user_id,
            PendingAction.action_type == "screening_due",
        )
        assert pa is not None

        # User opens app -> session_start
        engine = SessionEngine(test_user)
        greeting = await engine.handle_session_start(ctx)
        assert greeting is not None  # Should start screening

        # Complete PHQ-9 with moderate score (total=12)
        scores = [2, 1, 1, 1, 2, 1, 1, 2, 1]  # = 12
        for score_val in scores:
            option_label = ["Not at all", "Several days", "More than half the days", "Nearly every day"][score_val]
            await engine._active_screening_flow.process(option_label, ctx)

        # Verify screening result saved
        sr = await ScreeningResult.find_one(
            ScreeningResult.user_id == user_id,
            ScreeningResult.status == "completed",
        )
        assert sr is not None
        assert sr.total_score == 12
        assert sr.severity_tier == "moderate"

        # Severity router should recommend protocol
        decision = SeverityRouter.route("phq9", 12)
        assert decision.action == "recommend_protocol"
        assert "cbt_depression" in decision.eligible_protocols

        # User accepts -> enroll
        enrollment = await engine.enroll(
            protocol_id="cbt_depression",
            screening_id=str(sr.id),
        )
        assert enrollment is not None
        assert enrollment.status == "enrolled"

        # Next session_start should show session 1 greeting
        greeting2 = await engine.handle_session_start(ctx)
        assert greeting2 is not None
        assert "session 1" in greeting2["content"].lower() or "psychoeducation" in greeting2["content"].lower()
```

- [ ] **Step 2: Run integration test**

```bash
cd backend && python -m pytest tests/test_integration/test_full_protocol_flow.py -v
```

Fix any issues discovered.

- [ ] **Step 3: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v --timeout=30
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_integration/
git commit -m "test: add end-to-end integration test for full protocol flow"
```

---

## Task 15: Final Wiring + Cleanup

- [ ] **Step 1: Run full test suite one more time**

```bash
cd backend && python -m pytest tests/ -v --timeout=30
```

- [ ] **Step 2: Run ruff linter**

```bash
cd backend && ruff check app/ tests/ --fix
```

- [ ] **Step 3: Verify all imports and model registrations**

Ensure every new model is in:
- `backend/app/models/base.py` init_beanie list
- `backend/app/models/__init__.py` exports
- `backend/tests/conftest.py` ALL_MODELS list

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final wiring, lint fixes, and cleanup for proactive psychology engine"
```
