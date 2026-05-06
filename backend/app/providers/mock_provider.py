from __future__ import annotations

from app.interfaces.execution import BaseExecutionProvider, ExecutionRequest, ExecutionResponse
from app.models.common import ImplementationSource, ReasoningMode
from app.orchestration.reasoning_profiles import ReasoningProfile


class MockExecutionProvider(BaseExecutionProvider):
    """Deterministic provider used for local execution pipeline tests."""

    _METRICS_BY_MODE = {
        ReasoningMode.FAST: (1.0, 120, "Fast path: concise answer generated."),
        ReasoningMode.DEEP: (3.0, 480, "Deep path: multi-step reasoning simulated."),
        ReasoningMode.VERIFIED: (5.0, 900, "Verified path: higher-assurance response simulated."),
    }

    def execute(
        self, request: ExecutionRequest, mode: ReasoningMode, profile: ReasoningProfile
    ) -> ExecutionResponse:
        cost, latency, response_prefix = self._METRICS_BY_MODE[mode]
        snippet = request.prompt.strip().replace("\n", " ")[:60]

        return ExecutionResponse(
            reasoning_mode=mode,
            reasoning_profile=profile.profile_name,
            reasoning_style=profile.reasoning_style,
            caution_level=profile.caution_level,
            verification_behavior=profile.verification_behavior,
            implementation_source=ImplementationSource.MOCK,
            provider_name="mock-provider",
            simulated_response=f"{response_prefix} prompt='{snippet}'",
            estimated_cost_units=cost,
            estimated_latency_ms=latency,
            risk_score=0.0,
            complexity_score=0.0,
            routing_reason="provider-executed",
            demo_mode="mock",
        )
