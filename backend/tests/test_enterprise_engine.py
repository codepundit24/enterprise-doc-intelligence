import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base, init_db
from app.models import Document, DocumentChunk
from sentence_transformers import SentenceTransformer

client = TestClient(app)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    yield
    db = SessionLocal()
    try:
        db.query(Document).filter(Document.filename == "pytest_sample.txt").delete()
        db.commit()
    finally:
        db.close()

# 1. Test Health / Root UI Endpoint
def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "EnterpriseDocEngine" in response.text

# 2. Test Document Ingestion & Chunk Vectorization
def test_document_ingestion():
    mock_file_content = b"Microservices architecture with Kubernetes enables horizontal auto-scaling and pod resilience."
    file_obj = io.BytesIO(mock_file_content)

    response = client.post(
        "/documents/upload",
        files={"file": ("pytest_sample.txt", file_obj, "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "pytest_sample.txt"
    assert data["chunks_created"] > 0

# 3. Test pgvector Semantic Similarity Retrieval
def test_vector_similarity_search():
    db = SessionLocal()
    try:
        query_vec = embedding_model.encode("Kubernetes auto-scaling").tolist()
        match = (
            db.query(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.filename == "pytest_sample.txt")
            .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
            .first()
        )
        assert match is not None
        assert "horizontal auto-scaling" in match.content
    finally:
        db.close()

# 4. Test LangGraph Agent Endpoint (Mocking Ollama HTTP Dependency)
def test_agent_chat_endpoint():
    mock_response = "Kubernetes provides high availability and automated failover for application pods."
    with patch("app.agents.langgraph_agent.app_workflow.invoke", return_value={"final_answer": mock_response}):
        response = client.post(
            "/agent/chat",
            json={"query": "Explain Kubernetes pod resilience"}
        )
        assert response.status_code == 200
        json_data = response.json()
        assert "response" in json_data
        assert len(json_data["response"]) > 10

# 5. Test CrewAI Multi-Agent Endpoint Contract (Mocking OpenAI API Calls)
def test_crewai_endpoint_structure():
    mock_crew_output = {
        "analysis": "Executive Overview: Architecture features verified.",
        "trace": {
            "framework": "CrewAI (Sequential Multi-Agent Process)",
            "pipeline": [
                {"agent": "Senior Technical Researcher", "action": "Searched pgvector", "status": "Done"},
                {"agent": "Principal Enterprise Consultant", "action": "Formatted summary", "status": "Done"}
            ],
            "total_agents": 2
        }
    }
    with patch("app.agents.crew_analyst.run_crew_pipeline", return_value=mock_crew_output):
        response = client.post(
            "/crew/analyze",
            json={"query": "Summarize architecture features"}
        )
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "success"
        assert "analysis" in json_data
        assert "trace" in json_data
        assert json_data["trace"]["total_agents"] == 2