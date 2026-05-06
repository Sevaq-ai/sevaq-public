from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_PATH = "./sevaq_telemetry.db"
DB_PATH_ENV_VAR = "SEVAQ_TELEMETRY_DB_PATH"


def _sqlite_url() -> str:
    db_path = os.getenv(DB_PATH_ENV_VAR, DEFAULT_DB_PATH)
    if db_path == ":memory:":
        return "sqlite:///:memory:"
    return f"sqlite:///{db_path}"


@lru_cache(maxsize=4)
def get_engine(db_url: str | None = None):
    return create_engine(db_url or _sqlite_url(), future=True)


def get_session_local(db_url: str | None = None):
    return sessionmaker(bind=get_engine(db_url), autoflush=False, autocommit=False, future=True)
