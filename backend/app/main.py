from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from pydantic import BaseModel

from app.database import get_db, init_db
from app.models import Document, DocumentChunk
from app.services import extract_text_from_pdf, chunk_text, generate_embeddings


@asynccontextmanager
async def lifespan(app:FastAPI):
    # starting logic
    init_db()
    yield
    # Shutdown logic 

app = FastAPI(title="Enterprise Document Intelligence & Semantic Search Engine",
              version="1.0.0",
              lifespan=lifespan
 )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "enterprise-doc-engine"}

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), db:Session =Depends(get_db)):
    contents = await file.read()

    if file.filename.endswith(".pdf"):
        extract_text = extract_text_from_pdf(contents)
    elif file.filename.endswith(".txt"):
        extract_text = contents.decode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files supported.")

    if not extract_text.strip():
        raise HTTPException(status_code=400, detail="Document contains no readable text.")

    # Save Document metadata
    doc_record = Document(filename = file.filename, file_type=file.content_type or "unknown")
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # Chunk text & generate embeddings
    chunks = chunk_text(extract_text)
    embeddings = generate_embeddings(chunks)

    # Store chunks & vectors in postgresql 
    chunk_records = [
        DocumentChunk(
            document_id=doc_record.id,
            chunk_index=i,
            content = chunk,
            embedding = emb
        )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]
    db.add_all(chunk_records)
    db.commit()

    return {
        "message": "Document indexed successfully",
        "document_id": doc_record.id,
        "filename": doc_record.filename,
        "chunks_created": len(chunks)
    }

class SearchRequest(BaseModel):
    query: str
    top_k: int =3


@app.post("/documents/search")
def search_documents(request: SearchRequest, db: Session = Depends(get_db)):
    query_vector = generate_embeddings([request.query])[0]

    query = text("""
        SELECT c.id, c.document_id, c.content, d.filename,
                1 - (c.embedding <=> :query_embedding) AS similarity_score
        FROM document_chunks c
        JOIN documents d ON c.document_id = d.id
        ORDER BY c.embedding <=> :query_embedding ASC
        LIMIT :top_k;
    """)

    results = db.execute(
        query,
        {"query_embedding": str(query_vector), "top_k": request.top_k}
    ).fetchall()

    return {
        "query": request.query,
        "results": [
            {
                "chunk_id": row[0],
                "document_id": row[1],
                "content": row[2],
                "filename": row[3],
                "similarity_score": round(float(row[4]), 4)
            }
            for row in results
        ]
    }