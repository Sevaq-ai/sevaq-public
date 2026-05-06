from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.models.common import ImplementationSource


class ProbeResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    notes: str
    detected_domain: str = "general"
    detected_intent: str = "general_query"
    detected_risk_keywords: list[str] = Field(default_factory=list)
    detected_complexity_keywords: list[str] = Field(default_factory=list)
    verification_signals: list[str] = Field(default_factory=list)
    source: ImplementationSource = ImplementationSource.PUBLIC


class Probe(ABC):
    @abstractmethod
    def assess(self, prompt: str, mode: str) -> ProbeResult:
        """Assess prompt risk/complexity before execution."""
        raise NotImplementedError
