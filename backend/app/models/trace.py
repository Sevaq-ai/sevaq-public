from __future__ import annotations

from pydantic import BaseModel, Field


class ProbeTrace(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    detected_domain: str
    detected_intent: str
    detected_risk_keywords: list[str]
    detected_complexity_keywords: list[str]
    verification_signals: list[str]
    notes: str


class RoutingTrace(BaseModel):
    selected_mode: str
    selected_profile: str
    routing_reason: str
    confidence_level: str
    escalation_reason: str | None = None


class ExecutionTrace(BaseModel):
    reasoning_profile: str
    provider_name: str
    implementation_source: str
    provider_behavior_summary: str


class ValidationTrace(BaseModel):
    validation_status: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_notes: str
    needs_external_verification: bool
    risk_flags: list[str] = Field(default_factory=list)
    recommended_user_message: str = ""
    verifier_type: str = "heuristic"
    verification_score: float = Field(ge=0.0, le=1.0, default=0.0)
    grounding_risk: str = "medium"
    uncertainty_level: str = "medium"
    needs_external_sources: bool = False
    verifier_notes: list[str] = Field(default_factory=list)
    user_facing_summary: str = ""


class SevaQTrace(BaseModel):
    probe_summary: ProbeTrace
    routing_summary: RoutingTrace
    reasoning_profile_summary: str
    provider_selection_summary: str
    validation_summary: ValidationTrace
    verifier_summary: ValidationTrace | None = None
    control_metrics_summary: str
    telemetry_summary: str
