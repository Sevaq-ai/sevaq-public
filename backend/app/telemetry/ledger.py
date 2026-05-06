from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import select

from app.telemetry.db import get_engine, get_session_local
from app.telemetry.migrations import migrate_telemetry_schema
from app.telemetry.models import Base, TelemetryEvent


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
    migrate_telemetry_schema()


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def write_event(event_data: dict[str, Any]) -> TelemetryEvent:
    init_db()
    with get_session_local()() as session:
        event = TelemetryEvent(**event_data)
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


def read_recent_events(limit: int = 50) -> list[TelemetryEvent]:
    with get_session_local()() as session:
        stmt = select(TelemetryEvent).order_by(TelemetryEvent.timestamp.desc()).limit(limit)
        return list(session.scalars(stmt).all())
