# Autonomous Investment Research Pipeline

A self-correcting AI pipeline built with LangGraph that researches a stock ticker, critiques its own output, and produces a professional investment memo — with a Human-in-the-Loop review step before writing.

## Architecture

```
User Input (ticker)
    │
    ▼
┌─────────┐     ┌────────┐     ┌─────┐     ┌────────┐
│ Planner │────▶│ Search │────▶│ RAG │────▶│ Critic │
└─────────┘     └────────┘     └─────┘     └───┬────┘
                     ▲                          │
                     │   score < 6.0            │  score ≥ 6.0
                     └──────────────────────────┤
                                                │
                                          ⏸ Human Review
                                                │
                                                ▼
                                          ┌────────┐
                                          │ Writer │────▶ END
                                          └────────┘
```

| Node | What it does |
|---|---|
| Planner | Decomposes ticker into 3–5 targeted search queries |
| Search | DuckDuckGo web search via `@tool` decorator |
| RAG | Retrieves relevant chunks from earnings PDFs via ChromaDB |
| Critic | Scores research completeness (0–10), routes back or proceeds |
| Writer | Generates structured investment memo via LCEL chain |

## Stack

- **LangGraph** — StateGraph with conditional edges and self-corrective loop
- **LangChain** — LCEL chains, `@tool`, `ToolNode`, structured output (Pydantic)
- **Gemini 2.5 Flash** — LLM for Planner, Critic, Writer nodes
- **ChromaDB + HuggingFace Embeddings** — local RAG over earnings PDFs
- **DuckDuckGo** — web search, no API key required
- **Streamlit + Plotly** — interactive frontend with real-time progress
- **MemorySaver** — LangGraph checkpointer enabling Human-in-the-Loop

## Setup

```bash
git clone <your-repo-url>
cd investment-research-agent

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

## Running

```bash
# Web UI (recommended)
streamlit run demo/app.py

# CLI
python demo/run_demo.py
```

## Adding Earnings PDFs

Drop PDF files into `data/pdfs/`. The filename **must start with the ticker symbol**:

```
data/pdfs/
  AAPL_10k_2024.pdf   ✅
  TSLA_annual.pdf     ✅
  apple_report.pdf    ❌  (not linked to AAPL)
```

If no PDF exists for a ticker, the pipeline falls back to web-search-only mode automatically. After adding new PDFs, delete `chroma_db/` to rebuild the index.

## Project Structure

```
investment-research-agent/
├── state.py          # Global TypedDict state with reducers
├── graph.py          # StateGraph assembly (plain + HITL versions)
├── llm.py            # Shared rate-limited LLM instance
├── nodes/
│   ├── planner.py
│   ├── search.py
│   ├── rag.py
│   ├── critic.py
│   └── writer.py
├── demo/
│   ├── app.py        # Streamlit frontend
│   └── run_demo.py   # CLI entry point
├── PROJECT.md        # Technical documentation
├── requirements.txt
└── .env.example
```
