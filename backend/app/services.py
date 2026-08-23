from typing import List
from sentence_transformers import SentenceTransformer
import pypdf
import io

#Lighweight, high-speed 384-dim embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_from_pdf(file_bytes:bytes) -> str:
    """extract text from PDF Stream"""
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    extract_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extract_text.append(text)
    return "\n".join(extract_text)

def chunk_text(text:str ,chunk_size:int = 500, overlap: int =50) -> List[str]:
    """Document text to be split into overlapping chunks"""
    chunks =[]
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Use Local model to generate embeddings"""
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()