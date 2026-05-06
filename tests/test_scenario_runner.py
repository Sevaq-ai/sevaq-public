from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.evaluation.scenario_runner import (
    load_scenarios,
    run_scenario,
    summarize_results,
)
from app.providers.provider_factory import PROVIDER_ENV
from app.telemetry.db import DB_PATH_ENV_VAR, get_engine


def _set_test_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(PROVIDER_ENV, "mock")
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(tmp_path / "scenario_runner.db"))
    get_engine.cache_clear()


def test_scenarios_load_correctly() -> None:
    scenarios = load_scenarios()
    assert len(scenarios) >= 15
    assert {"id", "prompt", "expected_mode", "expected_profile", "risk_category", "explanation"} <= set(
        scenarios[0].keys()
    )


def test_runner_executes_at_least_one_scenario(monkeypatch, tmp_path) -> None:
    _set_test_env(monkeypatch, tmp_path)
    scenario = load_scenarios()[0]
    result = run_scenario(scenario)
    assert result["id"] == scenario["id"]
    assert "actual_mode" in result
    assert "actual_profile" in result
    assert "pass" in result


def test_summary_returns_required_metrics() -> None:
    sample = [
        {"risk_category": "low", "pass": True},
        {"risk_category": "low", "pass": False},
        {"risk_category": "high", "pass": True},
    ]
    summary = summarize_results(sample)
    assert summary["total"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert abs(summary["accuracy"] - (2 / 3)) < 1e-9
