# Member 3 — Planner Node
# Takes a stock ticker and decomposes it into specific search queries.

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from state import ResearchState
from llm import llm


class PlannerOutput(BaseModel):
    search_queries: list[str]   # 3–5 targeted search queries


PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a financial research planner.
Given a stock ticker symbol, generate 3 to 5 specific search queries
to research the company thoroughly.

Cover: recent news, earnings performance, competitive landscape, key risks.
Return ONLY the list of queries — no extra text."""),
    ("human", "Stock ticker: {ticker}"),
])

planner_chain = PLANNER_PROMPT | llm.with_structured_output(PlannerOutput)


def planner_node(state: ResearchState) -> dict:
    """Decompose ticker into search queries and store in state."""
    result: PlannerOutput = planner_chain.invoke({"ticker": state["ticker"]})
    print(f"[Planner] Generated {len(result.search_queries)} queries for {state['ticker']}")
    return {
        "search_queries": result.search_queries,
        "iteration": 0,          # reset loop counter at start
    }
