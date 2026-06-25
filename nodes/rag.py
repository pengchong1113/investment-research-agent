# Member 2 — RAG Node
# Loads earnings PDFs from data/pdfs/, indexes them in Chroma,
# and retrieves relevant context for the current ticker.

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from state import ResearchState

PDF_DIR    = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# ── Build / load vector store ──────────────────────────────────────

def _load_vectorstore() -> Chroma:
    """Load existing Chroma DB or build it from PDFs in data/pdfs/."""
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        print("[RAG] No PDFs found in data/pdfs/ — returning empty context.")
        return None

    print(f"[RAG] Loading {len(pdf_files)} PDF(s) into Chroma...")
    all_docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)

    for fname in pdf_files:
        path = os.path.join(PDF_DIR, fname)
        loader = PyPDFLoader(path)
        pages  = loader.load()
        chunks = splitter.split_documents(pages)
        all_docs.extend(chunks)
        print(f"[RAG]   {fname} → {len(chunks)} chunks")

    db = Chroma.from_documents(all_docs, embeddings, persist_directory=CHROMA_DIR)
    return db


_db: Chroma | None = None

def get_db() -> Chroma | None:
    global _db
    if _db is None:
        _db = _load_vectorstore()
    return _db


# ── Node ───────────────────────────────────────────────────────────

def rag_node(state: ResearchState) -> dict:
    """Retrieve earnings context for the given ticker."""
    db = get_db()
    if db is None:
        return {"rag_context": "No earnings documents available."}

    query = f"{state['ticker']} earnings revenue profit outlook"
    docs  = db.similarity_search(query, k=4)
    context = "\n\n".join(d.page_content for d in docs)

    print(f"[RAG] Retrieved {len(docs)} chunks for '{state['ticker']}'")
    return {"rag_context": context}
