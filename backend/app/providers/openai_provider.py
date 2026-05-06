from __future__ import annotations

import os
import time

from app.interfaces.execution import BaseExecutionProvider, ExecutionRequest, ExecutionResponse
from app.models.common import ImplementationSource, ReasoningMode
from app.orchestration.reasoning_profiles import ReasoningProfile

FAST_MODEL_ENV = "SEVAQ_OPENAI_FAST_MODEL"
DEEP_MODEL_ENV = "SEVAQ_OPENAI_DEEP_MODEL"
VERIFIED_MODEL_ENV = "SEVAQ_OPENAI_VERIFIED_MODEL"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
MAX_PROMPT_CHARS_ENV = "SEVAQ_MAX_PROMPT_CHARS"
MAX_OUTPUT_TOKENS_ENV = "SEVAQ_OPENAI_MAX_OUTPUT_TOKENS"
REQUEST_TIMEOUT_ENV = "SEVAQ_OPENAI_REQUEST_TIMEOUT_SECONDS"
DAILY_COST_BUDGET_ENV = "SEVAQ_OPENAI_DAILY_COST_BUDGET_UNITS"
DEFAULT_FAST_MODEL = "gpt-4.1-mini"
DEFAULT_DEEP_MODEL = "gpt-4.1-mini"
DEFAULT_VERIFIED_MODEL = "gpt-4.1-mini"


class OpenAIProviderConfigError(ValueError):
    pass


class OpenAIProviderRuntimeGuardrailError(RuntimeError):
    pass


class OpenAIExecutionProvider(BaseExecutionProvider):
    _daily_estimated_cost_accumulator = 0.0

    def __init__(self, client, models_by_mode: dict[ReasoningMode, str]):
        self._client = client
        self._models_by_mode = models_by_mode

    @classmethod
    def from_env(cls) -> "OpenAIExecutionProvider":
        api_key = os.getenv(OPENAI_API_KEY_ENV, "").strip()
        if not api_key:
            raise OpenAIProviderConfigError("Missing OPENAI_API_KEY")
        model_values = {
            ReasoningMode.FAST: os.getenv(FAST_MODEL_ENV, DEFAULT_FAST_MODEL).strip(),
            ReasoningMode.DEEP: os.getenv(DEEP_MODEL_ENV, DEFAULT_DEEP_MODEL).strip(),
            ReasoningMode.VERIFIED: os.getenv(VERIFIED_MODEL_ENV, DEFAULT_VERIFIED_MODEL).strip(),
        }
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise OpenAIProviderConfigError("OpenAI SDK not installed") from exc
        return cls(client=OpenAI(api_key=api_key), models_by_mode=model_values)

    def execute(
        self, request: ExecutionRequest, mode: ReasoningMode, profile: ReasoningProfile
    ) -> ExecutionResponse:
        self._enforce_prompt_length(request.prompt)
        estimated_cost = float(len(request.prompt.split())) / 100.0
        self._enforce_budget(estimated_cost)

        model = self._models_by_mode[mode]
        max_output_tokens = self._resolve_max_output_tokens(profile.max_output_tokens)
        timeout_s = self._resolve_timeout_seconds()
        start = time.perf_counter()
        output_text = self._create_response_text(
            model=model,
            system_prompt=profile.system_prompt,
            prompt=request.prompt,
            temperature=profile.temperature,
            max_output_tokens=max_output_tokens,
            timeout_s=timeout_s,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        if not output_text:
            output_text = "No text output returned by provider."
        self.__class__._daily_estimated_cost_accumulator += estimated_cost
        return ExecutionResponse(
            reasoning_mode=mode,
            reasoning_profile=profile.profile_name,
            reasoning_style=profile.reasoning_style,
            caution_level=profile.caution_level,
            verification_behavior=profile.verification_behavior,
            implementation_source=ImplementationSource.MOCK,
            provider_name="openai-provider",
            simulated_response=output_text.strip(),
            estimated_cost_units=round(estimated_cost, 4),
            estimated_latency_ms=max(latency_ms, 1),
            risk_score=0.0,
            complexity_score=0.0,
            routing_reason="provider-executed",
            demo_mode="live",
            live_model_used=model,
        )

    def _create_response_text(
        self,
        model: str,
        system_prompt: str,
        prompt: str,
        temperature: float,
        max_output_tokens: int,
        timeout_s: int,
    ) -> str:
        # Prefer the newer Responses API when available.
        responses_api = getattr(self._client, "responses", None)
        if responses_api is not None:
            response = responses_api.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                timeout=timeout_s,
            )
            output_text = getattr(response, "output_text", "") or ""
            if output_text:
                return output_text.strip()

        # Backward-compatible fallback for older OpenAI SDK versions.
        chat_api = getattr(self._client, "chat", None)
        completions_api = getattr(chat_api, "completions", None) if chat_api is not None else None
        if completions_api is None:
            raise OpenAIProviderConfigError("OpenAI SDK does not support responses or chat.completions APIs")

        completion = completions_api.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_output_tokens,
            timeout=timeout_s,
        )
        choices = getattr(completion, "choices", None) or []
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", "") if message is not None else ""
        return (content or "").strip()

    @staticmethod
    def _enforce_prompt_length(prompt: str) -> None:
        max_chars = int(os.getenv(MAX_PROMPT_CHARS_ENV, "4000"))
        if len(prompt) > max_chars:
            raise OpenAIProviderRuntimeGuardrailError(
                f"Prompt exceeds max length ({len(prompt)} > {max_chars})"
            )

    @classmethod
    def _enforce_budget(cls, request_estimated_cost: float) -> None:
        budget_raw = os.getenv(DAILY_COST_BUDGET_ENV, "").strip()
        if not budget_raw:
            return
        budget = float(budget_raw)
        projected = cls._daily_estimated_cost_accumulator + request_estimated_cost
        if projected > budget:
            raise OpenAIProviderRuntimeGuardrailError(
                f"OpenAI daily cost budget exceeded (projected={projected:.4f}, budget={budget:.4f})"
            )

    @staticmethod
    def _resolve_max_output_tokens(profile_default: int) -> int:
        override = os.getenv(MAX_OUTPUT_TOKENS_ENV, "").strip()
        return int(override) if override else profile_default

    @staticmethod
    def _resolve_timeout_seconds() -> int:
        return int(os.getenv(REQUEST_TIMEOUT_ENV, "20"))
