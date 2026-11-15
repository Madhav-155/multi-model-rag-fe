# Multi-PDF RAG frontend

Standalone Streamlit client for the Multi-PDF RAG HTTP API. It communicates
with the backend only through versioned HTTP and Server-Sent Events endpoints;
it does not import backend packages or contain model/database credentials.

## Local setup

Run every command below from this directory:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
set -a
source .env
set +a
streamlit run streamlit/app.py --server.port 8501
```

Open http://127.0.0.1:8501. By default, the client expects the backend at
`http://127.0.0.1:8000/api/v1`.

## Configuration

- `RAG_BACKEND_BASE_URL` — public versioned backend URL
- `RAG_UPLOAD_TIMEOUT_SECONDS` — upload/ingestion request timeout
- `RAG_QUERY_UI_TIMEOUT_SECONDS` — research query timeout

The sidebar owner UUID is a temporary development identity, not production
authentication. Gemini keys, database credentials, uploaded PDFs, and backend
implementation code must never be placed in this repository.

## Project contents

- `streamlit/app.py` — application entry point
- `streamlit/pages/` — upload and research flows
- `streamlit/components/` — reusable presentation components
- `streamlit/api_client.py` — backend HTTP/SSE client
- `tests/` — frontend test boundaries
