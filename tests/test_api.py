from __future__ import annotations

import pathlib
import sys

from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.main import app
from app.providers.provider_factory import PROVIDER_ENV
from app.telemetry.db import DB_PATH_ENV_VAR, get_engine
from app.telemetry.ledger import read_recent_events


def _client_with_db(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(tmp_path / "api_test.db"))
    monkeypatch.setenv(PROVIDER_ENV, "mock")
    get_engine.cache_clear()
    return TestClient(app)


def test_health_endpoint(monkeypatch, tmp_path) -> None:
    with _client_with_db(monkeypatch, tmp_path) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_route_runs_probe_and_routing_only(monkeypatch, tmp_path) -> None:
    with _client_with_db(monkeypatch, tmp_path) as client:
        response = client.post("/v1/route", json={"prompt": "Create a roadmap with tradeoff analysis."})
    assert response.status_code == 200
    payload = response.json()
    assert payload["reasoning_mode"] == "deep"
    assert "implementation_source" in payload
    assert read_recent_events() == []


def test_run_writes_telemetry_and_recent_endpoint(monkeypatch, tmp_path) -> None:
    prompt = "Need medical guidance with citations for this dosage."
    with _client_with_db(monkeypatch, tmp_path) as client:
        run_response = client.post("/v1/run", json={"prompt": prompt})
        telemetry_response = client.get("/v1/telemetry/recent?limit=1")

    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["reasoning_mode"] == "verified"
    assert "implementation_source" in run_payload

    assert telemetry_response.status_code == 200
    events = telemetry_response.json()
    assert len(events) == 1
    assert events[0]["success_flag"] is True
    assert "prompt" not in events[0]
    assert len(events[0]["prompt_hash"]) == 64
