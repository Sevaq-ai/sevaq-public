from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.common import ReasoningMode


class ReasoningProfile(BaseModel):
    profile_name: str
    system_prompt: str = Field(min_length=10)
    reasoning_style: str
    caution_level: str
    verification_behavior: str
    max_output_tokens: int = Field(gt=0)
    temperature: float = Field(ge=0.0, le=1.5)
    recommended_provider_behavior: str


_PROFILES = {
    ReasoningMode.FAST: ReasoningProfile(
        profile_name="fast",
        system_prompt="Provide a concise and direct response with minimal verbosity.",
        reasoning_style="brief-direct",
        caution_level="low",
        verification_behavior="not_applicable",
        max_output_tokens=300,
        temperature=0.2,
        recommended_provider_behavior="prioritize low latency and concise output",
    ),
    ReasoningMode.DEEP: ReasoningProfile(
        profile_name="deep",
        system_prompt="Use multi-step reasoning with structured explanation, synthesis, and tradeoffs.",
        reasoning_style="structured-multi-step",
        caution_level="medium",
        verification_behavior="state assumptions and uncertainty where relevant",
        max_output_tokens=900,
        temperature=0.4,
        recommended_provider_behavior="prioritize completeness and structured sections",
    ),
    ReasoningMode.VERIFIED: ReasoningProfile(
        profile_name="verified",
        system_prompt=(
            "Be careful and uncertainty-aware. Avoid unsupported claims, include caveats where "
            "appropriate, and mention when external verification may be needed. For legal, medical, "
            "financial, immigration, safety, and current-events topics, use extra caution and state "
            "that external verification is recommended."
        ),
        reasoning_style="careful-evidence-aware",
        caution_level="high",
        verification_behavior="emphasize uncertainty and potential need for external verification",
        max_output_tokens=800,
        temperature=0.2,
        recommended_provider_behavior="prioritize cautious language and explicit limitations",
    ),
}


def get_reasoning_profile(mode: ReasoningMode) -> ReasoningProfile:
    return _PROFILES[mode]
