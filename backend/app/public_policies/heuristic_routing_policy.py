from __future__ import annotations

from app.interfaces.routing import BaseRoutingPolicy, RoutingContext, RoutingDecision
from app.models.common import ImplementationSource, ReasoningMode


class HeuristicRoutingPolicy(BaseRoutingPolicy):
    """Public-safe transparent routing heuristics (no proprietary math)."""

    _VERIFIED_KEYWORDS = {
        "legal",
        "medical",
        "finance",
        "financial",
        "immigration",
        "visa",
        "asylum",
        "safety",
        "self-harm",
        "harm",
        "breaking news",
        "current events",
        "today",
    }
    _DEEP_KEYWORDS = {
        "plan",
        "roadmap",
        "strategy",
        "multi-step",
        "tradeoff",
        "architecture",
        "reasoning",
        "analyze",
        "compare",
    }
    _CAUTION_DEEP_KEYWORDS = {
        "unhappy",
        "upset",
        "angry",
        "frustrated",
        "conflict",
        "hostile",
        "harassment",
        "retaliation",
        "toxic",
        "burnout",
        "fired",
        "termination",
    }

    def decide(self, context: RoutingContext) -> RoutingDecision:
        prompt = context.prompt.lower()

        if context.require_citations:
            return self._decision(ReasoningMode.VERIFIED, "citations requested")

        if any(token in prompt for token in self._VERIFIED_KEYWORDS):
            return self._decision(ReasoningMode.VERIFIED, "high-stakes domain keyword")

        if context.probe_result.score >= 0.8:
            return self._decision(ReasoningMode.VERIFIED, "high probe risk score")

        if any(token in prompt for token in self._DEEP_KEYWORDS):
            return self._decision(ReasoningMode.DEEP, "planning/reasoning keyword")

        if any(token in prompt for token in self._CAUTION_DEEP_KEYWORDS):
            return self._decision(ReasoningMode.DEEP, "sensitive personal context")

        if context.probe_result.score >= 0.45:
            return self._decision(ReasoningMode.DEEP, "moderate probe complexity")

        return self._decision(ReasoningMode.FAST, "low-risk prompt")

    @staticmethod
    def _decision(mode: ReasoningMode, rationale: str) -> RoutingDecision:
        confidence_level = "high" if mode == ReasoningMode.VERIFIED else ("medium" if mode == ReasoningMode.DEEP else "low")
        escalation_reason = rationale if mode == ReasoningMode.VERIFIED else None
        return RoutingDecision(
            mode=mode,
            selected_mode=mode,
            selected_profile=mode.value,
            rationale=rationale,
            routing_reason=rationale,
            confidence_level=confidence_level,
            escalation_reason=escalation_reason,
            source=ImplementationSource.PUBLIC,
        )
