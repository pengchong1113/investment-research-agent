# Autonomous Investment Research Pipeline
## Technical Project Documentation

---

## 1. Business Problem

Traditional equity research requires analysts to manually:
- Search dozens of news sources and financial databases
- Read through hundreds of pages of earnings filings
- Cross-check facts and synthesize a coherent narrative
- Write a structured investment memo — a process that takes **1–3 days per report**

Our system automates this end-to-end in under **60 seconds**, using a self-correcting multi-node AI pipeline that searches the web, retrieves earnings data, critiques its own output, and produces a professional investment memo.

---

## 2. System Architecture

```
User Input (ticker symbol, e.g. "AAPL")
        │
        ▼
┌─────────────┐
│   Planner   │  LLM decomposes ticker into 3–5 targeted search queries
└──────┬──────┘
        │
        ▼
┌─────────────┐
│   Search    │  DuckDuckGo fetches latest news, filings, analyst comments
└──────┬──────┘
        │
        ▼
┌─────────────┐
│     RAG     │  Retrieves relevant chunks from earnings PDFs via Chroma
└──────┬──────┘
        │
        ▼
┌─────────────┐     score < 6.0 AND iterations < 3
│   Critic    │ ──────────────────────────────────────┐
└──────┬──────┘                                        │
        │ score ≥ 6.0 OR iterations = 3                │
        ▼                                              │
┌─────────────┐                                        │
│   Writer    │   ◄────────────────────────────────────┘
└──────┬──────┘
        │
        ▼
  Investment Memo (markdown)
```

**Framework**: LangGraph `StateGraph` — a directed graph where nodes are Python functions and edges define control flow, including conditional branches and loops.

---

## 3. Backend Deep Dive

### 3.1 Global State — `state.py`

All nodes communicate through a single shared `TypedDict` called `ResearchState`.

```python
class ResearchState(TypedDict):
    ticker:          str
    search_queries:  list[str]
    search_results:  Annotated[list[str], operator.add]   # ← key design
    rag_context:     str
    score:           float
    missing_topics:  list[str]
    critique:        str
    iteration:       int
    memo:            str
    messages:        Annotated[list, add_messages]
```

**Why `Annotated[list, operator.add]` for `search_results`?**

LangGraph calls each node and merges the return value back into the state. Without a reducer, the second call to the Search node would **overwrite** the first iteration's results:

```
Iteration 1 search_results = ["news A", "news B"]
Iteration 2 search_results = ["news C"]   ← overwrites, losing A and B ❌
```

With `operator.add` as the reducer, LangGraph **appends** instead:

```
Iteration 1 search_results = ["news A", "news B"]
Iteration 2 search_results = ["news A", "news B", "news C"]   ✅
```

This means the Writer always has the full accumulated research from all iterations.

---

### 3.2 Planner Node — `nodes/planner.py`

**Role**: Decompose a vague ticker symbol into concrete, targeted search queries.

**Why not just search the ticker directly?**
Searching `"AAPL"` returns generic results. Decomposing it produces queries like:
- `"Apple Inc Q2 2025 earnings beat estimates"`
- `"Apple Vision Pro sales outlook analyst forecast"`
- `"AAPL key investment risks regulatory antitrust"`

This dramatically improves the quality of downstream search results.

**Implementation**: Uses **Pydantic structured output** to force the LLM to return a clean Python object instead of free text:

```python
class PlannerOutput(BaseModel):
    search_queries: list[str]

planner_chain = PLANNER_PROMPT | llm.with_structured_output(PlannerOutput)
```

`with_structured_output` instructs Gemini to respond in JSON matching the schema. This prevents the LLM from adding explanations or formatting that would break parsing.

---

### 3.3 Search Node — `nodes/search.py`

**Role**: Execute web searches and accumulate results across loop iterations.

**Tool used**: `DuckDuckGoSearchResults` from LangChain Community — no API key required.

**Loop-aware design**: On subsequent iterations, the Critic provides `missing_topics` (e.g. `["ESG metrics", "revenue breakdown by segment"]`). The Search node generates additional queries from these gaps:

```python
missing = state.get("missing_topics", [])
extra_queries = [f"{state['ticker']} {topic}" for topic in missing]
queries = original_queries + extra_queries
```

This is how the system **learns what it doesn't know** and actively fills the gaps.

---

### 3.4 RAG Node — `nodes/rag.py`

**Role**: Retrieve relevant content from locally stored earnings PDFs.

**Full RAG pipeline**:

