# Team Policy Q&A Assistant — Project Roadmap

## 1. Project summary

Build a small production-style application where an administrator uploads company policy documents and employees ask questions about those policies.

The assistant retrieves relevant document sections from PostgreSQL with pgvector, generates a grounded answer through LangGraph, displays citations, and collects thumbs-up or thumbs-down feedback.

This project demonstrates:

- FastAPI
- React and TypeScript
- PostgreSQL with pgvector
- REST APIs and Server-Sent Events
- RabbitMQ
- OAuth 2.0 and OpenID Connect
- Docker
- Kubernetes and Helm
- CI/CD
- LangGraph
- RAG evaluation
- Observability

## 2. Scope

### Included in version 1

- One organization
- Two roles: `admin` and `employee`
- Keycloak login
- PDF and Markdown document uploads
- One shared knowledge base
- Asynchronous document ingestion
- Vector retrieval
- Cited answers
- Safe refusal when evidence is insufficient
- Answer feedback
- A small RAG evaluation dataset
- Metrics, logs, and traces
- Docker Compose development environment
- Basic Kubernetes deployment
- Continuous integration pipeline

### Deferred until later

- Multi-tenancy
- Multiple knowledge bases
- Complex document permissions
- Human-support escalation
- OCR and scanned documents
- Multiple model providers
- Advanced reranking
- Billing and quotas
- Slack or Teams integration
- Progressive production delivery

## 3. Technology stack

| Area | Technology |
|---|---|
| Backend | FastAPI, Python, SQLAlchemy, Alembic |
| Frontend | React, TypeScript, TanStack Query |
| Database | PostgreSQL with pgvector |
| Messaging | RabbitMQ |
| Authentication | Keycloak with OAuth 2.0 and OpenID Connect |
| AI workflow | LangGraph |
| Document storage | Local volume or MinIO |
| Observability | OpenTelemetry, Prometheus, Grafana |
| Local environment | Docker Compose |
| Deployment | Kubernetes and Helm |
| CI/CD | GitHub Actions |

## 4. Simplified architecture

```text
React Web Application
        |
        | OAuth/OIDC + REST/SSE
        v
FastAPI Application
   |        |          |
   |        |          +--> Keycloak
   |        |
   |        +--> PostgreSQL + pgvector
   |
   +--> RabbitMQ
           |
           +--> Ingestion Worker

FastAPI + Worker
        |
        +--> OpenTelemetry
                 |-- Prometheus
                 +-- Grafana
```

## 5. Core workflows

### Document ingestion

```text
Admin uploads document
    -> FastAPI validates role
    -> FastAPI stores the file
    -> FastAPI creates a document record
    -> FastAPI publishes document.uploaded.v1
    -> ingestion worker receives the event
    -> worker extracts and chunks the text
    -> worker creates embeddings
    -> worker stores chunks in pgvector
    -> document status changes to indexed
```

### Question answering

```text
Employee asks question
    -> FastAPI validates access token
    -> LangGraph retrieves document chunks
    -> LangGraph grades the retrieved context
    -> answer is generated from accepted context
    -> citations are verified
    -> answer and citations are streamed to React
    -> employee records feedback
```

## 6. Minimal LangGraph workflow

Use five bounded nodes:

1. `retrieve` — finds the most relevant document chunks.
2. `grade_context` — determines whether the retrieved evidence is sufficient.
3. `generate_answer` — answers using only the approved context.
4. `verify_answer` — confirms that claims are supported by citations.
5. `fallback` — refuses to answer when evidence is missing or unreliable.

Apply strict retry and timeout limits. Persist the selected chunk IDs, graph route, timing, and model usage for evaluation and debugging.

## 7. Minimal API

```text
GET    /api/v1/me

POST   /api/v1/documents
GET    /api/v1/documents
GET    /api/v1/documents/{id}
POST   /api/v1/documents/{id}/retry

POST   /api/v1/questions
GET    /api/v1/questions/{id}/events

POST   /api/v1/answers/{id}/feedback

GET    /api/v1/admin/evaluations
POST   /api/v1/admin/evaluations/run
```

Use REST for normal operations and Server-Sent Events for streaming generated answers.

## 8. Minimal data model

- `users`
- `documents`
- `document_chunks`
- `questions`
- `answers`
- `citations`
- `feedback`
- `evaluation_cases`
- `evaluation_results`

# Four-week implementation roadmap

This schedule assumes focused development over four weeks. If working part-time, treat each project week as one or two calendar weeks.

## Week 1 — Application foundation

### Goals

- Establish the repository and local environment.
- Implement authentication and role-based access.
- Connect the frontend, backend, and database.

### Tasks

#### Repository and development environment

