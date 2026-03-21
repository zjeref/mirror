"""Tests for the tiny habits module."""

import pytest

from app.psychology.tiny_habits import (
    COMMON_ANCHORS,
    create_recipe,
    get_templates_for_area,
    scale_to_energy,
    suggest_anchor,
)


class TestTemplates:
    def test_all_areas_have_templates(self):
        for area in ["physical", "mental", "career", "habits"]:
            templates = get_templates_for_area(area)
            assert len(templates) > 0, f"No templates for {area}"

    def test_templates_have_required_fields(self):
        for area in ["physical", "mental", "career"]:
            for template in get_templates_for_area(area):
                assert "name" in template
                assert "tiny" in template
                assert "scales" in template
                assert "full" in template
                assert "suggested_anchor" in template
                assert "celebration" in template

    def test_scales_start_tiny_end_full(self):
        templates = get_templates_for_area("physical")
        for t in templates:
            # First scale should be the tiny version
            assert t["scales"][0] == t["tiny"]


class TestRecipeCreation:
    def test_create_from_template(self):
        templates = get_templates_for_area("physical")
        recipe = create_recipe(templates[0])
        assert recipe.tiny_behavior == templates[0]["tiny"]
        assert recipe.full_behavior == templates[0]["full"]
        assert recipe.anchor == templates[0]["suggested_anchor"]

    def test_custom_anchor_overrides_default(self):
        templates = get_templates_for_area("physical")
        recipe = create_recipe(templates[0], anchor="After my morning alarm")
        assert recipe.anchor == "After my morning alarm"

    def test_custom_celebration(self):
        templates = get_templates_for_area("mental")
        recipe = create_recipe(templates[0], celebration="Do a little dance")
        assert recipe.celebration == "Do a little dance"


class TestScaleToEnergy:
    def test_energy_1_returns_tiniest(self):
        templates = get_templates_for_area("physical")
        recipe = create_recipe(templates[0])
        result = scale_to_energy(recipe, 1)
        assert result == recipe.scale_levels[0]

    def test_energy_2_returns_tiniest(self):
        templates = get_templates_for_area("physical")
        recipe = create_recipe(templates[0])
        result = scale_to_energy(recipe, 2)
        assert result == recipe.scale_levels[0]

    def test_energy_10_returns_fullest(self):
        templates = get_templates_for_area("physical")
        recipe = create_recipe(templates[0])
        result = scale_to_energy(recipe, 10)
        assert result == recipe.scale_levels[-1]

    def test_energy_scales_monotonically(self):
        """Higher energy should never return an easier version."""
        templates = get_templates_for_area("physical")
        recipe = create_recipe(templates[0])

        prev_idx = 0
        for energy in range(1, 11):
            result = scale_to_energy(recipe, energy)
            idx = recipe.scale_levels.index(result)
            assert idx >= prev_idx, f"Energy {energy} returned easier version than energy {energy-1}"
            prev_idx = idx


class TestAnchorSuggestions:
    def test_common_anchors_exist(self):
        assert len(COMMON_ANCHORS) > 0

    def test_morning_anchors(self):
        anchors = suggest_anchor("physical", "morning")
        assert all("morning" in a.lower() or "wake" in a.lower() or "brush" in a.lower()
                    for a in anchors)

    def test_evening_anchors(self):
        anchors = suggest_anchor("physical", "evening")
        assert any("evening" in a.lower() or "dinner" in a.lower() or "bed" in a.lower()
                    for a in anchors)
