"""Tests for CBT cognitive distortion detection and reframing."""

import pytest

from app.psychology.cbt import detect_distortions, generate_reframe


class TestDistortionDetection:
    def test_detects_all_or_nothing(self):
        distortions = detect_distortions("I always fail at everything")
        names = [d.name for d in distortions]
        assert "all_or_nothing" in names

    def test_detects_catastrophizing(self):
        distortions = detect_distortions("This is a complete disaster, everything is ruined")
        names = [d.name for d in distortions]
        assert "catastrophizing" in names

    def test_detects_should_statements(self):
        distortions = detect_distortions("I should be more productive")
        names = [d.name for d in distortions]
        assert "should_statements" in names

    def test_detects_labeling(self):
        distortions = detect_distortions("I'm such a failure")
        names = [d.name for d in distortions]
        assert "labeling" in names

    def test_detects_mind_reading(self):
        distortions = detect_distortions("They think I'm incompetent")
        names = [d.name for d in distortions]
        assert "mind_reading" in names

    def test_detects_fortune_telling(self):
        distortions = detect_distortions("I know it will fail, there's no point trying")
        names = [d.name for d in distortions]
        assert "fortune_telling" in names

    def test_no_distortions_in_neutral_text(self):
        distortions = detect_distortions("I went for a walk today and it was nice")
        assert len(distortions) == 0

    def test_multiple_distortions_detected(self):
        text = "I always fail and everything is terrible and I should be better"
        distortions = detect_distortions(text)
        assert len(distortions) >= 2

    def test_confidence_increases_with_more_matches(self):
        weak = detect_distortions("I always do that")
        strong = detect_distortions("I always fail, I never succeed, every time it goes wrong")

        # The one with more pattern matches should have higher confidence
        weak_conf = max((d.confidence for d in weak if d.name == "all_or_nothing"), default=0)
        strong_conf = max((d.confidence for d in strong if d.name == "all_or_nothing"), default=0)
        assert strong_conf >= weak_conf

    def test_results_sorted_by_confidence(self):
        distortions = detect_distortions(
            "I always fail, this is a disaster, I should be better"
        )
        if len(distortions) >= 2:
            for i in range(len(distortions) - 1):
                assert distortions[i].confidence >= distortions[i + 1].confidence


class TestReframing:
    def test_generates_reframe_for_all_or_nothing(self):
        distortions = detect_distortions("I never do anything right")
        assert len(distortions) > 0
        reframe = generate_reframe("I never do anything right", distortions[0])
        assert reframe.original_thought == "I never do anything right"
        assert reframe.reframed_thought  # Not empty
        assert reframe.distortion  # Has distortion name

    def test_reframe_references_original_thought(self):
        thought = "I always mess everything up"
        distortions = detect_distortions(thought)
        reframe = generate_reframe(thought, distortions[0])
        # Reframe should reference the original or provide alternative
        assert len(reframe.reframed_thought) > 10

    def test_reframe_has_explanation(self):
        distortions = detect_distortions("I should be working harder")
        reframe = generate_reframe("I should be working harder", distortions[0])
        assert reframe.explanation  # Has explanation for the distortion
