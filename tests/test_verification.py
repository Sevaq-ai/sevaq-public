from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.interfaces.execution import ExecutionRequest
from app.interfaces.verification import VerificationRequest
from app.models.common import ReasoningMode
from app.orchestration.execution_pipeline import ExecutionPipeline
from app.providers.provider_factory import PROVIDER_ENV
from app.telemetry.db import DB_PATH_ENV_VAR, get_engine
from app.verification.simple_verifier import SimpleVerifier


def _set_test_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(PROVIDER_ENV, "mock")
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(tmp_path / "verification_test.db"))
    get_engine.cache_clear()


def test_legal_prompt_requires_external_verification() -> None:
    result = SimpleVerifier().verify(
        VerificationRequest(
            reasoning_mode=ReasoningMode.VERIFIED,
            risk_category="high",
            response_text="placeholder",
            prompt_signals=["legal"],
        )
    )
    assert result.needs_external_verification is True
    assert result.grounding_risk == "high"
    assert result.needs_external_sources is True


def test_medical_prompt_requires_external_verification() -> None:
    result = SimpleVerifier().verify(
        VerificationRequest(
            reasoning_mode=ReasoningMode.VERIFIED,
            risk_category="high",
            response_text="placeholder",
            prompt_signals=["medical"],
        )
    )
    assert result.needs_external_verification is True
    assert result.grounding_risk == "high"


def test_simple_drafting_prompt_does_not_require_external_verification() -> None:
    result = SimpleVerifier().verify(
        VerificationRequest(
            reasoning_mode=ReasoningMode.FAST,
            risk_category="low",
            response_text="Drafted response",
            prompt_signals=[],
        )
    )
    assert result.needs_external_verification is False
    assert result.validation_status in {"not_applicable", "pass"}
    assert result.grounding_risk == "low"
    assert result.uncertainty_level == "low"


def test_verified_mode_includes_caution() -> None:
    result = SimpleVerifier().verify(
        VerificationRequest(
            reasoning_mode=ReasoningMode.VERIFIED,
            risk_category="medium",
            response_text="Response text",
            prompt_signals=[],
        )
    )
    assert result.validation_status in {"warning", "pass"}
    assert "verify" in result.recommended_user_message.lower()
    assert 0.0 <= result.verification_score <= 1.0


def test_current_events_prompt_requires_external_sources() -> None:
    result = SimpleVerifier().verify(
        VerificationRequest(
            reasoning_mode=ReasoningMode.VERIFIED,
            risk_category="medium",
            response_text="summary",
            prompt_signals=["current events", "today"],
        )
    )
    assert result.needs_external_sources is True
    assert result.uncertainty_level == "high"


def test_execution_response_includes_verification_result(monkeypatch, tmp_path) -> None:
    _set_test_env(monkeypatch, tmp_path)
    response = ExecutionPipeline().run(
        ExecutionRequest(prompt="Can you provide legal advice for this contract?")
    )
    assert response.verification_result is not None
    assert response.verification_result.needs_external_verification is True
    assert response.verification_result.verifier_type == "heuristic"
    assert 0.0 <= response.verification_result.verification_score <= 1.0
    assert response.verification_result.grounding_risk in {"low", "medium", "high"}


def test_dashboard_has_no_local_verifier_duplicate() -> None:
    dashboard_verifier = ROOT / "dashboard" / "simple_verifier.py"
    assert dashboard_verifier.exists() is False
    streamlit_app = (ROOT / "dashboard" / "streamlit_app.py").read_text(encoding="utf-8")
    assert "SimpleVerifier" not in streamlit_app
