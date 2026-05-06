from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.orchestration.control_metrics import ControlMetrics
from app.models.common import ImplementationSource, ReasoningMode
from app.models.trace import SevaQTrace
from app.interfaces.verification import VerificationResult
from app.orchestration.reasoning_profiles import ReasoningProfile


class ExecutionRequest(BaseModel):
    prompt: str = Field(min_length=1)
    user_tier: str = "standard"
    require_citations: bool = False
    requested_mode: ReasoningMode | None = None


class ExecutionResponse(BaseModel):
    reasoning_mode: ReasoningMode
    reasoning_profile: str
    reasoning_style: str
    caution_level: str
    verification_behavior: str
    implementation_source: ImplementationSource
    provider_name: str
    simulated_response: str
    estimated_cost_units: float = Field(ge=0.0)
    estimated_latency_ms: int = Field(ge=0)
    risk_score: float = Field(ge=0.0, le=1.0)
    complexity_score: float = Field(ge=0.0, le=1.0)
    routing_reason: str = Field(min_length=3)
    verification_result: VerificationResult | None = None
    control_metrics: ControlMetrics | None = None
    reasoning_summary: str = ""
    trace: SevaQTrace | None = None
    telemetry_logged: bool = True
    telemetry_error: str | None = None
    demo_mode: str = "mock"
    provider_fallback_used: bool = False
    fallback_reason: str | None = None
    live_model_used: str | None = None


class BaseExecutionProvider(ABC):
    @abstractmethod
    def execute(
        self, request: ExecutionRequest, mode: ReasoningMode, profile: ReasoningProfile
    ) -> ExecutionResponse:
        """Execute request for a selected reasoning mode."""
        raise NotImplementedError
