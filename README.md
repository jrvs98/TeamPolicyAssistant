# Team Policy Assistant

A FastAPI, React, PostgreSQL/pgvector, RabbitMQ, and Keycloak foundation for a grounded policy Q&A assistant.

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

## Roadmap slices

1. Add database migrations and authentication.
2. Add document storage, OCR fallback, and asynchronous ingestion.
3. Add retrieval, configurable embeddings, LangGraph, citations, and SSE.
4. Add evaluation, observability, and deployment manifests.
