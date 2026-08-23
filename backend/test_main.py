from fastapi.testclient import TestClient
from app.main import app

client = TestClient()

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "enterprise-doc-engine"
    }

def test_invalid_document_type():
    # Attempt to upload an unsupported format
    files = {'file': ('test.exe', b'malicious_content', 'application/octet-stream')}
    response = client.post("/documents/upload", files=files)
    assert response.status_code == 400