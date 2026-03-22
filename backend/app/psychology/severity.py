"""
SeverityRouter — translates instrument scores into clinical routing decisions.

Actions:
  monitor              — low severity, observe over time
  offer_protocol       — mild severity, optional structured protocol
  recommend_protocol   — moderate severity, protocol recommended
  protocol_plus_referral — moderately severe, protocol + professional referral
  referral_only        — severe or trauma-positive; no self-guided protocol

Referral resources are included in every routing decision at or above
moderately_severe, and always for PCL-5 positive screens.
"""
from dataclasses import dataclass
from typing import List

REFERRAL_RESOURCES = (
    "If you're in crisis right now, please reach out:\n"
    "  • 988 Suicide & Crisis Lifeline — call or text 988\n"
    "  • Crisis Text Line — text HOME to 741741\n"
    "  • SAMHSA National Helpline — 1-800-662-4357 (free, confidential, 24/7)\n"
    "\n"
    "To find a therapist:\n"
    "  • Psychology Today therapist finder — psychologytoday.com/us/therapists\n"
    "  • Open Path Collective (reduced-fee therapy) — openpathcollective.org"
)


@dataclass
class RoutingDecision:
    tier: str
    action: str
    eligible_protocols: List[str]
    referral_required: bool
    message: str = ""


# ---------------------------------------------------------------------------
# Per-instrument routing tables
# ---------------------------------------------------------------------------

# Each entry: (min_score, max_score, tier, action, protocols, referral_required)
_PHQ9_ROUTES = [
    (0,  4,  "minimal",            "monitor",               ["behavioral_activation"], False),
    (5,  9,  "mild",               "offer_protocol",        ["cbt_depression", "behavioral_activation"], False),
    (10, 14, "moderate",           "recommend_protocol",    ["cbt_depression", "behavioral_activation"], False),
    (15, 19, "moderately_severe",  "protocol_plus_referral",["cbt_depression", "behavioral_activation"], True),
    (20, 27, "severe",             "referral_only",         [], True),
]

_GAD7_ROUTES = [
    (0,  4,  "minimal",           "monitor",               [], False),
    (5,  9,  "mild",              "offer_protocol",        ["anxiety"], False),
    (10, 14, "moderate",          "recommend_protocol",    ["anxiety"], False),
    (15, 18, "moderately_severe", "protocol_plus_referral",["anxiety"], True),
    (19, 21, "severe",            "referral_only",         [], True),
]

# PCL-5: V1 — no self-guided protocol for any positive screen (≥16).
# Mild (8-15): monitor only (no active protocol yet for trauma in V1).
_PCL5_ROUTES = [
    (0,  7,  "minimal", "monitor",      [], False),
    (8,  15, "mild",    "monitor",      [], False),
    (16, 32, "severe",  "referral_only",[], True),
]

_INSTRUMENT_ROUTES = {
    "phq9": _PHQ9_ROUTES,
    "gad7": _GAD7_ROUTES,
    "pcl5": _PCL5_ROUTES,
}


class SeverityRouter:
    """Pure-static router: instrument + score → RoutingDecision."""

    @staticmethod
    def route(instrument: str, total_score: int) -> RoutingDecision:
        """
        Return a RoutingDecision for the given instrument and total score.

        Raises ValueError for unknown instruments.
        """
        routes = _INSTRUMENT_ROUTES.get(instrument.lower())
        if routes is None:
            raise ValueError(f"Unknown instrument: {instrument!r}")

        for min_s, max_s, tier, action, protocols, referral in routes:
            if min_s <= total_score <= max_s:
                message = REFERRAL_RESOURCES if referral else ""
                return RoutingDecision(
                    tier=tier,
                    action=action,
                    eligible_protocols=list(protocols),
                    referral_required=referral,
                    message=message,
                )

        # Score out of range — treat as severe
        return RoutingDecision(
            tier="severe",
            action="referral_only",
            eligible_protocols=[],
            referral_required=True,
            message=REFERRAL_RESOURCES,
        )
