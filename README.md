## System Architecture & Live Previews

| Interactive Web Dashboard | Swagger API Execution |
|:---:|:---:|
| ![Dashboard Preview](assets/dashboard_preview.png) | ![Swagger API](assets/swagger_api.png) |

| CI/CD Pipeline (GitHub Actions) | Docker Multi-Container Orchestration |
|:---:|:---:|
| ![GitHub Actions](assets/github_actions_ci.png) | ![Docker Containers](assets/docker_containers.png) |



# Enterprise Document Intelligence & Semantic Search Engine

A production-grade, containerized semantic search and document parsing pipeline built with **FastAPI**, **PostgreSQL (pgvector)**, and **Sentence-Transformers**. It ingests unstructured text/PDF documents, creates high-dimensional vector embeddings locally, and executes cosine similarity searches in PostgreSQL.

---

## Architecture Overview

```text
 ┌────────────────────────────────────────┐
 │   Interactive Web Dashboard (UI) / API  │
 └───────────────────┬────────────────────┘
                     │
 ┌───────────────────▼────────────────────┐
 │         FastAPI Orchestrator           │  <── Multi-stage Lean Build
 │    (Ingest / Chunk / Embed / Serve)    │
 └─────────────┬─────────────────┬────────┘
               │                 │
 ┌─────────────▼──────────────┐  │
 │ PostgreSQL 16 + pgvector   │  │
 │   (Relational + Vectors)   │  │
 └────────────────────────────┘  │
       ┌─────────────────────────▼────────────┐
       │ SentenceTransformer (all-MiniLM-L6-v2)│
       └──────────────────────────────────────┘
```


## Tech Stack

API Engine & Serving: FastAPI, Pydantic, Uvicorn

Database & Vector Store: PostgreSQL 16 with pgvector

Frontend: TailwindCSS, HTML5, Vanilla JavaScript

ORM: SQLAlchemy 2.0

Embeddings Model: sentence-transformers (all-MiniLM-L6-v2 - 384 dimensions)

Document Ingestion: pypdf

Containerization: Docker, Docker Compose (Multi-stage builds)

CI/CD: GitHub Actions (Pytest against PostgreSQL service container, Multi-stage Docker Build Verification)


## Key Features
Hybrid Relational & Vector Storage: Combines relational document metadata and vector embeddings in a single PostgreSQL instance.

Vector Indexing & Cosine Distance: Uses pgvector cosine operator (<=>) for low-latency semantic context retrieval.

Interactive Dashboard: Dark-mode dashboard for drag-and-drop document ingestion and semantic exploration.

Multi-Stage Dockerfile: Separates build dependencies (libpq-dev, build-essential) from runtime, optimizing image footprint.

Hot-Reloading in Development: Live mounted backend volume with instant reload capability.


## Quick Start with Docker
1. Clone the repository
```bash
git clone [https://github.com/codepundit24/enterprise-doc-intelligence.git](https://github.com/codepundit24/enterprise-doc-intelligence.git)
cd enterprise-doc-intelligence
```

## 2. Start the Application
```bash
docker compose up --build
```

## The services will initialize:

Interactive Web Dashboard: http://localhost:8000/

Interactive API Swagger Docs: http://localhost:8000/docs

PostgreSQL pgvector Database: localhost:5432

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

A GitHub Actions workflow (.github/workflows/ci.yml) runs on every push to main, validating code quality, running unit tests against a temporary pgvector service container, and building the production Docker image.

