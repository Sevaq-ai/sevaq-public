from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reasoning_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    reasoning_profile: Mapped[str] = mapped_column(String(32), nullable=False)
    reasoning_style: Mapped[str] = mapped_column(String(64), nullable=False)
    caution_level: Mapped[str] = mapped_column(String(32), nullable=False)
    verification_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    trace_confidence_level: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    trace_escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validation_status: Mapped[str] = mapped_column(String(24), nullable=False, default="not_applicable")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    needs_external_verification: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verifier_type: Mapped[str] = mapped_column(String(16), nullable=False, default="heuristic")
    verification_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    grounding_risk: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    uncertainty_level: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    needs_external_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    compute_intensity: Mapped[str] = mapped_column(String(16), nullable=False, default="low")
    potential_overallocation_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    potential_underallocation_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    implementation_source: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    complexity_score: Mapped[float] = mapped_column(Float, nullable=False)
    routing_reason: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_cost_units: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    success_flag: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
