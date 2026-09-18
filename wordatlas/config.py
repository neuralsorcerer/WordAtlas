from __future__ import annotations

import os

from pydantic import BaseModel, Field


def _env_int(key: str, default: int) -> int:
    """Read an integer from an environment variable, falling back to *default*."""
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


class Settings(BaseModel):
    default_depth: int = Field(default=_env_int("WORDATLAS_DEFAULT_DEPTH", 1))
    max_nodes: int = Field(default=_env_int("WORDATLAS_MAX_NODES", 300))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))


settings = Settings()
