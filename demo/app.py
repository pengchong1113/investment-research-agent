import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Investment Research AI",
    page_icon="📈",
    layout="wide"
)

# ── Session state defaults ────────────────────────────────────────
_DEFAULTS = {
    "phase":         "idle",  # idle | paused | done
    "thread":        None,
    "ticker":        "",
    "node_texts":    {},      # {node_name: display_text} — persists across reruns
    "iter_scores":   [],
    "score":         0.0,
    "missing":       [],
    "memo":          "",
    "total_results": 0,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

ss = st.session_state  # shorthand

# ── Node metadata ─────────────────────────────────────────────────
_META = {
    "planner":          ("🧠", "Planner"),
    "search":           ("🔍", "Search"),
    "rag":              ("📄", "RAG"),
    "critic":           ("⚖️", "Critic"),
    "query_transform":  ("🔄", "Query Transform"),
    "writer":           ("✍️", "Writer"),
}

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Investment Research AI")
    st.caption("GenAI Group Project · 2026")
    st.divider()

    # Graph visualization — draw_mermaid_png() from course material
    st.markdown("**LangGraph Pipeline**")

    @st.cache_data(show_spinner=False)
    def _get_graph_png():
        from graph import graph_hitl
        from langchain_core.runnables.graph import MermaidDrawMethod
        return graph_hitl.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)

    try:
        st.image(_get_graph_png(), use_container_width=True)
    except Exception:
        st.caption("_(graph viz unavailable offline)_")

    st.divider()
    st.markdown("**Advanced Features Used**")
    st.caption("✅ `MemorySaver` checkpointer")
    st.caption("✅ `interrupt_before=[\"writer\"]`")
    st.caption("✅ `graph.update_state()` for HITL")
    st.caption("✅ `@tool` decorator on search_web")
    st.caption("✅ `draw_mermaid_png()` visualization")
    st.divider()
    st.caption("Threshold: 6.0  ·  Max iter: 3")


# ── Header ────────────────────────────────────────────────────────
st.title("Autonomous Investment Research Pipeline")
st.caption(
    "Searches the web · retrieves earnings PDFs · self-critiques · "
    "**pauses for human review** · generates investment memo"
)
st.divider()

# ── Input ─────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([2, 1, 3])
with c1:
    ticker_input = st.text_input(
        "Ticker", value="AAPL",
        placeholder="AAPL · TSLA · MSFT · NVDA",
        label_visibility="collapsed"
    )
with c2:
    run_btn = st.button("▶  Research", type="primary", use_container_width=True)


# ── Helper: build display text for each node ─────────────────────
def _node_text(node_name: str, updates: dict) -> str:
    icon, name = _META.get(node_name, ("•", node_name))
    if node_name == "planner":
        n = len(updates.get("search_queries", []))
        return f"✅ {icon} **{name}** — {n} queries generated"
    if node_name == "search":
        ss.total_results += len(updates.get("search_results", []))
        it = updates.get("iteration", 1)
        return f"✅ {icon} **{name}** — {ss.total_results} results · iteration {it}"
    if node_name == "rag":
        ctx = len(updates.get("rag_context", ""))
        return f"✅ {icon} **{name}** — {ctx:,} chars from PDF"
    if node_name == "query_transform":
        n = len(updates.get("search_queries", []))
        return f"✅ {icon} **{name}** — rewrote into {n} targeted queries"
    if node_name == "critic":
        score = updates.get("score", 0)
        ss.iter_scores.append(score)
        done  = score >= 6.0 or len(ss.iter_scores) >= 3
        dot   = "🟢" if score >= 7 else "🟡" if score >= 5 else "🔴"
        arrow = "→ writing" if done else "→ query rewrite"
        return f"{dot} {icon} **{name}** — {score}/10 · {arrow}"
    if node_name == "writer":
        memo = updates.get("memo", "")
        ss.memo = memo
        return f"✅ {icon} **{name}** — memo ready ({len(memo):,} chars)"
    return f"✅ {icon} **{name}**"


