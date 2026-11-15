"""Document lifecycle presentation."""

from __future__ import annotations

import streamlit as st


def render_document(document: dict) -> None:
    status = document.get("status") or "unknown"
    icon = {"ready": "✅", "processing": "⏳", "failed": "❌"}.get(status, "•")
    st.markdown(f"{icon} **{document['filename']}** — {status}")
    st.caption(
        f"{document.get('chunk_count', 0)} chunks · "
        f"document {document['document_id']}"
    )
