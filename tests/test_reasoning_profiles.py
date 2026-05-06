from __future__ import annotations

import pathlib
import sys
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.interfaces.execution import ExecutionRequest
from app.models.common import ReasoningMode
from app.orchestration.execution_pipeline import ExecutionPipeline
from app.orchestration.reasoning_profiles import get_reasoning_profile
from app.providers.openai_provider import OpenAIExecutionProvider


def test_correct_profile_selected_for_each_mode() -> None:
    fast = get_reasoning_profile(ReasoningMode.FAST)
    deep = get_reasoning_profile(ReasoningMode.DEEP)
    verified = get_reasoning_profile(ReasoningMode.VERIFIED)

    assert fast.profile_name == "fast"
    assert deep.profile_name == "deep"
    assert verified.profile_name == "verified"
    assert "uncertainty" in verified.system_prompt.lower()
    assert "external verification" in verified.system_prompt.lower()


def test_openai_provider_receives_expected_profile_settings() -> None:
    captured: dict[str, object] = {}

    def _create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(output_text="ok")

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=_create))
    provider = OpenAIExecutionProvider(
        client=fake_client,
        models_by_mode={
            ReasoningMode.FAST: "fast-model",
            ReasoningMode.DEEP: "deep-model",
            ReasoningMode.VERIFIED: "verified-model",
        },
    )
    profile = get_reasoning_profile(ReasoningMode.VERIFIED)
    provider.execute(ExecutionRequest(prompt="test prompt"), ReasoningMode.VERIFIED, profile)

    assert captured["model"] == "verified-model"
    assert captured["temperature"] == profile.temperature
    assert captured["max_output_tokens"] == profile.max_output_tokens
    assert profile.system_prompt in str(captured["input"])


def test_pipeline_response_contains_profile_metadata(monkeypatch) -> None:
    monkeypatch.setenv("SEVAQ_PROVIDER", "mock")
    response = ExecutionPipeline().run(
        ExecutionRequest(prompt="Need medical guidance with citations for this dosage.")
    )
    assert response.reasoning_mode == ReasoningMode.VERIFIED
    assert response.reasoning_profile == "verified"
    assert response.caution_level == "high"
