# Member 4 — Writer Node
# Synthesises all gathered research into a structured investment memo.

from datetime import date

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from state import ResearchState
from llm import llm

WRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional equity research analyst at a top investment bank.
Today's date is {today}. Write a concise, well-structured investment research
memo using ONLY the data provided below.

Strict rules:
- Do NOT fabricate numbers, facts, or dates. If a figure is not in the data,
  write "Data not available" — never invent it.
- Do NOT use placeholders like [Your Name], [Date], [Department]. Use today's
  date ({today}) where a date is needed.
- Refer to the company by its full name (expand the ticker, e.g. AAPL ->
  Apple Inc.), not just the ticker.
- Any valuation figures (P/E, price target, market cap) must be attributed to
  the news/analyst sources in the data — these are reported figures, NOT a
  live market feed.

Start the memo with a single title line — the company's full name and ticker —
followed by today's date ({today}) and a one-line SUBJECT. Do NOT add TO or FROM
header lines; go from the title/date/subject straight into the sections.

Format the memo with these sections:
1. Company Overview
2. Recent Developments
3. Financial Highlights — be specific and metrics-rich. Include, where
   available: revenue, net income, EPS, gross/operating margin, year-over-year
   growth, forward guidance, P/E, market cap, and analyst price target. Use
   "Data not available" for any metric the research does not cover.
4. Key Risks
5. Investment Summary — end with a clear recommendation: BUY, HOLD, or SELL,
   followed by a one-line rationale grounded in the data above.

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
        "today":          date.today().isoformat(),
        "search_results": search_text or "No web data available.",
        "rag_context":    state.get("rag_context", "No earnings data available."),
        "human_feedback": human_feedback or "None — proceed with standard analysis.",
    })
    print(f"[Writer] Memo generated ({len(memo)} chars)"
          + (f" [human note: {human_feedback[:60]}...]" if human_feedback else ""))
    return {"memo": memo}
