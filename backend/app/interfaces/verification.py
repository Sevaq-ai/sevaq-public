from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import ReasoningMode


class VerificationRequest(BaseModel):
    reasoning_mode: ReasoningMode
    risk_category: str
    response_text: str
    prompt_signals: list[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    # Legacy validation fields kept for backward compatibility.
    validation_status: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    needs_external_verification: bool
    validation_notes: str
    risk_flags: list[str] = Field(default_factory=list)
    recommended_user_message: str
    # Verifier-agent-ready fields.
    verifier_type: Literal["heuristic", "llm", "retrieval", "hybrid"] = "heuristic"
    verification_score: float = Field(ge=0.0, le=1.0, default=0.0)
    grounding_risk: Literal["low", "medium", "high"] = "medium"
    uncertainty_level: Literal["low", "medium", "high"] = "medium"
    needs_external_sources: bool = False
    verifier_notes: list[str] = Field(default_factory=list)
    user_facing_summary: str = ""


class BaseVerifier(ABC):
    @abstractmethod
    def verify(self, request: VerificationRequest) -> VerificationResult:
        """Return public-safe validation signal for response posture."""
        raise NotImplementedError
