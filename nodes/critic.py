# Member 4 — Critic Node + Conditional Routing
# Scores the completeness of gathered research.
# If score < THRESHOLD and iterations < MAX, routes back to search.

import os
from typing import Literal
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from state import ResearchState

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

MAX_ITERATIONS = 3
SCORE_THRESHOLD = 7.0


# ── Structured output schema ───────────────────────────────────────

class CriticOutput(BaseModel):
    score: float = Field(
        description="Completeness score from 0 to 10. 7+ means sufficient to write a memo."
    )
    missing_topics: list[str] = Field(
        description="List of topics still missing or under-researched. Empty if score >= 7."
    )
    reasoning: str = Field(
        description="Brief explanation of the score."
    )


CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior equity research analyst reviewing gathered data.
Evaluate whether the information is sufficient to write a professional investment memo.

Score 0–10:
  9–10 : Comprehensive — recent news, financials, risks, outlook all covered
  7–8  : Sufficient — minor gaps but memo can be written
  5–6  : Partial — key sections would be weak
  0–4  : Insufficient — critical information missing

Be strict. A score of 7 or above means we proceed to writing."""),
    ("human", """Stock: {ticker}

--- Web Search Results ---
{search_results}

--- Earnings / RAG Context ---
{rag_context}

Evaluate completeness."""),
])

critic_chain = CRITIC_PROMPT | llm.with_structured_output(CriticOutput)


# ── Node ───────────────────────────────────────────────────────────

def critic_node(state: ResearchState) -> dict:
    """Score the research and identify any gaps."""
    search_text = "\n\n".join(state.get("search_results", []))
    result: CriticOutput = critic_chain.invoke({
        "ticker":         state["ticker"],
        "search_results": search_text or "None",
        "rag_context":    state.get("rag_context", "None"),
    })

    print(f"[Critic] Score: {result.score}/10  |  Iteration: {state.get('iteration', 0)}")
    if result.missing_topics:
        print(f"[Critic] Missing: {result.missing_topics}")

    return {
        "score":          result.score,
        "missing_topics": result.missing_topics,
        "critique":       result.reasoning,
    }


# ── Conditional edge function ──────────────────────────────────────

def route_after_critic(state: ResearchState) -> Literal["search", "writer"]:
    """Decide whether to loop back for more research or proceed to writing."""
    if state.get("iteration", 0) >= MAX_ITERATIONS:
        print(f"[Router] Max iterations reached — proceeding to writer.")
        return "writer"
    if state.get("score", 0) >= SCORE_THRESHOLD:
        print(f"[Router] Score {state['score']} >= {SCORE_THRESHOLD} — proceeding to writer.")
        return "writer"
    print(f"[Router] Score {state['score']} < {SCORE_THRESHOLD} — looping back to search.")
    return "search"
