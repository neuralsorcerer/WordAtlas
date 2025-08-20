from __future__ import annotations

import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    default_depth: int = Field(default=int(os.getenv("WORDATLAS_DEFAULT_DEPTH", 1)))
    max_nodes: int = Field(default=int(os.getenv("WORDATLAS_MAX_NODES", 300)))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))


settings = Settings()
