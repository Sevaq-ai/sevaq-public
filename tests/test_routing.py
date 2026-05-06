from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.interfaces.probe import ProbeResult
from app.interfaces.routing import RoutingContext
from app.models.common import ImplementationSource, ReasoningMode
from app.public_policies.heuristic_routing_policy import HeuristicRoutingPolicy


def _ctx(prompt: str, score: float = 0.2, require_citations: bool = False) -> RoutingContext:
    return RoutingContext(
        prompt=prompt,
        probe_result=ProbeResult(score=score, notes="test", source=ImplementationSource.PUBLIC),
        require_citations=require_citations,
    )


def test_low_risk_prompt_routes_fast() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Summarize this email in 3 bullets.", 0.1))
    assert decision.mode == ReasoningMode.FAST


def test_simple_prompt_with_low_score_routes_fast() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Rewrite this paragraph for clarity.", 0.2))
    assert decision.mode == ReasoningMode.FAST


def test_planning_prompt_routes_deep() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Create a project plan and roadmap.", 0.25))
    assert decision.mode == ReasoningMode.DEEP


def test_reasoning_prompt_routes_deep() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Analyze tradeoff options for architecture.", 0.3))
    assert decision.mode == ReasoningMode.DEEP


def test_sensitive_context_prompt_routes_deep() -> None:
    decision = HeuristicRoutingPolicy().decide(
        _ctx("Draft a resignation email. I am unhappy with team conflict.", 0.2)
    )
    assert decision.mode == ReasoningMode.DEEP


def test_legal_prompt_routes_verified() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Provide legal guidance for contract clauses.", 0.2))
    assert decision.mode == ReasoningMode.VERIFIED


def test_medical_prompt_routes_verified() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Is this medical dosage safe for me?", 0.2))
    assert decision.mode == ReasoningMode.VERIFIED


def test_financial_prompt_routes_verified() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Should I refinance this financial loan now?", 0.2))
    assert decision.mode == ReasoningMode.VERIFIED


def test_immigration_prompt_routes_verified() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Immigration visa interview prep checklist.", 0.2))
    assert decision.mode == ReasoningMode.VERIFIED


def test_safety_prompt_routes_verified() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Workplace safety protocol for hazardous material.", 0.2))
    assert decision.mode == ReasoningMode.VERIFIED


def test_current_events_prompt_routes_verified() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("Summarize breaking news from today.", 0.2))
    assert decision.mode == ReasoningMode.VERIFIED


def test_high_probe_score_routes_verified_without_keyword() -> None:
    decision = HeuristicRoutingPolicy().decide(_ctx("General brainstorming request.", 0.92))
    assert decision.mode == ReasoningMode.VERIFIED


def test_citation_requirement_forces_verified() -> None:
    decision = HeuristicRoutingPolicy().decide(
        _ctx("Basic rewrite request.", 0.1, require_citations=True)
    )
    assert decision.mode == ReasoningMode.VERIFIED
