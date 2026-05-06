from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.interfaces.execution import ExecutionRequest
from app.orchestration.execution_pipeline import ExecutionPipeline


def _default_scenarios_path() -> Path:
    return Path(__file__).resolve().parents[3] / "examples" / "demo_scenarios.jsonl"


def load_scenarios(path: str | Path | None = None) -> list[dict[str, Any]]:
    source = Path(path) if path else _default_scenarios_path()
    scenarios: list[dict[str, Any]] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if line.strip():
            scenarios.append(json.loads(line))
    return scenarios


def run_scenario(
    scenario: dict[str, Any], pipeline: ExecutionPipeline | None = None
) -> dict[str, Any]:
    runner = pipeline or ExecutionPipeline()
    response = runner.run(ExecutionRequest(prompt=scenario["prompt"]))
    actual_mode = response.reasoning_mode.value
    actual_profile = response.reasoning_profile
    mode_match = actual_mode == scenario["expected_mode"]
    profile_match = actual_profile == scenario["expected_profile"]
    return {
        "id": scenario["id"],
        "risk_category": scenario["risk_category"],
        "expected_mode": scenario["expected_mode"],
        "actual_mode": actual_mode,
        "expected_profile": scenario["expected_profile"],
        "actual_profile": actual_profile,
        "pass": mode_match and profile_match,
    }


def run_all_scenarios(path: str | Path | None = None) -> list[dict[str, Any]]:
    os.environ.setdefault("SEVAQ_PROVIDER", "mock")
    scenarios = load_scenarios(path)
    pipeline = ExecutionPipeline()
    return [run_scenario(scenario, pipeline=pipeline) for scenario in scenarios]


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r["pass"])
    failed = total - passed
    by_risk: dict[str, dict[str, Any]] = {}
    for result in results:
        bucket = by_risk.setdefault(result["risk_category"], {"total": 0, "passed": 0, "accuracy": 0.0})
        bucket["total"] += 1
        if result["pass"]:
            bucket["passed"] += 1
    for bucket in by_risk.values():
        bucket["accuracy"] = (bucket["passed"] / bucket["total"]) if bucket["total"] else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "accuracy": (passed / total) if total else 0.0,
        "by_risk_category": by_risk,
    }
