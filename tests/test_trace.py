from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.interfaces.execution import ExecutionRequest
from app.models.trace import ProbeTrace, RoutingTrace, SevaQTrace, ValidationTrace
from app.orchestration.execution_pipeline import ExecutionPipeline
from app.providers.provider_factory import PROVIDER_ENV
from dashboard.streamlit_app import _trace_sections


def test_trace_objects_serialize_correctly() -> None:
    trace = SevaQTrace(
        probe_summary=ProbeTrace(
            score=0.5,
            detected_domain="general",
            detected_intent="analysis",
            detected_risk_keywords=["medical"],
            detected_complexity_keywords=["tradeoff"],
            verification_signals=["citations"],
            notes="demo",
        ),
        routing_summary=RoutingTrace(
            selected_mode="verified",
            selected_profile="verified",
            routing_reason="high-stakes domain keyword",
            confidence_level="high",
            escalation_reason="high-stakes domain keyword",
        ),
        reasoning_profile_summary="verified profile summary",
        provider_selection_summary="mock provider selected",
        validation_summary=ValidationTrace(
            validation_status="warning",
            confidence_score=0.4,
            validation_notes="external verification recommended",
            needs_external_verification=True,
            verifier_type="heuristic",
            verification_score=0.5,
            grounding_risk="high",
            uncertainty_level="high",
            needs_external_sources=True,
            verifier_notes=["heuristic verifier"],
            user_facing_summary="Heuristic verifier signal",
        ),
        control_metrics_summary="compute=high cost=5.0",
        telemetry_summary="hash-only telemetry",
    )
    payload = trace.model_dump()
    assert payload["routing_summary"]["selected_mode"] == "verified"
    assert payload["validation_summary"]["needs_external_verification"] is True
    assert payload["validation_summary"]["verification_score"] == 0.5


def test_execution_pipeline_returns_trace(monkeypatch) -> None:
    monkeypatch.setenv(PROVIDER_ENV, "mock")
    response = ExecutionPipeline().run(ExecutionRequest(prompt="Create a roadmap and tradeoff analysis."))
    assert response.trace is not None
    assert response.reasoning_summary
    assert response.trace.routing_summary.selected_mode in {"fast", "deep", "verified"}


def test_verified_prompts_include_escalation_reason(monkeypatch) -> None:
    monkeypatch.setenv(PROVIDER_ENV, "mock")
    response = ExecutionPipeline().run(ExecutionRequest(prompt="Need legal guidance for contract clauses."))
    assert response.reasoning_mode.value == "verified"
    assert response.trace is not None
    assert response.trace.routing_summary.escalation_reason


def test_dashboard_can_render_trace_fields() -> None:
    sections = _trace_sections(
        {
            "probe_summary": {
                "detected_domain": "general",
                "detected_intent": "direct_answer",
                "detected_risk_keywords": [],
                "detected_complexity_keywords": ["plan"],
                "verification_signals": [],
            },
            "routing_summary": {
                "selected_mode": "deep",
                "selected_profile": "deep",
                "routing_reason": "planning/reasoning keyword",
                "confidence_level": "medium",
                "escalation_reason": None,
            },
            "reasoning_profile_summary": "deep profile summary",
            "validation_summary": {"validation_status": "not_applicable"},
            "provider_selection_summary": "mock provider",
        }
    )
    assert sections["probe_signals"]["detected_intent"] == "direct_answer"
    assert sections["routing_explanation"]["selected_profile"] == "deep"