- Create the backend, frontend, worker, and infrastructure directories.
- Add Docker Compose configuration.
- Run React, FastAPI, PostgreSQL, RabbitMQ, and Keycloak locally.
- Add environment-variable templates.
- Add health and readiness endpoints.
- Configure code formatting and linting.

#### Backend foundation

- Create the FastAPI application.
- Configure SQLAlchemy and Alembic.
- Enable the pgvector PostgreSQL extension.
- Create the initial user and document migrations.
- Add structured application logging.
- Publish an OpenAPI specification.

#### Authentication

- Configure a Keycloak realm.
- Create the React public client using Authorization Code with PKCE.
- Define `admin` and `employee` roles.
- Add test users for each role.
- Implement JWT validation in FastAPI.
- Add role-based API dependencies.

#### Frontend foundation

- Create the React and TypeScript application.
- Add sign-in and sign-out flows.
- Add protected routes.
- Create the application shell and navigation.
- Connect React to the FastAPI health and profile endpoints.

### Deliverable

Users can sign in and reach protected pages according to their assigned role.

### Completion checklist

- [ ] The local environment starts through Docker Compose.
- [ ] React can call FastAPI.
- [ ] FastAPI can access PostgreSQL and RabbitMQ.
- [ ] Database migrations succeed from a clean database.
- [ ] Unauthenticated API requests return `401`.
- [ ] Employee access to administrator endpoints returns `403`.
- [ ] Basic backend and frontend tests run in CI.

## Week 2 — Document ingestion

### Goals

- Allow administrators to upload documents.
- Process documents asynchronously through RabbitMQ.
- Store searchable vectors in PostgreSQL.

### Tasks

#### Document management

- Create document upload, list, detail, and retry endpoints.
- Validate file type and file size.
- Support PDF and Markdown documents.
- Store original files on a local volume or in MinIO.
- Add document states:
  - `uploaded`
  - `queued`
  - `processing`
  - `indexed`
  - `failed`
- Build the administrator upload and document-status screens.

#### RabbitMQ processing

- Create the `document.uploaded.v1` event contract.
- Configure durable exchanges and queues.
- Create the ingestion worker.
- Add message acknowledgment after successful processing.
- Add retry behavior and a dead-letter queue.
- Add idempotency so duplicate deliveries do not duplicate chunks.
- Include correlation and trace IDs in message headers.

#### Extraction and indexing

- Extract text from PDF and Markdown files.
- Normalize whitespace and metadata.
- Divide text into configurable overlapping chunks.
- Generate embeddings.
- Store content, metadata, and vectors in PostgreSQL.
- Mark the document as indexed after a successful transaction.
- Record a clear failure reason when processing fails.

### Deliverable

An administrator can upload a document and watch it progress asynchronously from `uploaded` to `indexed`.

### Completion checklist

- [ ] PDF and Markdown uploads work.
- [ ] Employees cannot upload documents.
- [ ] RabbitMQ messages survive a worker restart.
- [ ] Duplicate delivery does not create duplicate chunks.
- [ ] Failed messages reach a dead-letter queue after limited retries.
- [ ] An indexed document has searchable vector records.
- [ ] The UI displays processing status and failure information.

## Week 3 — RAG question answering

### Goals

- Retrieve relevant policy sections.
- Generate answers with verifiable citations.
- Provide a usable chat experience and feedback mechanism.

### Tasks

#### Retrieval

- Implement pgvector similarity search.
- Retrieve the top candidate chunks.
- Add simple metadata filters for active documents.
- Record retrieval scores and latency.
- Add a retrieval-debug endpoint available only to administrators.

#### LangGraph

- Implement the five workflow nodes.
- Add context-quality grading.
- Restrict generation to retrieved evidence.
- Verify that citations reference retrieved chunks.
- Add a safe refusal response.
- Set graph, retrieval, and model timeouts.
- Persist each graph route and selected chunk IDs.

#### API and frontend

- Add the question endpoint.
- Stream progress and answer tokens with Server-Sent Events.
- Persist questions, answers, and citations.
- Build the React question-and-answer screen.
- Display document names and cited passages.
- Add thumbs-up and thumbs-down feedback.
- Show a clear message when the assistant cannot answer.

### Deliverable

Employees can ask questions and receive streamed answers supported by clickable citations.

### Completion checklist

- [ ] Relevant policy questions receive grounded answers.
- [ ] Each factual answer contains at least one valid citation.
- [ ] Citations reference chunks used during generation.
- [ ] Unsupported questions trigger the safe fallback.
- [ ] Model or retrieval failures produce a controlled error state.
- [ ] Feedback is persisted with the associated answer and run.
- [ ] Retrieval and graph behavior have automated tests.

## Week 4 — Evaluation, observability, and deployment

### Goals

- Measure RAG quality.
- Make application behavior observable.
- Package and deploy the application.
- Establish automated quality gates.

