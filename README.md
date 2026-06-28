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
                        │                          │  score ≥ 7.0
              ┌─────────┴────────┐  score < 7.0    │  (or 3 loops)
              │  Query Transform │◀────────────────┤
              └──────────────────┘                 │
                                                    ▼
                                            ⏸ Human Review
                                                    │
                                                    ▼
                                              ┌────────┐
                                              │ Writer │────▶ END
                                              └────────┘
```

When the Critic scores below 7.0, the loop rewrites the queries (Query Transform) and searches again — up to a maximum of 3 iterations, after which it proceeds to the Writer regardless.

| Node | What it does |
|---|---|
| Planner | Decomposes ticker into exactly 5 targeted search queries (one per category: news, financials, competitors, risks, valuation) |
| Search | Web search via `@tool` decorator — Tavily (primary) with DuckDuckGo fallback, per-query 15s timeout |
| RAG | Retrieves relevant chunks from earnings PDFs via ChromaDB, filtered by ticker |
| Critic | Scores research completeness (0–10) across 5 dimensions; routes back or proceeds |
| Query Transform | On loop-back, rewrites the search queries using the Critic's missing topics |
| Writer | Generates a structured investment memo (ending in BUY / HOLD / SELL) via LCEL chain |

## Stack

- **LangGraph** — StateGraph with conditional edges and self-corrective loop
- **LangChain** — LCEL chains, `@tool`, structured output (Pydantic)
- **Gemini 3.1 Flash Lite** (temperature 0.2) — shared LLM for Planner, Critic, Query Transform, and Writer nodes
- **ChromaDB + HuggingFace Embeddings** (`all-MiniLM-L6-v2`) — local RAG over earnings PDFs
- **Tavily Search API** (primary) with **DuckDuckGo** fallback — web search
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
# Add your GOOGLE_API_KEY (required) and TAVILY_API_KEY (recommended — primary
# search backend; without it, search falls back to DuckDuckGo) to .env
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
│   ├── query_transform.py
│   └── writer.py
├── demo/
│   ├── app.py        # Streamlit frontend
│   └── run_demo.py   # CLI entry point
├── PROJECT.md        # Technical documentation
├── requirements.txt
└── .env.example
```