# ── Score chart ───────────────────────────────────────────────────
def _score_chart(scores: list, ticker: str):
    if not scores:
        return
    import plotly.graph_objects as go
    colors = ["#2e7d32" if s >= 7 else "#f57f17" if s >= 5 else "#c62828" for s in scores]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(scores) + 1)), y=scores,
        mode="lines+markers",
        line=dict(color="#1565c0", width=3),
        marker=dict(size=12, color=colors, line=dict(color="white", width=2))
    ))
    fig.add_hline(y=6.0, line_dash="dash", line_color="#e65100",
                  annotation_text="Threshold 6.0", annotation_position="top right")
    fig.update_layout(
        title=f"{ticker} — Research Quality per Iteration",
        xaxis=dict(title="Iteration", tickmode="linear", dtick=1),
        yaxis=dict(title="Score (0–10)", range=[0, 10.5]),
        height=230, margin=dict(t=40, b=30, l=40, r=20),
        showlegend=False, plot_bgcolor="#fafafa",
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PHASE A — New research (run button just clicked)
# Streams Phase 1: Planner → Search → RAG → Critic loop
# Graph pauses automatically at interrupt_before=["writer"]
# ══════════════════════════════════════════════════════════════════
if run_btn and ticker_input:
    from graph import graph_hitl

    ticker = ticker_input.strip().upper()
    thread = {"configurable": {"thread_id": f"{ticker}_{int(time.time())}"}}

    # Reset all session state for fresh run
    for k, v in _DEFAULTS.items():
        ss[k] = v
    ss.ticker = ticker
    ss.thread = thread

    initial_state = {
        "ticker": ticker, "search_queries": [], "search_results": [],
        "rag_context": "", "score": 0.0, "missing_topics": [],
        "critique": "", "iteration": 0, "memo": "",
        "messages": [], "human_feedback": "",
    }

    st.divider()
    left, right = st.columns([1, 1.7])

    with left:
        st.subheader("🔄 Pipeline Progress")
        slots = {k: st.empty() for k in _META}
        for k, (icon, name) in _META.items():
            slots[k].markdown(f"⏳ {icon} **{name}** — waiting")
        st.divider()
        mc1, mc2 = st.columns(2)
        m_iter  = mc1.empty()
        m_score = mc2.empty()
        m_iter.metric("Iterations", "—")
        m_score.metric("Score", "—")

    with right:
        st.subheader("📝 Investment Memo")
        right_area = st.empty()
        right_area.info("Review the Critic's score below, then approve to generate...")

    # Stream Phase 1 — stops at interrupt_before=["writer"]
    for step in graph_hitl.stream(initial_state, thread, stream_mode="updates"):
        for node_name, updates in step.items():
            text = _node_text(node_name, updates)
            if node_name in slots:
                slots[node_name].markdown(text)
            ss.node_texts[node_name] = text

            if node_name == "search":
                m_iter.metric("Iterations", updates.get("iteration", 1))
            elif node_name == "critic":
                m_score.metric("Score", f"{updates.get('score', 0)}/10")

    # Show score chart inline (same execution)
    with left:
        st.divider()
        _score_chart(ss.iter_scores, ticker)

    # Determine phase from graph snapshot
    snapshot   = graph_hitl.get_state(thread)
    ss.score   = snapshot.values.get("score", 0)
    ss.missing = snapshot.values.get("missing_topics", [])

    if snapshot.next:       # snapshot.next == ("writer",) → interrupted
        ss.phase = "paused"
    else:                   # finished without interrupt (shouldn't happen here)
        ss.phase = "done"


# ══════════════════════════════════════════════════════════════════
# PHASE B — Show stored results (re-renders on every subsequent execution)
# This handles: after generate_btn rerun, page refresh, etc.
# ══════════════════════════════════════════════════════════════════
elif ss.phase in ["paused", "done"] and ss.node_texts:
    st.divider()
    left, right = st.columns([1, 1.7])

    with left:
        st.subheader("🔄 Pipeline Progress")
        for text in ss.node_texts.values():
            st.markdown(text)

        if ss.iter_scores:
            st.divider()
            mc1, mc2 = st.columns(2)
            mc1.metric("Iterations", len(ss.iter_scores))
            mc2.metric("Score", f"{ss.score}/10")
            _score_chart(ss.iter_scores, ss.ticker)

    with right:
        st.subheader("📝 Investment Memo")
        if ss.memo:
            st.markdown(ss.memo)
            st.download_button(
                "⬇️  Download Memo (.txt)", ss.memo,
                file_name=f"{ss.ticker}_memo.txt", mime="text/plain"
            )
        else:
            st.info("Memo appears after generation...")


# ══════════════════════════════════════════════════════════════════
# HITL SECTION — shown whenever phase == "paused"
# Renders at the bottom of Phase A (same execution) AND in Phase B
# executions (when generate_btn is about to be clicked)
# ══════════════════════════════════════════════════════════════════
if ss.phase == "paused":
    st.divider()
    st.subheader("⏸️  Human-in-the-Loop — Paused Before Writer")

    hc1, hc2 = st.columns([1, 2])
    with hc1:
        st.metric(
            "Research Score", f"{ss.score} / 10",
            delta="ready" if ss.score >= 6.0 else "max iterations reached"
        )
    with hc2:
        if ss.missing:
            st.caption("**Gaps identified by Critic (for reference):**")
            for m in ss.missing[:5]:
                st.caption(f"• {m}")

    st.markdown("**Add instructions for the Writer** _(optional)_")
    feedback = st.text_area(
        "instructions",
        placeholder=(
            "Examples:\n"
            "• 'Focus on downside risks and regulatory threats'\n"
            "• 'Write from a long-term (5-year) investor perspective'\n"
            "• 'Give a clear Buy / Hold / Sell recommendation'\n"
            "• 'Compare performance vs Microsoft and Google'"
        ),
        key="hitl_feedback",
        height=110,
        label_visibility="collapsed",
    )

    gc1, gc2, _ = st.columns([1, 1, 3])
    with gc1:
        generate_btn = st.button("✍️  Generate Memo", type="primary", use_container_width=True)
    with gc2:
        skip_btn = st.button("⏭  Skip (no notes)", use_container_width=True)

    if generate_btn or skip_btn:
        from graph import graph_hitl

        thread  = ss.thread
        fb_text = feedback.strip() if generate_btn else ""

        # graph.update_state() injects human_feedback into the checkpoint
        # before the Writer node reads it
        if fb_text:
            graph_hitl.update_state(thread, {"human_feedback": fb_text})
            st.info(f"📝 Injected: _{fb_text[:90]}{'...' if len(fb_text) > 90 else ''}_")

        st.subheader("✍️  Generating memo...")
        memo_live = st.empty()

        # graph.stream(None, thread) resumes from the checkpoint
        for step in graph_hitl.stream(None, thread, stream_mode="updates"):
            for node_name, updates in step.items():
                text = _node_text(node_name, updates)
                ss.node_texts[node_name] = text
                if node_name == "writer":
                    memo_live.markdown(ss.memo)

        ss.phase = "done"
        st.rerun()  # clean redraw: Phase B renders memo in right column


# ── Idle hint ─────────────────────────────────────────────────────
if ss.phase == "idle":
    st.info("Enter a stock ticker above and click **▶  Research** to start.")
