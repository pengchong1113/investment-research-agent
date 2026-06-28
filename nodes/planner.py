# Member 3 — Planner Node
# Takes a stock ticker and decomposes it into specific search queries.

from datetime import date

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from state import ResearchState
from llm import llm


class PlannerOutput(BaseModel):
    search_queries: list[str]   # 5 targeted search queries, one per category


PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a financial research planner. Today's date is {today}.

Given a stock ticker symbol, generate exactly 5 specific search queries to
research the company thoroughly — ONE query for EACH of these categories:

1. Recent news and material events (use the current year for recency)
2. Latest quarterly/annual EARNINGS and detailed FINANCIAL performance —
   revenue, net income, EPS, margins, growth rates, and forward guidance
3. Competitive landscape and market share (name the key rivals)
4. Key risks, regulatory issues, and challenges
5. Valuation — analyst ratings, price targets, P/E, and market cap

Rules:
- Make every query specific: include the company's full name and, where
  time-sensitive, the current year ({year}).
- Avoid vague words like "overview" or "general".

Example for ticker MSFT:
  "Microsoft Corporation Q2 {year} earnings revenue net income EPS margins"

Return ONLY the list of queries — no extra text."""),
    ("human", "Stock ticker: {ticker}"),
])

planner_chain = PLANNER_PROMPT | llm.with_structured_output(PlannerOutput)


def planner_node(state: ResearchState) -> dict:
    """Decompose ticker into search queries and store in state."""
    today = date.today()
    result: PlannerOutput = planner_chain.invoke({
        "ticker": state["ticker"],
        "today":  today.isoformat(),
        "year":   today.year,
    })
    print(f"[Planner] Generated {len(result.search_queries)} queries for {state['ticker']}")
    return {
        "search_queries": result.search_queries,
        "iteration": 0,          # reset loop counter at start
    }
