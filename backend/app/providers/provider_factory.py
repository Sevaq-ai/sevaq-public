from __future__ import annotations

import os

from app.interfaces.execution import BaseExecutionProvider, ExecutionRequest, ExecutionResponse
from app.models.common import ReasoningMode
from app.providers.mock_provider import MockExecutionProvider
from app.providers.openai_provider import (
    OpenAIExecutionProvider,
    OpenAIProviderConfigError,
    OpenAIProviderRuntimeGuardrailError,
)
from app.orchestration.reasoning_profiles import ReasoningProfile

PROVIDER_ENV = "SEVAQ_PROVIDER"
DEMO_MODE_ENV = "SEVAQ_DEMO_MODE"
OPENAI_FALLBACK_ENV = "SEVAQ_OPENAI_GUARDRAIL_FALLBACK_TO_MOCK"


class FallbackMockProvider(BaseExecutionProvider):
    def __init__(self, reason: str):
        self._reason = reason
        self._delegate = MockExecutionProvider()

    def execute(
        self, request: ExecutionRequest, mode: ReasoningMode, profile: ReasoningProfile
    ) -> ExecutionResponse:
        response = self._delegate.execute(request, mode, profile)
        return response.model_copy(
            update={
                "provider_name": f"mock-provider[fallback:{self._reason}]",
                "demo_mode": "live",
                "provider_fallback_used": True,
                "fallback_reason": self._reason,
                "live_model_used": None,
            }
        )


class GuardedOpenAIProvider(BaseExecutionProvider):
    def __init__(self, delegate: OpenAIExecutionProvider):
        self._delegate = delegate
        self._fallback = MockExecutionProvider()
        self._allow_fallback = os.getenv(OPENAI_FALLBACK_ENV, "true").lower() != "false"

    def execute(
        self, request: ExecutionRequest, mode: ReasoningMode, profile: ReasoningProfile
    ) -> ExecutionResponse:
        try:
            response = self._delegate.execute(request, mode, profile)
            return response.model_copy(
                update={
                    "demo_mode": "live",
                    "provider_fallback_used": False,
                    "fallback_reason": None,
                }
            )
        except OpenAIProviderRuntimeGuardrailError as exc:
            if not self._allow_fallback:
                raise
            fallback = self._fallback.execute(request, mode, profile)
            return fallback.model_copy(
                update={
                    "provider_name": f"mock-provider[fallback:{str(exc)}]",
                    "provider_fallback_used": True,
                    "fallback_reason": str(exc),
                    "demo_mode": "live",
                    "live_model_used": None,
                }
            )
        except Exception as exc:
            if not self._allow_fallback:
                raise
            fallback = self._fallback.execute(request, mode, profile)
            return fallback.model_copy(
                update={
                    "provider_name": f"mock-provider[fallback:{str(exc)}]",
                    "provider_fallback_used": True,
                    "fallback_reason": str(exc),
                    "demo_mode": "live",
                    "live_model_used": None,
                }
            )


def create_execution_provider() -> BaseExecutionProvider:
    demo_mode = os.getenv(DEMO_MODE_ENV, "").strip().lower()
    if not demo_mode:
        provider_name = os.getenv(PROVIDER_ENV, "mock").strip().lower()
        demo_mode = "live" if provider_name == "openai" else "mock"
    if demo_mode != "live":
        return MockExecutionProvider()
    try:
        return GuardedOpenAIProvider(OpenAIExecutionProvider.from_env())
    except OpenAIProviderConfigError as exc:
        return FallbackMockProvider(reason=str(exc))
