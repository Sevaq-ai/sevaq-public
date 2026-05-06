from __future__ import annotations

from enum import Enum


class ReasoningMode(str, Enum):
    FAST = "fast"
    DEEP = "deep"
    VERIFIED = "verified"


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CostTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LatencyTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImplementationSource(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    MOCK = "mock"
