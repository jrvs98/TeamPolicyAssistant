# Team Policy Assistant

## Description

Team Policy Assistant is a production-style internal application for helping employees find reliable answers in company policy documents. Administrators upload PDF or Markdown policies, and employees ask questions through a protected web application.

The assistant is designed around retrieval-augmented generation (RAG): it finds relevant policy sections, generates an answer using only the retrieved evidence, and shows citations back to the source document. When the available evidence is insufficient, it should refuse to guess. Employees can provide feedback on answers so the system can be evaluated and improved.

The planned application has two roles:

- `admin`: uploads documents, monitors indexing, retries failed ingestion, and runs evaluations.
- `employee`: signs in, asks policy questions, reads cited answers, and submits feedback.
 
The project uses FastAPI for APIs, React and TypeScript for the web interface, PostgreSQL with pgvector for document retrieval, RabbitMQ for asynchronous ingestion, Keycloak for OAuth/OIDC authentication, and LangGraph for the bounded answer workflow. The current setup is local-first and does not require a paid AI provider until model-based features are enabled.

## Local setup

Prerequisites: Docker Desktop, Python 3.12+, and Node.js 20+.

### Start the full local stack

```bash
cp .env.example .env
docker compose up -d --build
```

This starts the full development stack in Docker:

- API: http://localhost:8000
- Frontend: http://localhost:8081
- RabbitMQ UI: http://localhost:15672
- Keycloak: http://localhost:8080
- PostgreSQL: localhost:5432
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### Run the backend directly for local development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Run the worker directly

```bash
cd backend
../backend/.venv/bin/python worker.py
```

### Run the frontend directly

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The AI provider defaults to `none`, so setup does not require a paid API. Configure a provider only when implementing the RAG workflow.

Keycloak imports a development realm with the `admin` and `employee` roles. The test users are `admin.user` / `admin_dev_only` and `employee.user` / `employee_dev_only`. These credentials are for local development only.

The Keycloak client is configured for both the Vite origin (`http://localhost:5173`) and the Dockerized frontend (`http://localhost:8081`) so the OAuth redirect works in local development.

The initial document management endpoints are admin-only:

- `POST /api/v1/documents` uploads a PDF or Markdown file to `data/uploads`.
- `GET /api/v1/documents` lists uploaded documents and their processing status.
- `POST /api/v1/documents/{id}/retry` republishes an uploaded or failed document.

Uploads are limited to 10 MB by default. RabbitMQ ingestion and OCR processing consume uploaded documents asynchronously.

After signing in as `admin.user`, the frontend displays the document library and upload form. The frontend calls the API and sends the Keycloak access token automatically.

The ingestion worker reads Markdown and PDFs, normalizes and chunks their text, stores chunks and 1536-dimensional local development embeddings in PostgreSQL, and changes the document status to `indexed`. Image-only PDF pages use local Tesseract OCR; empty or unreadable documents become `failed` with a stored failure reason. The local embedder is deterministic and keeps setup free; it is a development placeholder for a semantic model provider. Local OCR requires the Tesseract executable, while the backend Dockerfile installs it automatically.

Authenticated users can search indexed policy chunks with `POST /api/v1/questions/search` using `{"query":"remote work","limit":5}`. Results include the matching text, source filename, page number when available, and vector distance.

The authenticated frontend includes a policy search panel for both employees and administrators. It displays ranked source passages and citation metadata, and the answer flow is powered by the grounded retrieval workflow.

RabbitMQ publishes `document.uploaded.v1` events to the durable `policy.events` exchange and `policy.document-ingestion` queue. The worker process consumes those events and stores the resulting chunks and embeddings in PostgreSQL.

## Roadmap slices

1. Add database migrations and authentication.
2. Add document storage, OCR fallback, and asynchronous ingestion.
3. Add retrieval, configurable embeddings, LangGraph, citations, and SSE.
4. Add evaluation, observability, and deployment manifests.
