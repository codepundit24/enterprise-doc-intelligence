import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base, init_db
from app.models import DocumentChunk, Document
from sentence_transformers import SentenceTransformer

client = TestClient(app)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    yield
    db = SessionLocal()
    try:
        # Clean mock test records after test complete
        db.query(Document).filter(Document.filename == "pytest_sample.txt").delete()
        db.commit()
    finally:
        db.close()

# test health /root endpoint
def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "EnterpriseDocEngine" in response.text

# test document ingestion and chunk vectorization
def test_document_ingestion():
    mock_file_content = b"Microservices architecture with kubernetes enables horizontal auto-scaling and pod ressilience"
    file_obj = io.BytesIO(mock_file_content)

    response = client.post(
        "/documents/upload",
        files={"file": ("pytest_sample.txt", file_obj, " text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "pytest_sample.txt"
    assert data["chunks_created"]>0

# test pgvector semantic similarity retrieval
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

#Test fastmcp / agent route response integrity
def test_agent_chat_endpoint():
    response = client.post(
        "/agent/chat",
        json={"query":"Explain Kubernetes pod resilience"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "response" in json_data
    assert len(json_data["response"]) > 10

# Test crewAi multi agent endpoint contract
def test_crewai_endpoint_structure():
    response = client.post(
        "/crew/analyze",
        json={"query": " Summarize architecture features"}
    )
    assert response.status_code==200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert "analysis" in json_data
    assert "trace" in json_data
    assert json_data["trace"]["total_agents"] == 2