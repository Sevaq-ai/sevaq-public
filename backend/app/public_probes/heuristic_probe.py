from __future__ import annotations

from app.interfaces.probe import Probe, ProbeResult
from app.models.common import ImplementationSource


class HeuristicProbe(Probe):
    """Public-safe probe based on simple transparent heuristics."""

    def assess(self, prompt: str, mode: str) -> ProbeResult:
        text = prompt.lower()

        risk_terms = [
            "legal",
            "medical",
            "financial",
            "finance",
            "immigration",
            "visa",
            "safety",
            "harm",
            "breaking news",
            "today",
        ]
        sensitive_context_terms = [
            "unhappy",
            "upset",
            "angry",
            "frustrated",
            "conflict",
            "hostile",
            "harassment",
            "retaliation",
            "toxic",
            "burnout",
            "resignation",
            "quit",
            "fired",
            "termination",
        ]
        uncertainty_terms = ["verify", "prove", "uncertain", "evidence", "citations"]
        complexity_terms = ["multi-step", "edge case", "formal", "tradeoff", "optimize", "plan", "analyze"]

        risk_hits = [term for term in risk_terms if term in text]
        sensitive_hits = [term for term in sensitive_context_terms if term in text]
        complexity_hits = [term for term in complexity_terms if term in text]
        verification_signals = [term for term in uncertainty_terms if term in text]

        hits = len(risk_hits) + len(complexity_hits) + len(verification_signals)
        sensitive_bonus = min(0.2, len(sensitive_hits) * 0.07)
        mode_bonus = 0.2 if mode == "verified" else (0.1 if mode == "deep" else 0.0)

        score = min(1.0, 0.1 + hits * 0.12 + sensitive_bonus + mode_bonus)
        notes = f"heuristic_hits={hits}; mode={mode}"
        if risk_hits:
            detected_domain = "high_stakes"
        elif sensitive_hits:
            detected_domain = "sensitive_personal"
        elif "code" in text or "api" in text or "architecture" in text:
            detected_domain = "technical"
        else:
            detected_domain = "general"
        if sensitive_hits:
            detected_intent = "sensitive_communication"
        else:
            detected_intent = "analysis" if complexity_hits else "direct_answer"

        return ProbeResult(
            score=score,
            notes=notes,
            detected_domain=detected_domain,
            detected_intent=detected_intent,
            detected_risk_keywords=risk_hits + sensitive_hits,
            detected_complexity_keywords=complexity_hits,
            verification_signals=verification_signals,
            source=ImplementationSource.PUBLIC,
        )
