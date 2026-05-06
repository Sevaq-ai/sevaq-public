from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.interfaces.execution import ExecutionRequest, ExecutionResponse
from app.interfaces.plugin_loader import load_probe, load_routing_policy
from app.interfaces.routing import RoutingContext
from app.models.common import ImplementationSource, ReasoningMode
from app.providers.provider_factory import create_execution_provider
from app.orchestration.execution_pipeline import ExecutionPipeline
from app.orchestration.reasoning_profiles import get_reasoning_profile
from app.telemetry.ledger import read_recent_events

router = APIRouter()


class RouteRequest(BaseModel):
    prompt: str = Field(min_length=1)
    user_tier: str = "standard"
    require_citations: bool = False
    requested_mode: ReasoningMode | None = None


class RouteResponse(BaseModel):
    reasoning_mode: ReasoningMode
    reasoning_profile: str
    reasoning_style: str
    caution_level: str
    verification_behavior: str
    routing_reason: str
    confidence_level: str
    escalation_reason: str | None = None
    risk_score: float
    complexity_score: float
    implementation_source: ImplementationSource


class TelemetryEventResponse(BaseModel):
    id: int
    request_id: str
    timestamp: datetime
    prompt_hash: str
    reasoning_mode: str
    reasoning_profile: str
    reasoning_style: str
    caution_level: str
    verification_behavior: str
    trace_confidence_level: str
    trace_escalated: bool
    validation_status: str
    confidence_score: float
    needs_external_verification: bool
    verifier_type: str
    verification_score: float
    grounding_risk: str
    uncertainty_level: str
    needs_external_sources: bool
    compute_intensity: str
    potential_overallocation_flag: bool
    potential_underallocation_flag: bool
    implementation_source: str
    provider_name: str
    risk_score: float
    complexity_score: float
    routing_reason: str
    estimated_cost_units: float
    estimated_latency_ms: int
    success_flag: bool
    error_message: str | None


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/v1/route", response_model=RouteResponse)
def route_only(request: RouteRequest) -> RouteResponse:
    probe = load_probe()
    policy = load_routing_policy()
    initial_mode = request.requested_mode.value if request.requested_mode else ReasoningMode.FAST.value
    probe_result = probe.assess(request.prompt, initial_mode)
    decision = policy.decide(
        RoutingContext(
            prompt=request.prompt,
            probe_result=probe_result,
            user_tier=request.user_tier,
            require_citations=request.require_citations,
        )
    )
    implementation_source = (
        ImplementationSource.PRIVATE
        if ImplementationSource.PRIVATE in (probe_result.source, decision.source)
        else ImplementationSource.PUBLIC
    )
    complexity_score = ExecutionPipeline._complexity_score(request.prompt, decision.mode)
    profile = get_reasoning_profile(decision.mode)
    return RouteResponse(
        reasoning_mode=decision.mode,
        reasoning_profile=profile.profile_name,
        reasoning_style=profile.reasoning_style,
        caution_level=profile.caution_level,
        verification_behavior=profile.verification_behavior,
        routing_reason=decision.routing_reason,
        confidence_level=decision.confidence_level,
        escalation_reason=decision.escalation_reason,
        risk_score=probe_result.score,
        complexity_score=complexity_score,
        implementation_source=implementation_source,
    )


@router.post("/v1/run", response_model=ExecutionResponse)
def run_execution(request: RouteRequest) -> ExecutionResponse:
    execution_request = ExecutionRequest(
        prompt=request.prompt,
        user_tier=request.user_tier,
        require_citations=request.require_citations,
        requested_mode=request.requested_mode,
    )
    return ExecutionPipeline().run(execution_request)


@router.post("/v1/run/direct", response_model=ExecutionResponse)
def run_direct_provider(request: RouteRequest) -> ExecutionResponse:
    mode = request.requested_mode or ReasoningMode.FAST
    profile = get_reasoning_profile(mode)
    provider = create_execution_provider()
    response = provider.execute(
        ExecutionRequest(
            prompt=request.prompt,
            user_tier=request.user_tier,
            require_citations=request.require_citations,
            requested_mode=mode,
        ),
        mode,
        profile,
    )
    return response.model_copy(
        update={
            "reasoning_mode": mode,
            "reasoning_profile": profile.profile_name,
            "reasoning_style": profile.reasoning_style,
            "caution_level": profile.caution_level,
            "verification_behavior": profile.verification_behavior,
            "implementation_source": ImplementationSource.PUBLIC,
            "routing_reason": "direct-provider-baseline",
            "reasoning_summary": "Direct provider baseline without SevaQ routing/probe/validation layers.",
            "trace": None,
            "verification_result": None,
            "control_metrics": None,
            "demo_mode": "direct",
            "provider_fallback_used": False,
            "fallback_reason": None,
        }
    )


@router.get("/v1/telemetry/recent", response_model=list[TelemetryEventResponse])
def telemetry_recent(limit: int = 50) -> list[TelemetryEventResponse]:
    events = read_recent_events(limit=limit)
    return [
        TelemetryEventResponse(
            id=e.id,
            request_id=e.request_id,
            timestamp=e.timestamp,
            prompt_hash=e.prompt_hash,
            reasoning_mode=e.reasoning_mode,
            reasoning_profile=e.reasoning_profile,
            reasoning_style=e.reasoning_style,
            caution_level=e.caution_level,
            verification_behavior=e.verification_behavior,
            trace_confidence_level=e.trace_confidence_level,
            trace_escalated=e.trace_escalated,
            validation_status=e.validation_status,
            confidence_score=e.confidence_score,
            needs_external_verification=e.needs_external_verification,
            verifier_type=e.verifier_type,
            verification_score=e.verification_score,
            grounding_risk=e.grounding_risk,
            uncertainty_level=e.uncertainty_level,
            needs_external_sources=e.needs_external_sources,
            compute_intensity=e.compute_intensity,
            potential_overallocation_flag=e.potential_overallocation_flag,
            potential_underallocation_flag=e.potential_underallocation_flag,
            implementation_source=e.implementation_source,
            provider_name=e.provider_name,
            risk_score=e.risk_score,
            complexity_score=e.complexity_score,
            routing_reason=e.routing_reason,
            estimated_cost_units=e.estimated_cost_units,
            estimated_latency_ms=e.estimated_latency_ms,
            success_flag=e.success_flag,
            error_message=e.error_message,
        )
        for e in events
    ]
