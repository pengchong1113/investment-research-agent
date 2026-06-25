# Member 1 — LangGraph Assembly
# Run this file to visualise the graph: python graph.py

import os
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from state import ResearchState
from nodes.planner import planner_node
from nodes.search  import search_node
from nodes.rag     import rag_node
from nodes.critic  import critic_node, route_after_critic
from nodes.writer  import writer_node


def build_graph():
    workflow = StateGraph(ResearchState)

    # ── Nodes ──────────────────────────────────────────────────────
    workflow.add_node("planner", planner_node)
    workflow.add_node("search",  search_node)
    workflow.add_node("rag",     rag_node)
    workflow.add_node("critic",  critic_node)
    workflow.add_node("writer",  writer_node)

    # ── Edges ───────────────────────────────────────────────────────
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "search")
    workflow.add_edge("search",  "rag")
    workflow.add_edge("rag",     "critic")

    # Conditional: critic decides to loop back or finish
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "search": "search",   # not enough info → search again
            "writer": "writer",   # sufficient → write memo
        }
    )
    workflow.add_edge("writer", END)

    return workflow.compile()


graph = build_graph()


if __name__ == "__main__":
    # Visualise the graph structure
    from IPython.display import Image, display
    from langchain_core.runnables.graph import MermaidDrawMethod
    display(
        Image(graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API))
    )
