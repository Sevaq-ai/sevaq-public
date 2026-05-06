from __future__ import annotations

from sqlalchemy import text

from app.telemetry.db import get_engine

_REQUIRED_COLUMNS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "request_id": "VARCHAR(64) NOT NULL DEFAULT ''",
    "timestamp": "DATETIME NOT NULL DEFAULT '1970-01-01T00:00:00'",
    "prompt_hash": "VARCHAR(64) NOT NULL DEFAULT ''",
    "reasoning_mode": "VARCHAR(32) NOT NULL DEFAULT 'fast'",
    "reasoning_profile": "VARCHAR(32) NOT NULL DEFAULT 'fast'",
    "reasoning_style": "VARCHAR(64) NOT NULL DEFAULT 'brief-direct'",
    "caution_level": "VARCHAR(32) NOT NULL DEFAULT 'low'",
    "verification_behavior": "TEXT NOT NULL DEFAULT 'not_applicable'",
    "trace_confidence_level": "VARCHAR(16) NOT NULL DEFAULT 'medium'",
    "trace_escalated": "BOOLEAN NOT NULL DEFAULT 0",
    "validation_status": "VARCHAR(24) NOT NULL DEFAULT 'not_applicable'",
    "confidence_score": "FLOAT NOT NULL DEFAULT 0.0",
    "needs_external_verification": "BOOLEAN NOT NULL DEFAULT 0",
    "verifier_type": "VARCHAR(16) NOT NULL DEFAULT 'heuristic'",
    "verification_score": "FLOAT NOT NULL DEFAULT 0.0",
    "grounding_risk": "VARCHAR(16) NOT NULL DEFAULT 'medium'",
    "uncertainty_level": "VARCHAR(16) NOT NULL DEFAULT 'medium'",
    "needs_external_sources": "BOOLEAN NOT NULL DEFAULT 0",
    "compute_intensity": "VARCHAR(16) NOT NULL DEFAULT 'low'",
    "potential_overallocation_flag": "BOOLEAN NOT NULL DEFAULT 0",
    "potential_underallocation_flag": "BOOLEAN NOT NULL DEFAULT 0",
    "implementation_source": "VARCHAR(32) NOT NULL DEFAULT 'public'",
    "provider_name": "VARCHAR(64) NOT NULL DEFAULT 'unknown'",
    "risk_score": "FLOAT NOT NULL DEFAULT 0.0",
    "complexity_score": "FLOAT NOT NULL DEFAULT 0.0",
    "routing_reason": "TEXT NOT NULL DEFAULT ''",
    "estimated_cost_units": "FLOAT NOT NULL DEFAULT 0.0",
    "estimated_latency_ms": "INTEGER NOT NULL DEFAULT 0",
    "success_flag": "BOOLEAN NOT NULL DEFAULT 0",
    "error_message": "TEXT NULL",
}


def migrate_telemetry_schema() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        columns = conn.execute(text("PRAGMA table_info(telemetry_events)")).mappings().all()
        if not columns:
            return
        existing = {col["name"] for col in columns}
        for name, ddl in _REQUIRED_COLUMNS.items():
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE telemetry_events ADD COLUMN {name} {ddl}"))
