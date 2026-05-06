from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.interfaces.execution import BaseExecutionProvider, ExecutionRequest, ExecutionResponse
from app.models.common import ImplementationSource, ReasoningMode
from app.orchestration.execution_pipeline import ExecutionPipeline
from app.orchestration.reasoning_profiles import get_reasoning_profile
from app.providers.provider_factory import DEMO_MODE_ENV, PROVIDER_ENV, GuardedOpenAIProvider, create_execution_provider
from app.providers.openai_provider import OpenAIProviderRuntimeGuardrailError
from app.telemetry.db import DB_PATH_ENV_VAR, get_engine
from app.telemetry.ledger import read_recent_events


class DummyOpenAIProvider(BaseExecutionProvider):
    def execute(self, request: ExecutionRequest, mode: ReasoningMode, profile) -> ExecutionResponse:
        return ExecutionResponse(
            reasoning_mode=mode,
            reasoning_profile=profile.profile_name,
            reasoning_style=profile.reasoning_style,
            caution_level=profile.caution_level,
            verification_behavior=profile.verification_behavior,
            implementation_source=ImplementationSource.MOCK,
            provider_name="openai-provider",
            simulated_response="dummy",
            estimated_cost_units=1.2,
            estimated_latency_ms=50,
            risk_score=0.0,
            complexity_score=0.0,
            routing_reason="provider-executed",
        )


def _set_test_db(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(tmp_path / "provider_factory.db"))
    get_engine.cache_clear()


def test_mock_provider_is_default(monkeypatch) -> None:
    monkeypatch.delenv(DEMO_MODE_ENV, raising=False)
    monkeypatch.delenv(PROVIDER_ENV, raising=False)
    provider = create_execution_provider()
    assert provider.__class__.__name__ == "MockExecutionProvider"


def test_live_mode_uses_openai_provider_when_configured(monkeypatch) -> None:
    from app.providers import provider_factory

    monkeypatch.setenv(DEMO_MODE_ENV, "live")
    monkeypatch.setattr(
        provider_factory.OpenAIExecutionProvider,
        "from_env",
        classmethod(lambda cls: DummyOpenAIProvider()),
    )
    provider = create_execution_provider()
    assert isinstance(provider, GuardedOpenAIProvider)
    sample = provider.execute(
        ExecutionRequest(prompt="hello"),
        ReasoningMode.FAST,
        get_reasoning_profile(ReasoningMode.FAST),
    )
    assert sample.reasoning_profile == "fast"
    assert sample.demo_mode == "live"


def test_live_mode_missing_api_key_falls_back_gracefully(monkeypatch, tmp_path) -> None:
    _set_test_db(monkeypatch, tmp_path)
    monkeypatch.setenv(DEMO_MODE_ENV, "live")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = ExecutionPipeline().run(ExecutionRequest(prompt="Summarize this short note."))
    assert response.provider_name.startswith("mock-provider[fallback:")
    assert response.provider_fallback_used is True
    assert response.fallback_reason
    assert response.demo_mode == "live"


def test_no_raw_prompt_is_stored_in_telemetry(monkeypatch, tmp_path) -> None:
    _set_test_db(monkeypatch, tmp_path)
    monkeypatch.setenv(PROVIDER_ENV, "mock")
    prompt = "Sensitive user prompt content should not be stored"
    ExecutionPipeline().run(ExecutionRequest(prompt=prompt))

    events = read_recent_events(limit=1)
    assert len(events) == 1
    assert prompt not in events[0].prompt_hash
    assert not hasattr(events[0], "prompt")
    assert events[0].reasoning_profile in {"fast", "deep", "verified"}


def test_openai_guardrail_failure_falls_back_gracefully() -> None:
    class GuardrailFailingProvider(BaseExecutionProvider):
        def execute(self, request: ExecutionRequest, mode: ReasoningMode, profile) -> ExecutionResponse:
            raise OpenAIProviderRuntimeGuardrailError("Prompt exceeds max length")

    guarded = GuardedOpenAIProvider(GuardrailFailingProvider())  # type: ignore[arg-type]
    result = guarded.execute(
        ExecutionRequest(prompt="x"),
        ReasoningMode.FAST,
        get_reasoning_profile(ReasoningMode.FAST),
    )
    assert result.provider_name.startswith("mock-provider[fallback:")
    assert result.provider_fallback_used is True
