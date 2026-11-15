"""Ask questions, stream progress, and render validated answers with citations."""

from __future__ import annotations

from uuid import UUID

import streamlit as st
from api_client import ApiClient, ApiError
from config import FrontendSettings

_QUERY_PROGRESS = {
    "retrieving": (10, "Retrieving relevant chunks"),
    "context_ready": (35, "Preparing evidence context"),
    "waiting_for_generation": (45, "Waiting for generation capacity"),
    "generating": (60, "Generating grounded answer"),
    "validating": (80, "Validating citations"),
    "repairing": (90, "Repairing citations"),
    "completed": (100, "Answer ready"),
}


def _client() -> ApiClient:
    settings = FrontendSettings.from_env()
    st.sidebar.header("Development identity")
    owner_value = st.sidebar.text_input(
        "Owner UUID",
        value="11111111-1111-1111-1111-111111111111",
        help="Temporary until JWT login is implemented.",
    )
    try:
        owner_id = UUID(owner_value)
    except ValueError:
        st.error("Owner UUID is invalid.")
        st.stop()
    return ApiClient(
        base_url=settings.backend_base_url,
        owner_id=owner_id,
        upload_timeout_seconds=settings.upload_timeout_seconds,
        query_timeout_seconds=settings.query_timeout_seconds,
    )


def _render_result(result: dict) -> None:
    st.subheader("Answer")
    if result["status"] == "abstained":
        st.warning(result.get("abstention_reason") or "No supported answer was found.")
    elif result.get("answer_markdown"):
        st.markdown(result["answer_markdown"])

    limitations = result.get("limitations") or []
    if limitations:
        with st.expander("Limitations"):
            for limitation in limitations:
                st.write(f"- {limitation}")

    evidence = result.get("cited_evidence") or []
    st.subheader("Sources")
    if not evidence:
        st.caption("No sources were cited.")
    for item in evidence:
        pages = ", ".join(str(page) for page in item["page_numbers"])
        title = f"[{item['evidence_id']}] {item['filename']} - page {pages}"
        with st.expander(title):
            if item.get("section_title"):
                st.caption(f"Section: {item['section_title']}")
            st.write(item["text"])
            st.caption(f"Similarity: {item['similarity']:.3f}")

    usage = result.get("usage")
    if usage:
        st.caption(
            f"Model: {usage['model']} · input tokens: {usage.get('input_tokens') or 'n/a'} · "
            f"output tokens: {usage.get('output_tokens') or 'n/a'} · "
            f"generation: {usage['latency_ms']} ms"
        )


st.set_page_config(page_title="Research - Multi-PDF RAG", page_icon="🔎", layout="wide")
client = _client()

st.title("Research your PDFs")
st.write("Select indexed documents, ask a question, and receive a citation-validated answer.")

try:
    ready_documents = [
        document for document in client.list_documents() if document.get("status") == "ready"
    ]
except (ApiError, OSError, TimeoutError) as exc:
    st.error(str(exc))
    st.stop()

if not ready_documents:
    st.info("Upload and index at least one PDF before asking a question.")
    st.stop()

labels = {
    document["document_id"]: f"{document['filename']} ({document['chunk_count']} chunks)"
    for document in ready_documents
}
selected_documents = st.multiselect(
    "Documents",
    options=list(labels),
    default=list(labels),
    format_func=labels.__getitem__,
)
question = st.text_area(
    "Question",
    placeholder="What components make up a solar electric system?",
    height=100,
)

if st.button(
    "Ask",
    type="primary",
    disabled=not selected_documents or not question.strip(),
):
    progress_bar = st.progress(0, text="Starting query - 0%")

    def update_progress(event):
        percent, message = _QUERY_PROGRESS.get(
            event["stage"], (0, event["stage"].replace("_", " ").title())
        )
        progress_bar.progress(percent, text=f"{message} - {percent}%")

    try:
        query_result = client.query_stream(
            question.strip(), selected_documents, update_progress
        )
    except (ApiError, OSError, TimeoutError) as exc:
        progress_bar.empty()
        st.error(str(exc))
    else:
        progress_bar.progress(100, text="Answer ready - 100%")
        _render_result(query_result)
