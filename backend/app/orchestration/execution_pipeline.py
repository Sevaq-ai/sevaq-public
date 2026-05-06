from __future__ import annotations

import logging
import uuid

from app.interfaces.execution import ExecutionRequest, ExecutionResponse
from app.interfaces.plugin_loader import load_probe, load_routing_policy
from app.interfaces.routing import RoutingContext
from app.interfaces.verification import VerificationRequest
from app.models.common import ImplementationSource, ReasoningMode
from app.models.trace import ProbeTrace, RoutingTrace, SevaQTrace, ValidationTrace
from app.orchestration.control_metrics import compute_control_metrics
from app.orchestration.reasoning_profiles import get_reasoning_profile
from app.providers.provider_factory import create_execution_provider
from app.telemetry.ledger import hash_prompt, write_event
from app.verification.simple_verifier import SimpleVerifier

logger = logging.getLogger(__name__)


class ExecutionPipeline:
    def __init__(self) -> None:
        self._provider = create_execution_provider()
        self._verifier = SimpleVerifier()

    def run(self, request: ExecutionRequest) -> ExecutionResponse:
        request_id = str(uuid.uuid4())
        prompt_hash = hash_prompt(request.prompt)
        try:
            probe = load_probe()
            routing_policy = load_routing_policy()

            initial_mode = request.requested_mode.value if request.requested_mode else ReasoningMode.FAST.value
            probe_result = probe.assess(request.prompt, initial_mode)
            routing_context = RoutingContext(
                prompt=request.prompt,
                probe_result=probe_result,
                user_tier=request.user_tier,
                require_citations=request.require_citations,
            )
            decision = routing_policy.decide(routing_context)
            profile = get_reasoning_profile(decision.mode)
            provider_response = self._provider.execute(request, decision.mode, profile)
            risk_category = self._risk_category(
                probe_result.detected_risk_keywords, probe_result.score
            )
            verification_result = self._verifier.verify(
                VerificationRequest(
                    reasoning_mode=decision.mode,
                    risk_category=risk_category,
                    response_text=provider_response.simulated_response,
                    prompt_signals=probe_result.detected_risk_keywords
                    + probe_result.verification_signals,
                )
            )
            validation_trace = ValidationTrace(
                validation_status=verification_result.validation_status,
                confidence_score=verification_result.confidence_score,
                validation_notes=verification_result.validation_notes,
                needs_external_verification=verification_result.needs_external_verification,
                risk_flags=verification_result.risk_flags,
                recommended_user_message=verification_result.recommended_user_message,
                verifier_type=verification_result.verifier_type,
                verification_score=verification_result.verification_score,
                grounding_risk=verification_result.grounding_risk,
                uncertainty_level=verification_result.uncertainty_level,
                needs_external_sources=verification_result.needs_external_sources,
                verifier_notes=verification_result.verifier_notes,
                user_facing_summary=verification_result.user_facing_summary,
            )
            control_metrics = compute_control_metrics(
                mode=decision.mode,
                risk_score=probe_result.score,
                estimated_cost_units=provider_response.estimated_cost_units,
                estimated_latency_ms=provider_response.estimated_latency_ms,
            )

            implementation_source = self._resolve_implementation_source(
                probe_source=probe_result.source,
                routing_source=decision.source,
            )
            trace = SevaQTrace(
                probe_summary=ProbeTrace(
                    score=probe_result.score,
                    detected_domain=probe_result.detected_domain,
                    detected_intent=probe_result.detected_intent,
                    detected_risk_keywords=probe_result.detected_risk_keywords,
                    detected_complexity_keywords=probe_result.detected_complexity_keywords,
                    verification_signals=probe_result.verification_signals,
                    notes=probe_result.notes,
                ),
                routing_summary=RoutingTrace(
                    selected_mode=decision.selected_mode.value,
                    selected_profile=decision.selected_profile,
                    routing_reason=decision.routing_reason,
                    confidence_level=decision.confidence_level,
                    escalation_reason=decision.escalation_reason,
                ),
                reasoning_profile_summary=(
                    f"{profile.profile_name} profile with style={profile.reasoning_style}, "
                    f"caution={profile.caution_level}"
                ),
                provider_selection_summary=(
                    f"Provider {provider_response.provider_name} selected for mode={decision.mode.value}"
                ),
                validation_summary=validation_trace,
                verifier_summary=validation_trace,
                control_metrics_summary=(
                    f"compute={control_metrics.compute_intensity}, cost={control_metrics.estimated_cost_units}, "
                    f"latency_ms={control_metrics.estimated_latency_ms}, "
                    f"over={control_metrics.potential_overallocation_flag}, "
                    f"under={control_metrics.potential_underallocation_flag}"
                ),
                telemetry_summary=(
                    f"Telemetry logs prompt hash only with mode={decision.mode.value} "
                    f"and profile={profile.profile_name}"
                ),
            )
            reasoning_summary = (
                f"Probe detected domain '{probe_result.detected_domain}' with risk score "
                f"{probe_result.score:.2f}; routing selected {decision.mode.value} "
                f"because {decision.routing_reason}."
            )
            response = provider_response.model_copy(
                update={
                    "reasoning_mode": decision.mode,
                    "reasoning_profile": profile.profile_name,
                    "reasoning_style": profile.reasoning_style,
                    "caution_level": profile.caution_level,
                    "verification_behavior": profile.verification_behavior,
                    "implementation_source": implementation_source,
                    "risk_score": probe_result.score,
                    "complexity_score": self._complexity_score(request.prompt, decision.mode),
                    "routing_reason": decision.routing_reason,
                    "verification_result": verification_result,
                    "estimated_cost_units": control_metrics.estimated_cost_units,
                    "estimated_latency_ms": control_metrics.estimated_latency_ms,
                    "control_metrics": control_metrics,
                    "reasoning_summary": reasoning_summary,
                    "trace": trace,
                }
            )
            event = {
                "request_id": request_id,
                "prompt_hash": prompt_hash,
                "reasoning_mode": response.reasoning_mode.value,
                "reasoning_profile": response.reasoning_profile,
                "reasoning_style": response.reasoning_style,
                "caution_level": response.caution_level,
                "verification_behavior": response.verification_behavior,
                "trace_confidence_level": decision.confidence_level,
                "trace_escalated": bool(decision.escalation_reason),
                "validation_status": verification_result.validation_status,
                "confidence_score": verification_result.confidence_score,
                "needs_external_verification": verification_result.needs_external_verification,
                "verifier_type": verification_result.verifier_type,
                "verification_score": verification_result.verification_score,
                "grounding_risk": verification_result.grounding_risk,
                "uncertainty_level": verification_result.uncertainty_level,
                "needs_external_sources": verification_result.needs_external_sources,
                "compute_intensity": control_metrics.compute_intensity,
                "potential_overallocation_flag": control_metrics.potential_overallocation_flag,
                "potential_underallocation_flag": control_metrics.potential_underallocation_flag,
                "implementation_source": response.implementation_source.value,
                "provider_name": response.provider_name,
                "risk_score": response.risk_score,
                "complexity_score": response.complexity_score,
                "routing_reason": response.routing_reason,
                "estimated_cost_units": response.estimated_cost_units,
                "estimated_latency_ms": response.estimated_latency_ms,
                "success_flag": True,
                "error_message": None,
            }
            telemetry_logged, telemetry_error = self._write_telemetry_best_effort(event)
            return response.model_copy(
                update={"telemetry_logged": telemetry_logged, "telemetry_error": telemetry_error}
            )
        except Exception as exc:
            self._write_telemetry_best_effort(
                {
                    "request_id": request_id,
                    "prompt_hash": prompt_hash,
                    "reasoning_mode": ReasoningMode.FAST.value,
                    "reasoning_profile": "fast",
                    "reasoning_style": "brief-direct",
                    "caution_level": "low",
                    "verification_behavior": "not_applicable",
                    "trace_confidence_level": "low",
                    "trace_escalated": False,
                    "validation_status": "fail",
                    "confidence_score": 0.0,
                    "needs_external_verification": True,
                    "verifier_type": "heuristic",
                    "verification_score": 0.0,
                    "grounding_risk": "high",
                    "uncertainty_level": "high",
                    "needs_external_sources": True,
                    "compute_intensity": "low",
                    "potential_overallocation_flag": False,
                    "potential_underallocation_flag": True,
                    "implementation_source": ImplementationSource.PUBLIC.value,
                    "provider_name": "unresolved",
                    "risk_score": 0.0,
                    "complexity_score": 0.0,
                    "routing_reason": "execution-failed",
                    "estimated_cost_units": 0.0,
                    "estimated_latency_ms": 0,
                    "success_flag": False,
                    "error_message": str(exc),
                }
            )
            raise

    @staticmethod
    def _resolve_implementation_source(
        probe_source: ImplementationSource, routing_source: ImplementationSource
    ) -> ImplementationSource:
        if ImplementationSource.PRIVATE in (probe_source, routing_source):
            return ImplementationSource.PRIVATE
        return ImplementationSource.PUBLIC

    @staticmethod
    def _complexity_score(prompt: str, mode: ReasoningMode) -> float:
        length_component = min(0.6, len(prompt.split()) / 30.0)
        mode_bonus = {
            ReasoningMode.FAST: 0.1,
            ReasoningMode.DEEP: 0.25,
            ReasoningMode.VERIFIED: 0.35,
        }[mode]
        return min(1.0, round(length_component + mode_bonus, 3))

    @staticmethod
    def _risk_category(risk_keywords: list[str], score: float) -> str:
        if risk_keywords or score >= 0.8:
            return "high"
        if score >= 0.45:
            return "medium"
        return "low"

    @staticmethod
    def _write_telemetry_best_effort(event: dict) -> tuple[bool, str | None]:
        try:
            write_event(event)
            return True, None
        except Exception as telemetry_exc:  # pragma: no cover
            logger.exception("Telemetry write failed: %s", telemetry_exc)
            return False, str(telemetry_exc)
