"""Streamlit frontend entry point for PDF uploads."""

from uuid import UUID

import streamlit as st
from api_client import ApiClient
from config import FrontendSettings
from pages.documents_page import render

st.set_page_config(page_title="Multi-PDF RAG", page_icon="📚", layout="wide")
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

client = ApiClient(
    base_url=settings.backend_base_url,
    owner_id=owner_id,
    upload_timeout_seconds=settings.upload_timeout_seconds,
    query_timeout_seconds=settings.query_timeout_seconds,
)
render(client)
