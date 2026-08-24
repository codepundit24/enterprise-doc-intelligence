import re
import requests
from typing import TypedDict
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from sentence_transformers import SentenceTransformer
from app.database import get_db
from app.models import DocumentChunk

# 1. Models Setup
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

llm = ChatOllama(
    model="phi3",
    base_url="http://host.docker.internal:11434",
    temperature=0.1
)

# 2. State
class AgentState(TypedDict):
    query: str
    doc_context: str
    web_context: str
    final_answer: str

# 3. Vector DB Search Node
def retrieve_node(state: AgentState) -> dict:
    db = next(get_db())
    query_vector = embedding_model.encode(state["query"]).tolist()
    
    results = (
        db.query(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(2)
        .all()
    )
    context = "\n---\n".join([r.content for r in results]) if results else "No relevant local documents found."
    return {"doc_context": context}

# 4. Dynamic Wikipedia REST API Search Node
def web_search_node(state: AgentState) -> dict:
    web_text = "No external encyclopedia search performed."
    query = state["query"]
    
    # Check if query is seeking general/technical knowledge
    triggers = ["what is", "who is", "explain", "overview", "history", "architecture", "kubernetes", "docker", "fastapi", "devops"]
    
    if any(k in query.lower() for k in triggers):
        # Extract search keyword by removing conversational filler words
        cleaned_query = re.sub(r'(?i)\b(what|is|who|explain|tell|me|about|the|overview|of|architecture|and|its|control|plane|\?|\!)\b', '', query).strip()
        search_term = cleaned_query.split()[0] if cleaned_query.split() else "Kubernetes"
        
        # Format for Wikipedia title URL (Capitalized, underscores)
        wiki_title = search_term.capitalize()
        
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
            headers = {"User-Agent": "EnterpriseAgent/1.0 (dev@local.net)"}
            res = requests.get(url, headers=headers, timeout=5)
            
            if res.status_code == 200:
                data = res.json()
                title = data.get("title", wiki_title)
                extract = data.get("extract", "")
                web_text = f"Source (Wikipedia - {title}):\n{extract}"
                print(f"--> Wikipedia Fetched: {title}")
        except Exception as e:
            web_text = f"Wikipedia API error: {str(e)}"
            
    return {"web_context": web_text}

# 5. Synthesizer Node
def generate_node(state: AgentState) -> dict:
    doc_ctx = state.get("doc_context", "None")
    web_ctx = state.get("web_context", "None")
    
    prompt = f"""<|system|>
You are an enterprise AI technical assistant. 
Synthesize the available context to answer the user query clearly and accurately in professional English.
- If asking about uploaded files or syllabus, refer to [Internal Document Context].
- If asking conceptual technical definitions or architecture, use [External Encyclopedia Context].
- Structure the answer cleanly with bullet points if explaining components.<|end|>
<|user|>
[Internal Document Context]:
{doc_ctx}

[External Encyclopedia Context]:
{web_ctx}

User Question: {state['query']}<|end|>
<|assistant|>"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_answer": response.content}

# 6. Graph Compilation
workflow = StateGraph(AgentState)

workflow.add_node("retriever", retrieve_node)
workflow.add_node("web_searcher", web_search_node)
workflow.add_node("generator", generate_node)

workflow.set_entry_point("retriever")
workflow.add_edge("retriever", "web_searcher")
workflow.add_edge("web_searcher", "generator")
workflow.add_edge("generator", END)

agent_app = workflow.compile()