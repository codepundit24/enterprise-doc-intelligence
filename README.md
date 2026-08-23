# Enterprise Document Intelligence & Semantic Search Engine

A production-grade, containerized semantic search and document parsing pipeline built with **FastAPI**, **PostgreSQL (pgvector)**, and **Sentence-Transformers**. It ingests unstructured text/PDF documents, creates high-dimensional vector embeddings locally, and executes cosine similarity searches in PostgreSQL.

---

## Architecture Overview

```text
 ┌─────────────────────────┐
 │     Client / Swagger    │
 └────────────┬────────────┘
              │
 ┌────────────▼────────────┐
 │   FastAPI Orchestrator  │  <── Multi-stage Lean Build
 │ (Ingest / Chunk / Embed)│
 └─────┬─────────────┬─────┘
       │             │
 ┌─────▼──────────┐  │
 │ PostgreSQL 16  │  │
 │   + pgvector   │  │
 └────────────────┘  │
       ┌─────────────▼─────────┐
       │ SentenceTransformer   │
       │ (all-MiniLM-L6-v2)    │
       └───────────────────────┘
```


## Tech Stack
API Engine: FastAPI, Pydantic, Uvicorn

Database & Vector Store: PostgreSQL 16 with pgvector

ORM: SQLAlchemy 2.0

Embeddings: sentence-transformers (all-MiniLM-L6-v2 - 384 dimensions)

Document Parsing: pypdf

Containerization: Docker, Docker Compose (Multi-stage builds)

CI/CD: GitHub Actions (Pytest, Linting, Multi-stage Docker Build Verification)


## Key Features
Hybrid Data Storage: Combines relational document metadata with vector embeddings in a single PostgreSQL database instance.

Vector Indexing & Cosine Distance: Uses pgvector cosine operator (<=>) for low-latency semantic information retrieval.

Multi-Stage Dockerfile: Separates compilation tools (libpq-dev, build-essential) from the runtime stage, significantly reducing final image size.

Resilient Startup & Healthchecks: Automatic connection retry loops for database availability during container orchestration.

Hot-Reloading in Development: Live mounted backend volume with instant reload capability.

## Quick Start with Docker
1. Clone the repository
```bash
git clone [https://github.com/](https://github.com/)<your-username>/enterprise-doc-intelligence.git
cd enterprise-doc-intelligence
```

## 2. Start the Application
```bash
docker compose up --build
```

## The services will initialize:

API Service & Swagger UI: http://localhost:8000/docs

PostgreSQL: localhost:5432

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Application health and status verification |
| `POST` | `/documents/upload` | Upload `.pdf` or `.txt` files for chunking and vector indexing |
| `POST` | `/documents/search` | Query semantic search with natural language (`top_k` results) |


## Example Usage
1. Ingest a Document
```bash
curl -X 'POST' \
  'http://localhost:8000/documents/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample_report.pdf;type=application/pdf'
```

2. Semantic Search Query
```bash
curl -X 'POST' \
  'http://localhost:8000/documents/search' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What are the infrastructure requirements?",
    "top_k": 3
  }'

  ```

## Testing & CI/CD Pipeline
Unit tests verify endpoint status codes and file format validation.

```bash
# Run tests locally
pytest -v backend/test_main.py
```