```
PDF files
    │
    ▼  PyPDFLoader
Raw text (pages)
    │
    ▼  RecursiveCharacterTextSplitter (chunk_size=800, overlap=80)
Chunks (~1000 per 10-K)
    │
    ▼  HuggingFaceEmbeddings ("all-MiniLM-L6-v2")
768-dimensional vectors
    │
    ▼  Chroma.from_documents()
ChromaDB (persisted to disk at ./chroma_db/)
    │
    ▼  db.similarity_search(query, k=4, filter={"ticker": ticker})
Top-4 most relevant chunks
```

**Why chunk size 800?**
- Too small (< 200): chunks lose surrounding context, retrieval quality drops
- Too large (> 2000): exceeds LLM context window, costs more tokens
- 800 characters ≈ one financial paragraph — the natural unit of meaning in filings

**Why HuggingFace embeddings instead of Gemini?**
Gemini's free tier allows only **100 embedding requests per minute**. A single Apple 10-K produces ~600 chunks, requiring 6 minutes of waiting with rate-limit pauses. `all-MiniLM-L6-v2` runs **locally** with no API calls, no rate limits, and builds the full index in ~30 seconds.

**Ticker metadata filtering**:
Each chunk is tagged at index time:
```python
chunk.metadata["ticker"] = fname.split("_")[0].upper()   # "AAPL_10k.pdf" → "AAPL"
```

At query time, Chroma filters by this tag:
```python
db.similarity_search(query, k=4, filter={"ticker": ticker})
```

This means one Chroma database can hold PDFs for **multiple companies** and will never return Apple's financials when you're researching Tesla.

**Graceful degradation**: If no PDF exists for the queried ticker, the node returns a message saying so. The Writer is informed and produces a web-search-only analysis — the pipeline never crashes due to missing files.

**Persistence optimisation**: The vector index is saved to `./chroma_db/` on first build. On all subsequent runs, it is loaded directly — no re-embedding. This avoids re-processing 1000+ chunks every time the app starts.

---

### 3.5 Critic Node — `nodes/critic.py`

**Role**: Evaluate research completeness, score it, and decide whether to continue.

This node implements the **LLM-as-Judge** pattern — using an LLM to evaluate the output of other LLM calls rather than using hard-coded rules.

**Why Pydantic structured output is critical here**:

Without it, the LLM might respond:
> *"I'd give this a 6 out of 10, it's pretty good but missing some things."*

This makes it impossible to extract a reliable number for routing. With Pydantic:

```python
class CriticOutput(BaseModel):
    score:          float          # always a number, always 0–10
    missing_topics: list[str]      # always a list, usable directly
    reasoning:      str

critic_chain = CRITIC_PROMPT | llm.with_structured_output(CriticOutput)
```

The LLM **must** return valid JSON matching this schema. The score is always a Python `float`, safe to compare against the threshold.

**Routing function** (`route_after_critic`):

```python
def route_after_critic(state) -> Literal["search", "writer"]:
    if state["iteration"] >= MAX_ITERATIONS:   # safety guard
        return "writer"
    if state["score"] >= SCORE_THRESHOLD:      # sufficient quality
        return "writer"
    return "search"                            # loop back
```

This function is passed to `add_conditional_edges` in the graph. LangGraph calls it after every Critic execution to determine the next node.

**Why `MAX_ITERATIONS = 3`?**
Without a cap, a strict critic could loop forever. Three iterations is a deliberate tradeoff:
- Iteration 1: broad search → base score
- Iteration 2: targeted gap-filling → improved score
- Iteration 3: final attempt → write regardless

In practice, score improves from ~5 → ~6 across iterations, which is the expected behaviour with web-search-grade data.

---

### 3.6 Writer Node — `nodes/writer.py`

**Role**: Synthesise all gathered information into a structured investment memo.

**Implementation**: A simple **LCEL chain** (LangChain Expression Language):

```python
writer_chain = WRITER_PROMPT | llm | StrOutputParser()
```

The `|` operator composes three components into a pipeline:
1. `WRITER_PROMPT` — formats the state data into a structured prompt
2. `llm` — calls Gemini 2.5 Flash
3. `StrOutputParser()` — extracts the raw string from the LLM response object

The prompt instructs the LLM to produce five sections: Company Overview, Recent Developments, Financial Highlights, Key Risks, and Investment Summary — and explicitly forbids fabricating numbers not present in the provided data.

---

### 3.7 Graph Assembly — `graph.py`

