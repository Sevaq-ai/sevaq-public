from __future__ import annotations

import pathlib
import sys
from types import SimpleNamespace

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.providers.openai_provider import (
    DAILY_COST_BUDGET_ENV,
    MAX_PROMPT_CHARS_ENV,
    OpenAIExecutionProvider,
    OpenAIProviderRuntimeGuardrailError,
)


def test_prompt_max_length_is_enforced(monkeypatch) -> None:
    monkeypatch.setenv(MAX_PROMPT_CHARS_ENV, "10")
    with_oversized = "x" * 11
    with pytest.raises(OpenAIProviderRuntimeGuardrailError):
        OpenAIExecutionProvider._enforce_prompt_length(with_oversized)


def test_oversized_prompt_does_not_reach_openai(monkeypatch) -> None:
    monkeypatch.setenv(MAX_PROMPT_CHARS_ENV, "3")
    provider = OpenAIExecutionProvider(
        client=SimpleNamespace(
            responses=SimpleNamespace(
                create=lambda **_: (_ for _ in ()).throw(AssertionError("should not call openai"))
            )
        ),
        models_by_mode={},
    )
    with pytest.raises(OpenAIProviderRuntimeGuardrailError):
        provider._enforce_prompt_length("toolong")


def test_budget_guardrail_enforced(monkeypatch) -> None:
    monkeypatch.setenv(DAILY_COST_BUDGET_ENV, "0.01")
    OpenAIExecutionProvider._daily_estimated_cost_accumulator = 0.02
    with pytest.raises(OpenAIProviderRuntimeGuardrailError):
        OpenAIExecutionProvider._enforce_budget(0.01)
