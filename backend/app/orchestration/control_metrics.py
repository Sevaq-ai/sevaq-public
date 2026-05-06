from __future__ import annotations

from pydantic import BaseModel

from app.models.common import ReasoningMode


class ControlMetrics(BaseModel):
    estimated_cost_units: float
    estimated_latency_ms: int
    compute_intensity: str
    allocation_reason: str
    potential_overallocation_flag: bool
    potential_underallocation_flag: bool
    risk_adjusted_allocation_note: str


def compute_control_metrics(
    mode: ReasoningMode,
    risk_score: float,
    estimated_cost_units: float | None = None,
    estimated_latency_ms: int | None = None,
) -> ControlMetrics:
    defaults = {
        ReasoningMode.FAST: (1.0, 120, "low", "fast mode selected for low-latency execution"),
        ReasoningMode.DEEP: (3.0, 480, "medium", "deep mode selected for structured multi-step reasoning"),
        ReasoningMode.VERIFIED: (
            5.0,
            900,
            "high",
            "verified mode selected for cautious high-assurance posture",
        ),
    }
    base_cost, base_latency, intensity, reason = defaults[mode]
    cost = estimated_cost_units if estimated_cost_units is not None else base_cost
    latency = estimated_latency_ms if estimated_latency_ms is not None else base_latency

    underallocation = mode == ReasoningMode.FAST and risk_score >= 0.8
    overallocation = mode == ReasoningMode.VERIFIED and risk_score < 0.3
    if underallocation:
        note = "High-risk prompt on fast mode may need stronger reasoning depth."
    elif overallocation:
        note = "Low-risk prompt on verified mode may be over-provisioned."
    else:
        note = "Compute allocation is heuristically aligned with routed mode and risk."

    return ControlMetrics(
        estimated_cost_units=round(float(cost), 4),
        estimated_latency_ms=int(latency),
        compute_intensity=intensity,
        allocation_reason=reason,
        potential_overallocation_flag=overallocation,
        potential_underallocation_flag=underallocation,
        risk_adjusted_allocation_note=note,
    )
