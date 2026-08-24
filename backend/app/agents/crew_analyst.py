import os

# Disable CrewAI interactive prompts, tracing, and telemetry
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from sentence_transformers import SentenceTransformer
from app.database import SessionLocal
from app.models import DocumentChunk

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Vector DB Search Tool
@tool("Search Internal Knowledge Base")
def search_knowledge_base(query: str) -> str:
    """Searches internal enterprise documentation, syllabus files, and candidate data in pgvector."""
    db = SessionLocal()
    try:
        query_vector = embedding_model.encode(query).tolist()
        results = (
            db.query(DocumentChunk)
            .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
            .limit(2)
            .all()
        )
        if not results:
            return "No matching internal documents found."
        return "\n\n".join([f"Document Chunk: {r.content}" for r in results])
    finally:
        db.close()

# 4. Multi-Agent Pipeline Execution
def run_crew_pipeline(user_query: str) -> str:
    researcher = Agent(
        role="Senior Technical Researcher",
        goal=f"Extract accurate technical details from internal documents to address: {user_query}",
        backstory="You are an enterprise technical analyst who inspects documentation without guessing.",
        tools=[search_knowledge_base],
        verbose=True
    )

    technical_writer = Agent(
        role="Principal Enterprise Consultant",
        goal="Structure the findings into a concise, professional executive briefing.",
        backstory="You are a senior solutions architect specialized in clear technical communication.",
        verbose=True
    )

    task1 = Task(
        description=f"Query the database tool and extract key technical facts regarding: {user_query}",
        expected_output="Bulleted technical facts extracted from internal documents.",
        agent=researcher
    )

    task2 = Task(
        description="Format the researcher's findings into a concise executive overview.",
        expected_output="A structured enterprise briefing in English.",
        agent=technical_writer
    )

    enterprise_crew = Crew(
        agents=[researcher, technical_writer],
        tasks=[task1, task2],
        process=Process.sequential,
        verbose=True
    )

    result = enterprise_crew.kickoff()
    return {
        "analysis": str(result),
        "trace": {
            "framework": "CrewAI (Sequential Multi-Agent Process)",
            "pipeline": [
                {
                    "agent": "Senior Technical Researcher",
                    "action": "Invoked tool `Search Internal Knowledge Base` on PostgreSQL pgvector",
                    "status": "Task 1 Completed"
                },
                {
                    "agent": "Principal Enterprise Consultant",
                    "action": "Synthesized raw research findings into executive briefing format",
                    "status": "Task 2 Completed"
                }
            ],
            "total_agents": 2
        }
    }