from __future__ import annotations

import pathlib
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.telemetry.db import DB_PATH_ENV_VAR, get_engine
from app.telemetry.ledger import init_db


def test_db_schema_initialization_and_migration_path(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "migration_test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE telemetry_events ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "request_id TEXT NOT NULL, "
        "timestamp TEXT NOT NULL, "
        "prompt_hash TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv(DB_PATH_ENV_VAR, str(db_path))
    get_engine.cache_clear()
    init_db()

    check = sqlite3.connect(db_path)
    cols = {row[1] for row in check.execute("PRAGMA table_info(telemetry_events)").fetchall()}
    check.close()
    assert "validation_status" in cols
    assert "compute_intensity" in cols
    assert "needs_external_verification" in cols
    assert "verifier_type" in cols
    assert "verification_score" in cols
    assert "grounding_risk" in cols
    assert "uncertainty_level" in cols
    assert "needs_external_sources" in cols
