# Member 2 — RAG Node
# Loads earnings PDFs from data/pdfs/, indexes them in Chroma,
# and retrieves relevant context for the current ticker.

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from state import ResearchState

PDF_DIR    = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

# Local embeddings — no API key, no rate limits
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ── Build / load vector store ──────────────────────────────────────

def _load_vectorstore() -> Chroma:
    """Load existing Chroma DB if present; otherwise build from PDFs."""
    # If DB was already built, just load it — no re-embedding needed
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        print("[RAG] Found existing Chroma DB — loading (skipping re-embedding).")
        return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print("[RAG] No PDFs found in data/pdfs/ — returning empty context.")
        return None

    print(f"[RAG] Building Chroma DB from {len(pdf_files)} PDF(s)...")
    all_docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)

    for fname in pdf_files:
        # Extract ticker from filename: "AAPL_10k_2024.pdf" → "AAPL"
        ticker_tag = fname.split("_")[0].upper()
        path = os.path.join(PDF_DIR, fname)
        loader = PyPDFLoader(path)
        pages  = loader.load()
        chunks = splitter.split_documents(pages)
        # Tag every chunk with its ticker so we can filter later
        for chunk in chunks:
            chunk.metadata["ticker"] = ticker_tag
        all_docs.extend(chunks)
        print(f"[RAG]   {fname} → {len(chunks)} chunks  [ticker={ticker_tag}]")

    print(f"[RAG] Embedding {len(all_docs)} chunks locally (no rate limit)...")
    db = Chroma.from_documents(all_docs, embeddings, persist_directory=CHROMA_DIR)
    print("[RAG] Chroma DB built and saved.")
    return db


_db: Chroma | None = None

def get_db() -> Chroma | None:
    global _db
    if _db is None:
        _db = _load_vectorstore()
    return _db


# ── Node ───────────────────────────────────────────────────────────

def rag_node(state: ResearchState) -> dict:
    """Retrieve earnings context for the given ticker only."""
    db = get_db()
    if db is None:
        return {"rag_context": "No earnings documents available."}

    ticker = state["ticker"]
    query  = f"{ticker} earnings revenue profit outlook"

    # Filter by ticker metadata — only return chunks from this company's PDFs
    docs = db.similarity_search(query, k=4, filter={"ticker": ticker})

    if not docs:
        print(f"[RAG] No PDF found for {ticker} — RAG skipped.")
        return {"rag_context": f"No earnings PDF available for {ticker}. Analysis based on web search only."}

    context = "\n\n".join(d.page_content for d in docs)
    print(f"[RAG] Retrieved {len(docs)} chunks for '{ticker}'")
    return {"rag_context": context}
