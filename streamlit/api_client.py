"""HTTP client for the implemented document endpoints."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, BinaryIO
from uuid import UUID

import httpx


class ApiError(Exception):
    pass


@dataclass(slots=True)
class ApiClient:
    base_url: str
    owner_id: UUID
    upload_timeout_seconds: float = 180
    query_timeout_seconds: float = 180

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-User-ID": str(self.owner_id)}

    def upload_pdf(self, filename: str, source: BinaryIO) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}/documents",
                headers=self._headers,
                files={"file": (filename, source, "application/pdf")},
                timeout=self.upload_timeout_seconds,
            )
        except httpx.RequestError as exc:
            raise ApiError("Could not reach the backend upload API") from exc
        return self._json(response)

    def upload_pdf_stream(
        self,
        filename: str,
        source: BinaryIO,
        on_progress: Callable[[dict[str, Any]], None],
    ) -> dict[str, Any]:
        source.seek(0)
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/documents/stream",
                headers=self._headers,
                files={"file": (filename, source, "application/pdf")},
                timeout=self.upload_timeout_seconds,
            ) as response:
                if response.is_error:
                    response.read()
                    self._json(response)
                result: dict[str, Any] | None = None
                for event, payload in self._iter_sse(response):
                    if event == "progress":
                        on_progress(payload)
                    elif event == "error":
                        raise ApiError(payload.get("message", "Document ingestion failed"))
                    elif event == "result":
                        result = payload
                if result is None:
                    raise ApiError("Backend ingestion stream ended without a result")
                return result
        except httpx.RequestError as exc:
            raise ApiError("Could not reach the backend upload API") from exc

    def query_stream(
        self,
        question: str,
        document_ids: list[str],
        on_progress: Callable[[dict[str, Any]], None],
    ) -> dict[str, Any]:
        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/queries/stream",
                headers=self._headers,
                json={
                    "question": question,
                    "document_ids": document_ids,
                    "source_mode": "pdf",
                },
                timeout=self.query_timeout_seconds,
            ) as response:
                if response.is_error:
                    response.read()
                    self._json(response)
                result: dict[str, Any] | None = None
                for event, payload in self._iter_sse(response):
                    if event == "progress":
                        on_progress(payload)
                    elif event == "error":
                        raise ApiError(payload.get("message", "The query failed"))
                    elif event == "result":
                        result = payload
                if result is None:
                    raise ApiError("Backend query stream ended without a result")
                return result
        except httpx.RequestError as exc:
            raise ApiError("Could not reach the backend query API") from exc

    def list_documents(self) -> list[dict[str, Any]]:
        try:
            response = httpx.get(
                f"{self.base_url}/documents", headers=self._headers, timeout=30
            )
        except httpx.RequestError as exc:
            raise ApiError("Could not reach the backend document API") from exc
        return self._json(response)["documents"]

    @staticmethod
    def _json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiError(f"Backend returned HTTP {response.status_code}") from exc
        if response.is_error:
            message = payload.get("message", f"Backend returned HTTP {response.status_code}")
            raise ApiError(message)
        return payload

    @staticmethod
    def _iter_sse(response: httpx.Response):
        event = "message"
        data_lines: list[str] = []
        for line in response.iter_lines():
            if not line:
                if data_lines:
                    yield event, json.loads("\n".join(data_lines))
                event = "message"
                data_lines = []
            elif line.startswith("event:"):
                event = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        if data_lines:
            yield event, json.loads("\n".join(data_lines))
