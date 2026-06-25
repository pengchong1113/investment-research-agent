# Member 4 — Writer Node
# Synthesises all gathered research into a structured investment memo.

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from state import ResearchState

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

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

Write the investment memo now."""),
])

writer_chain = WRITER_PROMPT | llm | StrOutputParser()


def writer_node(state: ResearchState) -> dict:
    """Generate the final investment memo."""
    search_text = "\n\n".join(state.get("search_results", []))
    memo = writer_chain.invoke({
        "ticker":         state["ticker"],
        "search_results": search_text or "No web data available.",
        "rag_context":    state.get("rag_context", "No earnings data available."),
    })
    print(f"[Writer] Memo generated ({len(memo)} chars)")
    return {"memo": memo}
