from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PRIVATE_REPO = ROOT.parent / "sevaq-private"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.interfaces.execution import ExecutionRequest
from app.models.common import ImplementationSource, ReasoningMode
import app.orchestration.execution_pipeline as execution_pipeline_module
from app.orchestration.execution_pipeline import ExecutionPipeline
from app.providers.provider_factory import DEMO_MODE_ENV, PROVIDER_ENV
from app.telemetry.db import DB_PATH_ENV_VAR, get_engine
from app.telemetry.ledger import read_recent_events


def _clear_private_modules() -> None:
    for key in list(sys.modules.keys()):
        if key.startswith("sevaq_private"):
            del sys.modules[key]


def _set_test_db(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(tmp_path / "execution_pipeline.db"))
    monkeypatch.setenv(PROVIDER_ENV, "mock")
    monkeypatch.setenv(DEMO_MODE_ENV, "mock")
    get_engine.cache_clear()


def test_fast_prompt_routes_and_executes_fast(monkeypatch, tmp_path) -> None:
    _set_test_db(monkeypatch, tmp_path)
    _clear_private_modules()
    sys.path[:] = [p for p in sys.path if "sevaq-private" not in p]
    response = ExecutionPipeline().run(ExecutionRequest(prompt="Summarize this short note."))

    assert response.reasoning_mode == ReasoningMode.FAST
    assert response.provider_name == "mock-provider"
    assert "Fast path" in response.simulated_response
    assert response.estimated_cost_units == 1.0
    assert response.estimated_latency_ms == 120
    assert response.demo_mode == "mock"
    assert response.provider_fallback_used is False
    assert len(read_recent_events(limit=1)) == 1


def test_deep_reasoning_prompt_routes_deep() -> None:
    _clear_private_modules()
    sys.path[:] = [p for p in sys.path if "sevaq-private" not in p]
    response = ExecutionPipeline().run(
        ExecutionRequest(prompt="Create a roadmap and analyze tradeoff options for migration.")
    )

    assert response.reasoning_mode == ReasoningMode.DEEP
    assert "Deep path" in response.simulated_response
    assert response.estimated_cost_units == 3.0
    assert response.routing_reason


def test_sensitive_resignation_prompt_routes_deep_vs_basic_fast() -> None:
    _clear_private_modules()
    sys.path[:] = [p for p in sys.path if "sevaq-private" not in p]
    basic = ExecutionPipeline().run(ExecutionRequest(prompt="Draft a resignation email."))
    sensitive = ExecutionPipeline().run(
        ExecutionRequest(prompt="Draft a resignation email. I am unhappy and frustrated with my team.")
    )
    assert basic.reasoning_mode == ReasoningMode.FAST
    assert sensitive.reasoning_mode == ReasoningMode.DEEP


def test_verified_risk_prompt_routes_verified() -> None:
    _clear_private_modules()
    sys.path[:] = [p for p in sys.path if "sevaq-private" not in p]
    response = ExecutionPipeline().run(
        ExecutionRequest(prompt="Need medical guidance with citations for this dosage.")
    )

    assert response.reasoning_mode == ReasoningMode.VERIFIED
    assert "Verified path" in response.simulated_response
    assert response.estimated_latency_ms == 900
    assert 0.0 <= response.risk_score <= 1.0


def test_pipeline_falls_back_to_public_implementations() -> None:
    _clear_private_modules()
    sys.path[:] = [p for p in sys.path if "sevaq-private" not in p]
    response = ExecutionPipeline().run(
        ExecutionRequest(prompt="Rewrite this paragraph for clarity and brevity.")
    )

    assert response.implementation_source == ImplementationSource.PUBLIC
    assert "private placeholder" not in response.routing_reason


def test_pipeline_can_optionally_load_private_plugins() -> None:
    _clear_private_modules()
    if str(PRIVATE_REPO) not in sys.path:
        sys.path.insert(0, str(PRIVATE_REPO))
    response = ExecutionPipeline().run(
        ExecutionRequest(prompt="Legal contract review: identify risky clauses.")
    )

    assert response.implementation_source == ImplementationSource.PRIVATE
    assert "private placeholder" in response.routing_reason


def test_telemetry_write_failure_does_not_fail_execution(monkeypatch, tmp_path) -> None:
    _set_test_db(monkeypatch, tmp_path)
    _clear_private_modules()
    sys.path[:] = [p for p in sys.path if "sevaq-private" not in p]

    def _fail_write(_event):
        raise RuntimeError("telemetry down")

    monkeypatch.setattr(execution_pipeline_module, "write_event", _fail_write)
    response = ExecutionPipeline().run(ExecutionRequest(prompt="Summarize this short note."))
    assert response.reasoning_mode == ReasoningMode.FAST
    assert response.telemetry_logged is False
    assert "telemetry down" in (response.telemetry_error or "")
