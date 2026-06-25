# Member 1 — Global State Definition
# All nodes read from and write to this shared state.

from typing import Annotated, TypedDict
import operator
from langgraph.graph.message import add_messages


class ResearchState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────
    ticker: str                                      # e.g. "AAPL"

    # ── Planner output (Member 3) ───────────────────────────────────
    search_queries: list[str]                        # decomposed search directions

    # ── Search results (Member 3) ───────────────────────────────────
    # Annotated with operator.add so each loop iteration APPENDS,
    # rather than overwriting previous results.
    search_results: Annotated[list[str], operator.add]

    # ── RAG output (Member 2) ───────────────────────────────────────
    rag_context: str                                 # relevant text from earnings PDFs

    # ── Critic output (Member 4) ────────────────────────────────────
    score: float                                     # completeness score 0–10
    missing_topics: list[str]                        # gaps identified by critic
    critique: str                                    # critic's reasoning
    iteration: int                                   # how many loops so far

    # ── Writer output (Member 4) ────────────────────────────────────
    memo: str                                        # final investment memo

    # ── Conversation history (optional) ────────────────────────────
    messages: Annotated[list, add_messages]
