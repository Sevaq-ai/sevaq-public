from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.models.common import ReasoningMode
from app.orchestration.control_metrics import compute_control_metrics


def test_fast_mode_produces_low_compute() -> None:
    metrics = compute_control_metrics(ReasoningMode.FAST, risk_score=0.2)
    assert metrics.compute_intensity == "low"


def test_deep_mode_produces_medium_compute() -> None:
    metrics = compute_control_metrics(ReasoningMode.DEEP, risk_score=0.5)
    assert metrics.compute_intensity == "medium"


def test_verified_mode_produces_high_compute() -> None:
    metrics = compute_control_metrics(ReasoningMode.VERIFIED, risk_score=0.9)
    assert metrics.compute_intensity == "high"


def test_high_risk_fast_route_flags_underallocation() -> None:
    metrics = compute_control_metrics(ReasoningMode.FAST, risk_score=0.92)
    assert metrics.potential_underallocation_flag is True


def test_low_risk_verified_route_flags_overallocation() -> None:
    metrics = compute_control_metrics(ReasoningMode.VERIFIED, risk_score=0.1)
    assert metrics.potential_overallocation_flag is True
