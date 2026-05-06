from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.models.common import ImplementationSource
from app.public_probes.heuristic_probe import HeuristicProbe


def test_probe_returns_public_source_and_valid_score() -> None:
    probe = HeuristicProbe()
    result = probe.assess("Please verify this with evidence and edge case analysis.", "verified")

    assert 0.0 <= result.score <= 1.0
    assert result.source == ImplementationSource.PUBLIC
    assert "mode=verified" in result.notes


def test_probe_scores_verified_higher_than_fast_for_same_prompt() -> None:
    probe = HeuristicProbe()
    prompt = "Need formal tradeoff discussion with citations."

    fast_result = probe.assess(prompt, "fast")
    verified_result = probe.assess(prompt, "verified")

    assert verified_result.score > fast_result.score


def test_sensitive_personal_prompt_increases_risk_and_domain() -> None:
    probe = HeuristicProbe()
    base = probe.assess("Draft a resignation email.", "fast")
    sensitive = probe.assess("Draft a resignation email. I am unhappy and frustrated.", "fast")
    assert sensitive.score > base.score
    assert sensitive.detected_domain == "sensitive_personal"