```python
workflow = StateGraph(ResearchState)

workflow.add_node("planner", planner_node)
workflow.add_node("search",  search_node)
workflow.add_node("rag",     rag_node)
workflow.add_node("critic",  critic_node)
workflow.add_node("writer",  writer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "search")
workflow.add_edge("search",  "rag")
workflow.add_edge("rag",     "critic")
workflow.add_conditional_edges("critic", route_after_critic,
                                {"search": "search", "writer": "writer"})
workflow.add_edge("writer", END)

graph = workflow.compile()
```

`add_conditional_edges` wires the Critic to two possible next nodes. LangGraph evaluates `route_after_critic(state)` at runtime after every Critic execution to decide which branch to follow.

---

## 4. Key Design Decisions

| Decision | Alternative considered | Why we chose this |
|---|---|---|
| LangGraph StateGraph | Simple sequential chain | Enables the Critic loop; conditional routing is not possible with a linear chain |
| `operator.add` reducer | Overwrite each iteration | Preserves all search results across loop iterations for the Writer |
| Pydantic structured output | Parse LLM string response | Reliable score extraction; prevents routing failure from malformed LLM output |
| HuggingFace local embeddings | Gemini embedding API | Free tier rate limit (100 req/min) makes indexing 1000+ chunks impractical |
| Ticker metadata in Chroma | Separate DB per company | One shared index, zero duplication, correct per-company retrieval |
| Max iterations = 3 | No cap / higher cap | Balances quality improvement against API cost and demo speed |
| DuckDuckGo search | Tavily Search API | No API key required; sufficient for demo-quality research |

---

## 5. Data Flow Summary

```
"AAPL"
  → ["AAPL news 2025", "AAPL earnings outlook", ...]      (Planner)
  → ["Apple hit record...", "Analysts expect...", ...]     (Search, accumulated)
  → "Net income $112B, gross margin 47.86%..."             (RAG from 10-K)
  → score: 5.0, missing: ["ESG", "segment breakdown"]     (Critic iter 1)
  → [original queries] + ["AAPL ESG", "AAPL segment..."]  (Search iter 2)
  → score: 6.0                                             (Critic iter 2)
  → "## Investment Memo: Apple Inc. ..."                   (Writer)
```

---

## 6. Potential Teacher Questions

**Q: Why use LangGraph instead of just chaining LangChain calls?**

A LangChain chain is linear — it cannot loop back. LangGraph models the pipeline as a directed graph with conditional edges, which is necessary for the Critic loop. When the Critic scores research as insufficient, the graph routes back to the Search node. This is impossible to express in a sequential chain without custom control flow code.

**Q: What is RAG and why do you need it?**

RAG (Retrieval-Augmented Generation) solves the problem that LLMs have a training cutoff and don't know company-specific financial details. By indexing actual earnings PDFs and retrieving the most relevant excerpts at query time, we ground the model's output in real, verifiable numbers rather than hallucinated ones. Without RAG, the memo's financial figures would be invented by the LLM.

**Q: How does the Critic know what's missing?**

The Critic receives the accumulated search results and RAG context, then uses Gemini to evaluate whether a professional investment memo could be written from the available information. It returns a structured object with a numeric score and an explicit list of missing topics. These missing topics are fed back into the next Search iteration as additional queries — this is the self-correction mechanism.

**Q: What prevents the pipeline from looping forever?**

Two termination conditions: (1) the score reaches the threshold of 6.0, or (2) the iteration counter reaches `MAX_ITERATIONS = 3`. The routing function checks both conditions before deciding whether to loop. This guarantees the graph always terminates.

**Q: Why do you tag chunks with ticker metadata in Chroma?**

Without metadata filtering, a similarity search for "TSLA earnings revenue" would return the most semantically similar chunks from all PDFs in the database — which may include Apple's revenue figures. By tagging each chunk with its source ticker at index time and filtering at query time, each company's RAG context stays isolated. This allows one shared vector database to serve multiple tickers correctly.

**Q: Why is `search_results` annotated with `operator.add` instead of a plain list?**

LangGraph merges each node's return value into the state using the field's reducer. A plain `list` would use the default reducer (overwrite), meaning iteration 2's search results would replace iteration 1's. Using `operator.add` as the reducer tells LangGraph to concatenate instead of replace, so the Writer node always receives the full accumulated research from every iteration.

**Q: What is structured output and why do you use it for the Critic and Planner?**

Structured output (`llm.with_structured_output(PydanticModel)`) instructs the LLM to respond in JSON that must match a given Pydantic schema. For the Critic, this guarantees we always get a numeric `score` field we can compare against the threshold. For the Planner, it guarantees we get a clean `list[str]` of queries. Without structured output, we would need to parse free-form LLM text — fragile and failure-prone.
