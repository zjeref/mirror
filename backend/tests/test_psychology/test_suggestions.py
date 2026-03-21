"""Tests for the suggestion engine - the core decision maker."""

import pytest

from app.psychology.suggestions import UserState, suggest, score_strategy


class TestSuggestionEngine:
    def test_energy_1_only_mva(self):
        """At energy 1, ONLY micro-actions should be suggested."""
        state = UserState(energy=1, mood=5)
        result = suggest(state)
        assert result.strategy_type in ("mva", "validation")
        assert result.energy_required <= 2

    def test_energy_2_only_mva(self):
        state = UserState(energy=2, mood=5)
        result = suggest(state)
        assert result.strategy_type in ("mva", "validation")
        assert result.energy_required <= 2

    def test_energy_1_never_guilt_trips(self):
        """Suggestions at low energy must NEVER contain guilt language."""
        state = UserState(energy=1, mood=3)
        result = suggest(state)
        content_lower = result.content.lower()
        guilt_words = ["should", "must", "lazy", "need to", "have to"]
        for word in guilt_words:
            assert word not in content_lower, f"Found guilt word '{word}' in low-energy suggestion"

    def test_energy_1_has_validation(self):
        """Low energy suggestions must include validation."""
        state = UserState(energy=1, mood=3)
        result = suggest(state)
        assert result.validation is not None
        assert len(result.validation) > 0

    def test_returning_after_absence(self):
        """After 3+ days away, first response should be welcoming, not judgmental."""
        state = UserState(energy=5, mood=5, days_since_last_checkin=4)
        result = suggest(state)
        assert result.strategy_type == "validation"
        content_lower = result.content.lower()
        assert "should have" not in content_lower
        assert "missed" not in content_lower or "missed you" in content_lower

    def test_cognitive_distortion_triggers_cbt(self):
        """When user expresses cognitive distortion, CBT reframe should be suggested."""
        state = UserState(
            energy=5,
            mood=4,
            recent_thought="I always fail at everything and I'm worthless",
        )
        result = suggest(state)
        assert result.strategy_type == "cbt_reframe"

    def test_low_mood_prioritizes_mental_health(self):
        """When mood is very low, mental health actions should be prioritized."""
        state = UserState(energy=5, mood=2)
        result = suggest(state)
        assert result.life_area == "mental"

    def test_targets_weakest_life_area(self):
        """Suggestions should target the life area with lowest score."""
        state = UserState(
            energy=6,
            mood=6,
            life_area_scores={
                "physical": 8.0,
                "mental": 7.0,
                "career": 3.0,  # Weakest
                "habits": 6.0,
            },
        )
        result = suggest(state)
        assert result.life_area == "career"

    def test_has_rationale(self):
        """Every suggestion must include a rationale."""
        state = UserState(energy=5, mood=5)
        result = suggest(state)
        assert result.rationale
        assert len(result.rationale) > 0


class TestStrategyScoring:
    def test_high_energy_cost_penalized_at_low_energy(self):
        state = UserState(energy=2, mood=5)
        mva_score = score_strategy("mva", state)
        general_score = score_strategy("general", state)
        assert mva_score > general_score

    def test_recently_rejected_strategy_penalized(self):
        state = UserState(
            energy=5,
            mood=5,
            recent_rejections=["cbt_reframe"],
        )
        cbt_score = score_strategy("cbt_reframe", state)
        habit_score = score_strategy("tiny_habit", state)
        assert cbt_score < habit_score

    def test_effectiveness_history_matters(self):
        state = UserState(
            energy=5,
            mood=5,
            strategy_effectiveness={"mva": 0.9, "cbt_reframe": 0.2},
        )
        mva_score = score_strategy("mva", state)
        cbt_score = score_strategy("cbt_reframe", state)
        assert mva_score > cbt_score
