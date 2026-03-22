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
        assert result.action == "monitor"
    def test_ba_eligible_from_phq9(self):
        result = SeverityRouter.route("phq9", 8)
        assert "behavioral_activation" in result.eligible_protocols
