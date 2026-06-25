# Member 5 — Demo Entry Point
# Run:  python demo/run_demo.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from graph import graph


def run(ticker: str):
    print(f"\n{'='*55}")
    print(f"  Autonomous Investment Research Pipeline")
    print(f"  Ticker: {ticker}")
    print(f"{'='*55}\n")

    initial_state = {
        "ticker":         ticker,
        "search_queries": [],
        "search_results": [],
        "rag_context":    "",
        "score":          0.0,
        "missing_topics": [],
        "critique":       "",
        "iteration":      0,
        "memo":           "",
        "messages":       [],
    }

    # Stream events so we can see each node firing in real time
    print("Running pipeline...\n")
    final = None
    for step in graph.stream(initial_state, stream_mode="values"):
        final = step

    print(f"\n{'='*55}")
    print("  INVESTMENT MEMO")
    print(f"{'='*55}\n")
    print(final["memo"])
    print(f"\n[Done]  Completed in {final['iteration']} research iteration(s).")
    print(f"        Final completeness score: {final['score']}/10")


if __name__ == "__main__":
    ticker = input("Enter stock ticker (e.g. AAPL, TSLA, MSFT): ").strip().upper()
    if not ticker:
        ticker = "AAPL"
    run(ticker)
