"""Upload and list PDF data sources through the backend API."""

from __future__ import annotations

import streamlit as st
from api_client import ApiClient, ApiError
from components.document_status import render_document


def render(client: ApiClient) -> None:
    st.title("PDF data sources")
    st.write("Upload text-readable PDFs. Scanned and encrypted PDFs are not supported yet.")

    uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False)
    if st.button("Upload and index", type="primary", disabled=uploaded is None):
        assert uploaded is not None
        progress_bar = st.progress(0, text="Uploading PDF - 0%")

        def update_progress(event):
            percent = int(event["percent"])
            progress_bar.progress(percent, text=f"{event['message']} - {percent}%")

        try:
            result = client.upload_pdf_stream(uploaded.name, uploaded, update_progress)
        except (ApiError, OSError, TimeoutError) as exc:
            progress_bar.empty()
            st.error(str(exc))
        else:
            progress_bar.progress(100, text="Ready - 100%")
            if result.get("reused"):
                st.info("This PDF was already indexed; the ready version was reused.")
            else:
                st.success(
                    f"Indexed {result['filename']} into {result['chunk_count']} chunks."
                )

    st.subheader("Indexed PDFs")
    try:
        documents = client.list_documents()
    except (ApiError, OSError, TimeoutError) as exc:
        st.error(str(exc))
        return
    if not documents:
        st.info("No PDFs have been uploaded for this owner yet.")
        return
    for document in documents:
        render_document(document)
