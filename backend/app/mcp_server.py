from fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
from app.database import SessionLocal
from app.models import DocumentChunk

# Initialize fastmcp instance
mcp = FastMCP("EnterpriseDockerEngine")

# Local Embedding Model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

@mcp.tool()
def searche_internal_knowledge_base(query:str, top_k: int=3) -> str:
    """
    Searches the Enterprise PostgreSQL pgvector database for private documents, 
    codebases, architecture notes, and uploaded syllabi.
    
    Args:
        query: The search question or keyword.
        top_k: Number of relevant chunks to retrieve (default: 3)
    """
    db = SessionLocal()
    try:
        query_vector = embedding_model.encode(query).tolist()
        results = (
            db.query(DocumentChunk)
            .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
            .limit(top_k)
            .all()
        )

        if not results:
            return "No matching internal documentation found"

        formatted_results = []
        for i, r in enumerate(results, 1):
            formatted_results.append(f"[Results {i}]\n{r.content}")

        return "\n\n---\n\n".join(formatted_results)
    finally:
        db.close()

if __name__== "__main__":

    # Run the standard mcp server over stdio for ai clients
    mcp.run()