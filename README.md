# Autonomous Investment Research Pipeline

A LangGraph multi-node pipeline that automatically researches a stock ticker,
critiques its own output, loops back for more data if needed, and produces a
professional investment memo.

## Architecture

```
User Input (ticker)
    │
    ▼
┌─────────┐     ┌────────┐     ┌─────┐     ┌────────┐
│ Planner │────▶│ Search │────▶│ RAG │────▶│ Critic │
└─────────┘     └────────┘     └─────┘     └───┬────┘
                     ▲                          │
                     │   score < 7.0            │  score >= 7.0
                     └──────────────────────────┤
                                                │
                                                ▼
                                          ┌────────┐
                                          │ Writer │────▶ END
                                          └────────┘
```

| Node    | Owner    | What it does |
|---------|----------|--------------|
| Planner | Member 3 | Decomposes ticker into 3–5 search queries |
| Search  | Member 3 | DuckDuckGo web search, appends to state |
| RAG     | Member 2 | Retrieves context from earnings PDFs via Chroma |
| Critic  | Member 4 | Scores completeness (0–10), routes: loop or write |
| Writer  | Member 4 | Generates investment memo via LCEL chain |
| Graph   | Member 1 | Assembles and compiles the StateGraph |
| Demo    | Member 5 | End-to-end testing and presentation |

## Setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd investment-research-agent

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up API keys
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 5. Add earnings PDFs (optional but recommended)
# Drop any company 10-K or earnings PDFs into data/pdfs/
# e.g. Apple_10K_2024.pdf, Tesla_Q4_2024.pdf

# 6. Run the demo
python demo/run_demo.py
```

## Project Structure

```
investment-research-agent/
├── state.py              ← Member 1: global TypedDict state
├── graph.py              ← Member 1: StateGraph assembly
├── nodes/
│   ├── planner.py        ← Member 3
│   ├── search.py         ← Member 3
│   ├── rag.py            ← Member 2
│   ├── critic.py         ← Member 4
│   └── writer.py         ← Member 4
├── data/
│   └── pdfs/             ← Drop earnings PDFs here (git-ignored)
├── demo/
│   └── run_demo.py       ← Member 5: demo entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

## Git Workflow (5-person team)

```bash
# Each member works on their own branch
git checkout -b feature/rag          # Member 2
git checkout -b feature/search       # Member 3
git checkout -b feature/critic       # Member 4

# Commit and push your branch
git add nodes/rag.py
git commit -m "feat: implement RAG node with Chroma"
git push origin feature/rag

# Open a Pull Request on GitHub → Member 1 reviews and merges to main
```

## Key Design Decisions

- **State reducers**: `search_results` uses `operator.add` so results accumulate
  across loop iterations instead of being overwritten.
- **Max iterations guard**: Critic loops back at most `MAX_ITERATIONS=3` times to
  prevent infinite loops.
- **Score threshold**: `SCORE_THRESHOLD=7.0` — tune this in `nodes/critic.py`.
- **RAG is optional**: If no PDFs are in `data/pdfs/`, the RAG node returns an empty
  context and the pipeline still runs on web search results alone.

## Team

| Member | Role |
|--------|------|
| 1 | System Architect & LangGraph Assembly |
| 2 | RAG Pipeline Engineer |
| 3 | Planner & Search Node |
| 4 | Critic Loop & Writer |
| 5 | Business Analyst & Demo Lead |
