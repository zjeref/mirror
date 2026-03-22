import pytest
from app.models.check_in import CheckIn
from app.models.habit import Habit
from app.models.suggestion import Suggestion


class TestDashboardEndpoints:
    @pytest.mark.asyncio
    async def test_summary_empty(self, auth_client):
        resp = await auth_client.get("/api/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_mood"] is None
        assert data["total_check_ins"] == 0

    @pytest.mark.asyncio
    async def test_summary_with_checkin(self, auth_client, test_user):
        await CheckIn(user_id=str(test_user.id), check_in_type="morning",
                      mood_score=7, energy_score=6).insert()
        resp = await auth_client.get("/api/dashboard/summary")
        data = resp.json()
        assert data["current_mood"] == 7
        assert data["total_check_ins"] == 1

    @pytest.mark.asyncio
    async def test_requires_auth(self, client):
        resp = await client.get("/api/dashboard/summary")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_mood_trends(self, auth_client):
        resp = await auth_client.get("/api/dashboard/mood-trends?days=30")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_life_areas(self, auth_client):
        resp = await auth_client.get("/api/dashboard/life-areas")
        assert resp.status_code == 200
        assert len(resp.json()) == 4


class TestHabitEndpoints:
    @pytest.mark.asyncio
    async def test_create_habit(self, auth_client):
        resp = await auth_client.post("/api/habits", json={
            "name": "Pushups", "anchor": "After coffee",
            "tiny_behavior": "2 pushups", "life_area": "physical",
        })
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_log_habit(self, auth_client, test_user):
        habit = Habit(user_id=str(test_user.id), name="Pushups",
                      anchor="After coffee", tiny_behavior="2 pushups", life_area="physical")
        await habit.insert()
        resp = await auth_client.post(f"/api/habits/{habit.id}/log", json={"completed": True})
        assert resp.status_code == 200
        assert resp.json()["streak"] == 1

    @pytest.mark.asyncio
    async def test_streak_resets(self, auth_client, test_user):
        habit = Habit(user_id=str(test_user.id), name="X", anchor="Y",
                      tiny_behavior="Z", life_area="physical", current_streak=5)
        await habit.insert()
        resp = await auth_client.post(f"/api/habits/{habit.id}/log", json={"completed": False})
        assert resp.json()["streak"] == 0


class TestSuggestionFeedback:
    @pytest.mark.asyncio
    async def test_feedback(self, auth_client, test_user):
        s = Suggestion(user_id=str(test_user.id), strategy_type="mva",
                       life_area="physical", content="Breathe", energy_required=1)
        await s.insert()
        resp = await auth_client.post(f"/api/suggestions/{s.id}/feedback",
                                       json={"status": "completed", "effectiveness_rating": 4})
        assert resp.status_code == 200
