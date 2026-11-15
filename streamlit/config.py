"""Frontend-only settings."""

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FrontendSettings:
    backend_base_url: str
    upload_timeout_seconds: float
    query_timeout_seconds: float

    @classmethod
    def from_env(cls) -> "FrontendSettings":
        return cls(
            backend_base_url=os.getenv(
                "RAG_BACKEND_BASE_URL", "http://127.0.0.1:8000/api/v1"
            ).rstrip("/"),
            upload_timeout_seconds=float(os.getenv("RAG_UPLOAD_TIMEOUT_SECONDS", "180")),
            query_timeout_seconds=float(os.getenv("RAG_QUERY_UI_TIMEOUT_SECONDS", "180")),
        )
