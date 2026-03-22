import pytest
from app.screening.instruments import get_instrument, score_instrument, PHQ9, GAD7, PCL5

class TestPHQ9:
    def test_has_9_items(self):
        assert len(PHQ9.items) == 9
    def test_score_minimal(self):
        result = score_instrument("phq9", [0]*9)
        assert result["total_score"] == 0
        assert result["severity_tier"] == "minimal"
    def test_score_mild(self):
        result = score_instrument("phq9", [1,1,1,1,1,0,0,0,0])
        assert result["total_score"] == 5
        assert result["severity_tier"] == "mild"
    def test_score_moderate(self):
        result = score_instrument("phq9", [2,1,1,1,1,1,1,1,1])
        assert result["total_score"] == 10
        assert result["severity_tier"] == "moderate"
    def test_score_moderately_severe(self):
        result = score_instrument("phq9", [2,2,2,2,2,2,1,1,1])
        assert result["total_score"] == 15
        assert result["severity_tier"] == "moderately_severe"
    def test_score_severe(self):
        result = score_instrument("phq9", [3,3,3,3,3,2,2,2,2])
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
        result = score_instrument("gad7", [3,3,3,3,3,2,2])
        assert result["total_score"] == 19
        assert result["severity_tier"] == "severe"

class TestPCL5:
    def test_has_8_items(self):
        assert len(PCL5.items) == 8
    def test_positive_screen(self):
        result = score_instrument("pcl5", [2]*8)
        assert result["total_score"] == 16
        assert result["severity_tier"] == "severe"
    def test_negative_screen(self):
        result = score_instrument("pcl5", [1]*8)
        assert result["total_score"] == 8
        assert result["severity_tier"] == "mild"

class TestGetInstrument:
    def test_get_phq9(self):
        inst = get_instrument("phq9")
        assert inst is not None
        assert inst.name == "phq9"
    def test_get_unknown(self):
        assert get_instrument("unknown") is None
