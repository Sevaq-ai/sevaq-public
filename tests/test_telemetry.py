from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.interfaces.execution import ExecutionRequest
from app.orchestration.execution_pipeline import ExecutionPipeline
from app.providers.provider_factory import PROVIDER_ENV
from app.telemetry.db import DB_PATH_ENV_VAR, get_engine
from app.telemetry.ledger import hash_prompt, init_db, read_recent_events
from app.telemetry.models import TelemetryEvent


def _set_test_db(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(tmp_path / "telemetry_test.db"))
    monkeypatch.setenv(PROVIDER_ENV, "mock")
    get_engine.cache_clear()


def test_database_initializes(monkeypatch, tmp_path) -> None:
    _set_test_db(monkeypatch, tmp_path)
    init_db()
    events = read_recent_events()
    assert events == []


def test_hash_prompt_is_deterministic() -> None:
    first = hash_prompt("hello world")
    second = hash_prompt("hello world")
    assert first == second
    assert len(first) == 64


def test_successful_execution_writes_event(monkeypatch, tmp_path) -> None:
    _set_test_db(monkeypatch, tmp_path)
    prompt = "Summarize this short note."
    ExecutionPipeline().run(ExecutionRequest(prompt=prompt))

    events = read_recent_events(limit=1)
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, TelemetryEvent)
    assert event.success_flag is True
    assert event.prompt_hash == hash_prompt(prompt)
    assert event.reasoning_profile in {"fast", "deep", "verified"}


def test_recent_events_can_be_read_and_prompt_not_stored(monkeypatch, tmp_path) -> None:
    _set_test_db(monkeypatch, tmp_path)
    pipeline = ExecutionPipeline()
    pipeline.run(ExecutionRequest(prompt="First prompt"))
    pipeline.run(ExecutionRequest(prompt="Second prompt"))

    events = read_recent_events(limit=2)
    assert len(events) == 2
    assert events[0].id > events[1].id
    assert not hasattr(events[0], "prompt")
