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

```bash
cp .env.example .env
docker compose up -d

cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Services:

- API: http://localhost:8000/docs
- Frontend: http://localhost:5173
- RabbitMQ management: http://localhost:15672
- Keycloak: http://localhost:8080
- PostgreSQL: localhost:5432

The AI provider defaults to `none`, so setup does not require a paid API. Configure a provider only when implementing the RAG workflow.

Keycloak imports a development realm with the `admin` and `employee` roles. The test users are `admin.user` / `admin_dev_only` and `employee.user` / `employee_dev_only`. These credentials are for local development only.

## Roadmap slices

1. Add database migrations and authentication.
2. Add document storage, OCR fallback, and asynchronous ingestion.
3. Add retrieval, configurable embeddings, LangGraph, citations, and SSE.
4. Add evaluation, observability, and deployment manifests.
