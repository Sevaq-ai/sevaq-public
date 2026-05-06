from __future__ import annotations

from app.interfaces.verification import BaseVerifier, VerificationRequest, VerificationResult
from app.models.common import ReasoningMode

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
_LOW_STAKES = {"draft", "drafting", "creative", "email", "thank-you", "follow-up"}
_EXTERNAL_SOURCE_SIGNALS = {"breaking news", "current events", "today"}


class SimpleVerifier(BaseVerifier):
    def verify(self, request: VerificationRequest) -> VerificationResult:
        signals = [s.lower() for s in request.prompt_signals]
        high_stakes_flags = [s for s in signals if s in _HIGH_STAKES]
        low_stakes_flags = [s for s in signals if s in _LOW_STAKES]
        has_external_source_signal = any(s in _EXTERNAL_SOURCE_SIGNALS for s in signals)
        needs_external = (
            request.risk_category == "high"
            or bool(high_stakes_flags)
            or has_external_source_signal
        )

        if high_stakes_flags:
            grounding_risk = "high"
        elif request.risk_category == "medium" and not low_stakes_flags:
            grounding_risk = "medium"
        else:
            grounding_risk = "low"

        if needs_external:
            uncertainty_level = "high"
        elif request.reasoning_mode == ReasoningMode.VERIFIED:
            uncertainty_level = "medium"
        else:
            uncertainty_level = "low"

        if request.reasoning_mode == ReasoningMode.VERIFIED:
            status = "warning" if needs_external else "pass"
            confidence = 0.45 if needs_external else 0.7
            verification_score = 0.42 if needs_external else 0.74
            notes = (
                "Verified mode used with high-stakes indicators; external verification is recommended."
                if needs_external
                else "Verified mode used; uncertainty and caveats should still be reviewed."
            )
        elif request.reasoning_mode == ReasoningMode.FAST and not needs_external:
            status = "not_applicable"
            confidence = 0.8
            verification_score = 0.84
            notes = "Low-risk fast prompt; lightweight validation posture."
        else:
            status = "warning" if needs_external else "pass"
            confidence = 0.5 if needs_external else 0.65
            verification_score = 0.48 if needs_external else 0.66
            notes = "Review assumptions and check critical claims before relying on response."

        verifier_notes: list[str] = []
        if high_stakes_flags:
            verifier_notes.append(f"High-stakes domain indicators: {', '.join(sorted(set(high_stakes_flags)))}.")
        if has_external_source_signal:
            verifier_notes.append("Prompt implies time-sensitive or externally-grounded facts.")
        if low_stakes_flags:
            verifier_notes.append("Low-stakes drafting/creative indicators detected.")
        verifier_notes.append("Current verifier uses public-safe heuristics, not factual adjudication.")

        user_summary = (
            f"Heuristic verifier signal: grounding risk is {grounding_risk}, uncertainty is {uncertainty_level}, "
            f"verification score is {verification_score:.2f}."
        )
        if needs_external:
            user_summary += " External sources are recommended before relying on high-stakes claims."

        return VerificationResult(
            validation_status=status,
            confidence_score=confidence,
            needs_external_verification=needs_external,
            validation_notes=notes,
            risk_flags=high_stakes_flags,
            recommended_user_message=(
                "Treat this output as guidance and verify important claims with trusted sources."
            ),
            verifier_type="heuristic",
            verification_score=verification_score,
            grounding_risk=grounding_risk,
            uncertainty_level=uncertainty_level,
            needs_external_sources=needs_external,
            verifier_notes=verifier_notes,
            user_facing_summary=user_summary,
        )
