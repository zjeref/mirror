"""Tests for passive state inference engine."""

import pytest
from app.psychology.state_inference import infer_state, aggregate_states


class TestMoodInference:
    def test_positive_message(self):
        state = infer_state("I'm feeling really happy and grateful today")
        assert state.mood_valence is not None
        assert state.mood_valence >= 7

    def test_negative_message(self):
        state = infer_state("I'm sad and frustrated, everything feels hopeless")
        assert state.mood_valence is not None
        assert state.mood_valence <= 4

    def test_neutral_message(self):
        state = infer_state("I went to the store and bought some groceries")
        assert state.mood_valence is not None
        # Should be roughly neutral
        assert 4 <= state.mood_valence <= 7


class TestEnergyInference:
    def test_low_energy(self):
        state = infer_state("I'm exhausted, totally drained, can't do anything")
        assert state.energy_level is not None
        assert state.energy_level <= 3

    def test_high_energy(self):
        state = infer_state("I'm so excited and pumped, ready to go!")
        assert state.energy_level is not None
        assert state.energy_level >= 7


class TestChangeTalk:
    def test_detects_change_talk(self):
        state = infer_state("I want to start exercising, I think I could do it")
        assert state.change_talk_score > 0

    def test_detects_sustain_talk(self):
        state = infer_state("I can't do it, there's no point, it's too hard")
        assert state.sustain_talk_score > 0

    def test_change_talk_higher_than_sustain(self):
        state = infer_state("I'm ready to change, I will start tomorrow, I could try")
        assert state.change_talk_score > state.sustain_talk_score


class TestStageDetection:
    def test_contemplation(self):
        state = infer_state("Part of me wants to exercise but I know I should but I can't")
        assert "contemplation" in state.stage_signals

    def test_preparation(self):
        state = infer_state("I'm going to start running, how do I begin?")
        assert "preparation" in state.stage_signals

    def test_action(self):
        state = infer_state("I started going to the gym yesterday and did a workout")
        assert "action" in state.stage_signals


class TestThemeDetection:
    def test_health_theme(self):
        state = infer_state("I need to start going to the gym and eating better")
        assert "health" in state.themes

    def test_work_theme(self):
        state = infer_state("My boss gave me a terrible deadline at work")
        assert "work" in state.themes

    def test_multiple_themes(self):
        state = infer_state("I'm worried about money and my job is stressing me out")
        assert "money" in state.themes
        assert "work" in state.themes


class TestAbsolutistLanguage:
    def test_detects_absolutist(self):
        state = infer_state("I always fail and nothing ever works out")
        assert state.absolutist_count >= 2

    def test_no_absolutist_in_normal_text(self):
        state = infer_state("I had an okay day today")
        assert state.absolutist_count == 0


class TestAggregation:
    def test_aggregate_multiple_states(self):
        states = [
            infer_state("I'm really happy today, feeling great"),
            infer_state("I'm sad and tired"),
            infer_state("Feeling okay, nothing special"),
        ]
        agg = aggregate_states(states)
        assert agg["mood"] is not None
        assert agg["message_count"] == 3

    def test_empty_aggregation(self):
        agg = aggregate_states([])
        assert agg["mood"] is None
        assert agg["energy"] is None

    def test_themes_aggregated(self):
        states = [
            infer_state("Work is stressing me out"),
            infer_state("My job is terrible"),
            infer_state("I need to exercise more"),
        ]
        agg = aggregate_states(states)
        assert "work" in agg["themes"]
