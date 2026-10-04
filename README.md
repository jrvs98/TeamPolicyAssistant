# Team Policy Assistant

## Description

Team Policy Assistant is a production-style internal application for helping employees find reliable answers in company policy documents. Administrators upload PDF or Markdown policies, and employees ask questions through a protected web application.

The assistant retrieves relevant policy sections, builds an extractive answer from their text, and shows citations back to the source document. It returns a fallback response when no passages are found, the best match exceeds the distance threshold, or the extracted answer is empty. Employees can provide feedback on answers so the system can be evaluated and improved.

The application has two roles:

- `admin`: uploads documents, monitors indexing, retries failed ingestion, and runs evaluations.
- `employee`: signs in, asks policy questions, reads cited answers, and submits feedback.
 
The project uses FastAPI for APIs, React and TypeScript for the web interface, PostgreSQL with pgvector for document retrieval, RabbitMQ for asynchronous ingestion, and Keycloak for OAuth/OIDC authentication. The current answer workflow is implemented in Python; LangGraph and model-based generation remain planned. The local setup does not require a paid AI provider.

## Local setup

Prerequisite for the Docker stack: Docker Desktop with Docker Compose. Running services directly also requires Python 3.12+ for the backend and Node.js 20+ for the frontend.

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

From the repository root, start the infrastructure services. If the full stack is already running, stop its API and worker before running them directly to avoid a port conflict and competing ingestion workers.

```bash
docker compose stop api worker
docker compose up -d postgres rabbitmq keycloak
```

Then create the backend environment. Settings load `.env` from the current working directory, so copy the example into `backend/.env` and adjust it for any custom local settings. The defaults point to the infrastructure ports on localhost. Leave `KEYCLOAK_AUDIENCE` unset unless audience validation is required; remove the empty example entry.

```bash
cd backend
cp ../.env.example .env
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
.venv/bin/python worker.py
```

### Run the frontend directly

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend development server runs at http://localhost:5173. The direct backend defaults to allowing this origin; the Docker API allows http://localhost:8081. Set `FRONTEND_ORIGIN` to match the frontend when mixing direct and Docker services.

`AI_PROVIDER` defaults to `none`. Model-based generation is not implemented, and changing this setting does not enable it. `EMBEDDING_PROVIDER=local` is the only supported embedding provider; the default embedding dimension is 1536.

Keycloak imports a development realm with the `admin` and `employee` roles. The test users are `admin.user` / `admin_dev_only` and `employee.user` / `employee_dev_only`. These credentials are for local development only.

The Keycloak client is configured for both the Vite origin (`http://localhost:5173`) and the Dockerized frontend (`http://localhost:8081`) so the OAuth redirect works in local development.

## Document ingestion

The document management endpoints are admin-only:

- `POST /api/v1/documents` uploads a PDF or Markdown file to `data/uploads`.
- `GET /api/v1/documents` lists uploaded documents and their processing status.
- `POST /api/v1/documents/{id}/retry` republishes an uploaded or failed document.

Uploads are limited to 10 MB by default. RabbitMQ ingestion and OCR processing consume uploaded documents asynchronously.

After signing in as `admin.user`, the frontend displays the document library and upload form. The frontend calls the API and sends the Keycloak access token automatically.

The ingestion worker reads Markdown and PDFs, normalizes and chunks their text, stores chunks and 1536-dimensional local development embeddings in PostgreSQL, and changes the document status to `indexed`. Image-only PDF pages use local Tesseract OCR; empty or unreadable documents become `failed` with a stored failure reason. The local embedder is deterministic and keeps setup free; it is a development placeholder for a semantic model provider. Local OCR requires the Tesseract executable, while the backend Dockerfile installs it automatically.

RabbitMQ publishes `document.uploaded.v1` events to the durable `policy.events` exchange and `policy.document-ingestion` queue. The worker process consumes those events and stores the resulting chunks and embeddings in PostgreSQL.

## Search, answers, and feedback

The frontend provides search, cited answers, and helpful/unhelpful feedback for both employees and administrators. API requests include the Keycloak bearer token automatically.

- `POST /api/v1/questions/search` searches indexed policy chunks using `{"query":"remote work","limit":5}`. Results include passage text, source filename, page number when available, and cosine distance.
- `POST /api/v1/questions` accepts the same request shape, persists the question and answer, and returns `question_id`, `answer_id`, `answer`, `route`, and up to three source citations. The route is `extractive` or `fallback`.
- `POST /api/v1/answers/{answer_id}/feedback` accepts `{"value":"helpful"}` or `{"value":"unhelpful"}`, with an optional `comment` of up to 2000 characters.

These endpoints require authentication. The local answer workflow selects sentences from up to three retrieved passages. It does not call an LLM or perform a separate model-based verification step.

`GET /api/v1/questions/{question_id}/events` currently emits a fixed sequence of SSE step events followed by `done`. It does not validate the question ID, require authentication, or report live execution. The frontend uses the synchronous answer endpoint.

## Admin evaluations

- `GET /api/v1/admin/evaluations` lists evaluation cases and seeds three default cases when the table is empty.
- `POST /api/v1/admin/evaluations/run` runs the stored cases, persists results, and returns case scores, passed-case count, and average score.

Both endpoints require the `admin` role and are currently API-only. Evaluation scoring uses retrieval availability and the refusal distance threshold; it does not yet assess generated answer quality or compare expected answers and document IDs.

## Health and observability

- `GET /health` reports API liveness.
- `GET /ready` checks database connectivity and returns HTTP 503 when the database is unavailable.
- API responses include `X-Request-ID`, and request middleware emits log records with request metadata.

Docker Compose includes Prometheus and Grafana with a provisioned datasource and dashboard. Grafana development credentials are `admin` / `admin_dev_only`. Prometheus currently scrapes itself; API and worker metrics endpoints and scrape targets remain to be implemented.

API documentation is available at http://localhost:8000/docs.

## Development checks

With the backend virtual environment activated, run `pytest` and `ruff check .` from `backend`. From `frontend`, run `npm run lint` and `npm run build`.

## Remaining roadmap

Database migrations, authentication, asynchronous ingestion with OCR, local vector retrieval, extractive answers, citations, feedback, basic evaluations, request logging, and a Docker development stack are implemented.

1. Add semantic embedding providers and model-based generation with a bounded LangGraph workflow.
2. Replace fixed SSE events with authenticated progress tied to actual question execution.
3. Expand evaluation scoring to cover answer quality and expected sources.
4. Add API and worker metrics instrumentation and connect monitoring to application data.
5. Add production deployment configuration beyond the current Docker development stack.
