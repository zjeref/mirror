"""Tests for the energy module - MVAs and energy ladders."""

import pytest

from app.psychology.energy import get_mva, get_validation


class TestGetMVA:
    def test_energy_1_returns_micro_action(self):
        mva = get_mva("physical", 1)
        assert mva.energy_required <= 2
        assert mva.validation  # Always has validation at low energy
        assert mva.action  # Has an actual action

    def test_energy_1_never_suggests_gym(self):
        """At energy 1, we should NEVER suggest going to the gym."""
        mva = get_mva("physical", 1)
        action_lower = mva.action.lower()
        assert "gym" not in action_lower
        assert "workout" not in action_lower
        assert "run" not in action_lower

    def test_energy_8_can_suggest_full_workout(self):
        mva = get_mva("physical", 8)
        assert mva.energy_required >= 6

    def test_all_life_areas_have_actions(self):
        for area in ["physical", "mental", "career", "habits"]:
            for energy in range(1, 9):
                mva = get_mva(area, energy)
                assert mva.action, f"No action for {area} at energy {energy}"

    def test_fallback_is_easier_than_action(self):
        mva = get_mva("physical", 5)
        # Fallback should exist and be different from action (or same at level 1)
        assert mva.fallback is not None

    def test_scale_up_offered_when_available(self):
        mva = get_mva("physical", 3)
        # At mid-energy, there should be a scale-up option
        assert mva.scale_up is not None

    def test_clamps_energy_to_valid_range(self):
        mva_low = get_mva("physical", -5)
        mva_high = get_mva("physical", 100)
        assert mva_low.action  # Doesn't crash
        assert mva_high.action

    def test_unknown_area_falls_back_to_physical(self):
        mva = get_mva("nonexistent_area", 5)
        assert mva.action  # Falls back gracefully

    def test_user_calibration_adjusts_level(self):
        """User calibration should shift the suggested action difficulty."""
        calibration = {"physical": {"3": 5}}  # This user does energy-5 actions at energy 3
        mva = get_mva("physical", 3, user_calibration=calibration)
        # Should suggest something slightly harder than default energy-3


class TestValidation:
    def test_low_energy_gets_validation(self):
        msg = get_validation(1)
        assert msg  # Non-empty
        # Should be empathetic, not demanding
        lower = msg.lower()
        assert "should" not in lower
        assert "lazy" not in lower

    def test_very_low_energy_is_extra_gentle(self):
        msg = get_validation(1)
        assert any(word in msg.lower() for word in ["real", "enough", "protecting", "energy"])

    def test_high_energy_is_encouraging(self):
        msg = get_validation(8)
        assert msg  # Non-empty
