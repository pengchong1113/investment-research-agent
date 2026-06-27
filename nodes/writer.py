# Member 4 — Writer Node
# Synthesises all gathered research into a structured investment memo.

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from state import ResearchState
from llm import llm

WRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional equity research analyst at a top investment bank.
Write a concise, well-structured investment research memo using ONLY the data provided.
Do not fabricate numbers or facts.

Format the memo with these sections:
1. Company Overview
2. Recent Developments
3. Financial Highlights
4. Key Risks
5. Investment Summary

Keep it professional, factual, and under 600 words."""),
    ("human", """Stock Ticker: {ticker}

--- News & Web Research ---
{search_results}

--- Earnings & Fundamentals (from filings) ---
{rag_context}

--- Analyst Notes (human reviewer instructions) ---
{human_feedback}

Write the investment memo now. If Analyst Notes are provided, follow them carefully."""),
])

writer_chain = WRITER_PROMPT | llm | StrOutputParser()


def writer_node(state: ResearchState) -> dict:
    """Generate the final investment memo, respecting any human feedback."""
    search_text    = "\n\n".join(state.get("search_results", []))
    human_feedback = state.get("human_feedback", "").strip()
    memo = writer_chain.invoke({
        "ticker":         state["ticker"],
        "search_results": search_text or "No web data available.",
        "rag_context":    state.get("rag_context", "No earnings data available."),
        "human_feedback": human_feedback or "None — proceed with standard analysis.",
    })
    print(f"[Writer] Memo generated ({len(memo)} chars)"
          + (f" [human note: {human_feedback[:60]}...]" if human_feedback else ""))
    return {"memo": memo}
