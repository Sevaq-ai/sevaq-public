from __future__ import annotations

from app.models.common import ReasoningMode
from app.models.trace import ValidationTrace

_HIGH_STAKES = {
    "legal",
    "medical",
    "finance",
    "financial",
    "immigration",
    "visa",
    "asylum",
    "safety",
    "harm",
    "breaking news",
    "current events",
    "today",
}


def build_validation_trace(prompt: str, mode: ReasoningMode) -> ValidationTrace:
    text = prompt.lower()
    high_stakes_hit = any(token in text for token in _HIGH_STAKES)
    if mode != ReasoningMode.VERIFIED:
        return ValidationTrace(
            validation_status="not_applicable",
            confidence_score=0.0,
            validation_notes="Validation posture is only elevated for verified mode.",
            needs_external_verification=high_stakes_hit,
        )
    if high_stakes_hit:
        return ValidationTrace(
            validation_status="warning",
            confidence_score=0.45,
            validation_notes="High-stakes domain detected; external verification is recommended.",
            needs_external_verification=True,
        )
    return ValidationTrace(
        validation_status="pass",
        confidence_score=0.72,
        validation_notes="No high-stakes trigger detected in this verified-mode prompt.",
        needs_external_verification=False,
    )