### Tasks

#### RAG evaluation

- Create 20–30 representative evaluation cases.
- Include answerable policy questions.
- Include questions with expected source documents.
- Include questions that should be refused.
- Measure retrieval recall@5.
- Measure answer correctness or required-fact coverage.
- Measure citation correctness.
- Measure refusal accuracy.
- Record latency and token usage.
- Produce a versioned evaluation report.

#### Observability

- Instrument FastAPI and the worker with OpenTelemetry.
- Trace HTTP requests, database operations, RabbitMQ messages, and LangGraph nodes.
- Export metrics to Prometheus.
- Create a Grafana dashboard.
- Measure API errors and latency.
- Measure queue depth and message age.
- Measure ingestion failures and duration.
- Measure retrieval and model latency.
- Redact tokens, document content, and personal information from logs.

#### Packaging and Kubernetes

- Create production Dockerfiles for React, FastAPI, and the worker.
- Run containers as non-root users.
- Create a basic Helm chart.
- Add deployments and services.
- Add health probes and resource limits.
- Configure application secrets through Kubernetes secret references.
- Add a database migration job.
- Deploy to a local Kubernetes cluster.

#### CI/CD

- Run formatting and linting checks.
- Run unit and integration tests.
- Start PostgreSQL and RabbitMQ for integration tests.
- Run a small RAG evaluation subset.
- Build and scan container images.
- Generate an SBOM.
- Publish versioned images after a successful main-branch build.
- Optionally deploy automatically to a development namespace.

### Deliverable

The application is tested, observable, containerized, and deployable to Kubernetes.

### Completion checklist

- [ ] The golden dataset contains at least 20 reviewed cases.
- [ ] Evaluation results are stored and comparable between runs.
- [ ] A trace connects an API request to LangGraph and database operations.
- [ ] RabbitMQ processing exposes useful metrics.
- [ ] Grafana displays health, latency, and ingestion information.
- [ ] The Helm release installs successfully in a clean namespace.
- [ ] CI blocks changes that fail tests or minimum RAG thresholds.

## 9. Testing strategy

### Unit tests

- Role and authorization rules
- File validation
- Chunking behavior
- LangGraph routing
- Safe refusal decisions
- Citation validation

### Integration tests

- PostgreSQL and pgvector retrieval
- RabbitMQ publishing and consumption
- Document processing
- Database migrations
- JWT validation

### End-to-end tests

- Administrator login and document upload
- Employee login and question submission
- Answer streaming
- Citation display
- Feedback submission

### RAG evaluation tests

- Retrieval quality
- Answer correctness
- Groundedness
- Citation correctness
- Refusal behavior

## 10. Initial quality targets

| Metric | Initial target |
|---|---:|
| Golden evaluation questions | 20–30 |
| Retrieval recall@5 | At least 80% |
| Citation correctness | At least 90% |
| Unauthorized administrator operations | 0 |
| Supported document formats | 2 |
| RabbitMQ consumers | 1 |
| Ingestion success rate | At least 98% |
| Critical security findings | 0 |

These are starting targets. Adjust them after evaluating representative documents and realistic questions.

## 11. Recommended repository layout

```text
team-policy-assistant/
├── apps/
│   ├── api/
│   ├── web/
│   └── ingestion-worker/
├── packages/
│   ├── auth/
│   ├── rag/
│   ├── messaging/
│   └── observability/
├── infra/
│   ├── docker/
│   ├── helm/
│   ├── keycloak/
│   └── monitoring/
├── tests/
│   ├── integration/
│   ├── end-to-end/
│   └── evaluation/
└── .github/workflows/
```

## 12. Definition of done

Version 1 is complete when:

- [ ] Administrators and employees can sign in through Keycloak.
- [ ] Role restrictions are enforced by FastAPI.
- [ ] Administrators can upload PDF and Markdown files.
- [ ] RabbitMQ triggers reliable asynchronous ingestion.
- [ ] The worker stores document chunks and embeddings in pgvector.
- [ ] Employees receive streamed answers with valid citations.
- [ ] Unsupported questions receive a safe refusal.
- [ ] Users can rate answers.
- [ ] At least 20 evaluation cases run automatically.
- [ ] Metrics and traces are visible in Grafana.
- [ ] Docker Compose reproduces the local environment.
- [ ] Helm deploys the application to Kubernetes.
- [ ] CI runs tests, evaluation checks, and image builds.

## 13. Critical path

```text
Authentication
    -> document upload
    -> RabbitMQ ingestion
    -> pgvector indexing
    -> retrieval
    -> LangGraph answers
    -> evaluation
    -> observability
    -> Kubernetes deployment
```

Finish the complete upload-to-answer workflow before adding optional integrations or advanced agent behavior.
