from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.interfaces.probe import ProbeResult
from app.models.common import ImplementationSource, ReasoningMode


class RoutingContext(BaseModel):
    prompt: str
    probe_result: ProbeResult
    user_tier: str = "standard"
    require_citations: bool = False


class RoutingDecision(BaseModel):
    mode: ReasoningMode
    selected_mode: ReasoningMode
    selected_profile: str
    rationale: str = Field(min_length=3)
    routing_reason: str = Field(min_length=3)
    confidence_level: str = "medium"
    escalation_reason: str | None = None
    source: ImplementationSource = ImplementationSource.PUBLIC


class BaseRoutingPolicy(ABC):
    @abstractmethod
    def decide(self, context: RoutingContext) -> RoutingDecision:
        """Return a public-safe routing decision for the prompt."""
        raise NotImplementedError
