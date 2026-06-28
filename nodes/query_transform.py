# Query Transform Node
# Directly from Self-Corrective RAG pattern (teacher's notebook).
# When the Critic finds research insufficient, instead of searching
# with raw missing_topics, this node first rewrites the queries
# into more precise, targeted search terms.

from datetime import date

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from state import ResearchState
from llm import llm


class TransformedQueries(BaseModel):
    search_queries: list[str]


TRANSFORM_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a financial research expert who crafts precise search queries.
Today's date is {today}.

Given a stock ticker, the queries already tried, the gaps identified by the
critic, and the critic's reasoning, rewrite the search queries into highly
specific, targeted queries that will find exactly what is still missing.

Rules:
- Generate 3–5 queries
- Be specific: include the current year ({year}), exact metric names, and the
  company's full name
- Do NOT repeat or lightly reword the queries already tried — go after the gaps
- Avoid generic terms like "overview" or "general"
- Return ONLY the list of improved queries, no explanations"""),
    ("human", """Stock: {ticker}

Queries already tried:
{previous_queries}

Research gaps identified:
{missing_topics}

Critic's reasoning:
{critique}

Rewrite the search queries to fill these gaps."""),
])

_transform_chain = TRANSFORM_PROMPT | llm.with_structured_output(TransformedQueries)


def query_transform_node(state: ResearchState) -> dict:
    """Rewrite search queries based on what the Critic found lacking."""
    missing  = state.get("missing_topics", [])
    critique = state.get("critique", "")
    previous = state.get("search_queries", [])
    today    = date.today()

    result: TransformedQueries = _transform_chain.invoke({
        "ticker":           state["ticker"],
        "today":            today.isoformat(),
        "year":             today.year,
        "previous_queries": "\n".join(f"• {q}" for q in previous) or "None",
        "missing_topics":   "\n".join(f"• {m}" for m in missing) or "Not specified",
        "critique":         critique or "Research incomplete",
    })

    print(f"[QueryTransform] Rewrote into {len(result.search_queries)} targeted queries:")
    for q in result.search_queries:
        print(f"  → {q}")

    # Overwrites search_queries in state (plain list, no reducer)
    return {"search_queries": result.search_queries}
