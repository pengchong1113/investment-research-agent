# Member 1 — LangGraph Assembly
# Run this file to visualise the graph: python graph.py

import os
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from state import ResearchState
from nodes.planner        import planner_node
from nodes.search         import search_node
from nodes.rag            import rag_node
from nodes.critic         import critic_node, route_after_critic
from nodes.query_transform import query_transform_node
from nodes.writer         import writer_node


def _build_workflow() -> StateGraph:
    workflow = StateGraph(ResearchState)

    # ── Nodes ──────────────────────────────────────────────────────
    workflow.add_node("planner",          planner_node)
    workflow.add_node("search",           search_node)
    workflow.add_node("rag",              rag_node)
    workflow.add_node("critic",           critic_node)
    workflow.add_node("query_transform",  query_transform_node)
    workflow.add_node("writer",           writer_node)

    # ── Edges ───────────────────────────────────────────────────────
    workflow.set_entry_point("planner")
    workflow.add_edge("planner",         "search")
    workflow.add_edge("search",          "rag")
    workflow.add_edge("rag",             "critic")

    # When Critic routes "search", go to QueryTransform first (rewrite queries),
    # then Search — directly from Self-Corrective RAG pattern in course material
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {"search": "query_transform", "writer": "writer"},
    )
    workflow.add_edge("query_transform", "search")
    workflow.add_edge("writer",          END)
    return workflow


# Plain graph — used by CLI demo (no interrupt, no memory)
graph = _build_workflow().compile()

# HITL graph — used by Streamlit (pauses before Writer, persists state)
_checkpointer = MemorySaver()
graph_hitl = _build_workflow().compile(
    checkpointer=_checkpointer,
    interrupt_before=["writer"],
)


if __name__ == "__main__":
    # Visualise the graph structure (run: python graph.py)
    from langchain_core.runnables.graph import MermaidDrawMethod
    png = graph_hitl.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)
    with open("pipeline_graph.png", "wb") as f:
        f.write(png)
    print("Saved pipeline_graph.png")
