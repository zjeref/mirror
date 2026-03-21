"""Tests for dashboard endpoints and service."""

import pytest
from datetime import datetime, timezone

from app.models.check_in import CheckIn
from app.models.habit import Habit
from app.models.suggestion import Suggestion


class TestDashboardEndpoints:
    def test_summary_empty_user(self, auth_client):
        response = auth_client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["current_mood"] is None
        assert data["days_active"] == 0
        assert data["total_check_ins"] == 0

    def test_summary_with_checkin(self, auth_client, db, test_user):
        checkin = CheckIn(
            user_id=test_user.id,
            check_in_type="morning",
            mood_score=7,
            energy_score=6,
        )
        db.add(checkin)
        db.commit()

        response = auth_client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["current_mood"] == 7
        assert data["current_energy"] == 6
        assert data["total_check_ins"] == 1

    def test_summary_requires_auth(self, client):
        response = client.get("/api/dashboard/summary")
        assert response.status_code in (401, 403)

    def test_mood_trends_empty(self, auth_client):
        response = auth_client.get("/api/dashboard/mood-trends?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["data_points"] == []
        assert data["period_days"] == 30

    def test_mood_trends_with_data(self, auth_client, db, test_user):
        for i in range(5):
            db.add(CheckIn(
                user_id=test_user.id,
                check_in_type="morning",
                mood_score=6 + i % 3,
                energy_score=5,
            ))
        db.commit()

        response = auth_client.get("/api/dashboard/mood-trends?days=30")
        data = response.json()
        assert len(data["data_points"]) == 5
        assert data["average"] is not None

    def test_life_areas(self, auth_client):
        response = auth_client.get("/api/dashboard/life-areas")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # physical, mental, career, habits

    def test_patterns_empty(self, auth_client):
        response = auth_client.get("/api/dashboard/patterns")
        assert response.status_code == 200
        assert response.json() == []

    def test_habits_empty(self, auth_client):
        response = auth_client.get("/api/dashboard/habits")
        assert response.status_code == 200
        assert response.json() == []


class TestHabitEndpoints:
    def test_create_habit(self, auth_client):
        response = auth_client.post("/api/habits", json={
            "name": "Morning pushups",
            "anchor": "After I pour my coffee",
            "tiny_behavior": "Do 2 pushups",
            "life_area": "physical",
        })
        assert response.status_code == 201
        assert response.json()["name"] == "Morning pushups"

    def test_log_habit_completion(self, auth_client, db, test_user):
        habit = Habit(
            user_id=test_user.id,
            name="Pushups",
            anchor="After coffee",
            tiny_behavior="2 pushups",
            life_area="physical",
        )
        db.add(habit)
        db.commit()
        db.refresh(habit)

        response = auth_client.post(f"/api/habits/{habit.id}/log", json={
            "completed": True,
            "version_done": "tiny",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["streak"] == 1
        assert data["total_completions"] == 1

    def test_log_habit_updates_streak(self, auth_client, db, test_user):
        habit = Habit(
            user_id=test_user.id,
            name="Pushups",
            anchor="After coffee",
            tiny_behavior="2 pushups",
            life_area="physical",
            current_streak=5,
            longest_streak=5,
            total_completions=10,
        )
        db.add(habit)
        db.commit()
        db.refresh(habit)

        # Complete
        response = auth_client.post(f"/api/habits/{habit.id}/log", json={"completed": True})
        assert response.json()["streak"] == 6

    def test_log_habit_resets_streak_on_skip(self, auth_client, db, test_user):
        habit = Habit(
            user_id=test_user.id,
            name="Pushups",
            anchor="After coffee",
            tiny_behavior="2 pushups",
            life_area="physical",
            current_streak=5,
        )
        db.add(habit)
        db.commit()
        db.refresh(habit)

        response = auth_client.post(f"/api/habits/{habit.id}/log", json={"completed": False})
        assert response.json()["streak"] == 0

    def test_log_habit_not_found(self, auth_client):
        response = auth_client.post("/api/habits/nonexistent/log", json={"completed": True})
        assert response.status_code == 404


class TestSuggestionFeedback:
    def test_feedback_accepted(self, auth_client, db, test_user):
        suggestion = Suggestion(
            user_id=test_user.id,
            strategy_type="mva",
            life_area="physical",
            content="Take 3 deep breaths",
            energy_required=1,
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)

        response = auth_client.post(
            f"/api/suggestions/{suggestion.id}/feedback",
            json={"status": "accepted"},
        )
        assert response.status_code == 200

        db.refresh(suggestion)
        assert suggestion.status == "accepted"

    def test_feedback_with_rating(self, auth_client, db, test_user):
        suggestion = Suggestion(
            user_id=test_user.id,
            strategy_type="mva",
            life_area="physical",
            content="Walk to the door",
            energy_required=2,
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)

        response = auth_client.post(
            f"/api/suggestions/{suggestion.id}/feedback",
            json={"status": "completed", "effectiveness_rating": 4},
        )
        assert response.status_code == 200

        db.refresh(suggestion)
        assert suggestion.status == "completed"
        assert suggestion.effectiveness_rating == 4

    def test_feedback_not_found(self, auth_client):
        response = auth_client.post(
            "/api/suggestions/nonexistent/feedback",
            json={"status": "accepted"},
        )
        assert response.status_code == 404
