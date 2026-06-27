import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Streamlit Community Cloud: load API key from secrets if not in .env
if "GOOGLE_API_KEY" not in os.environ:
    try:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass

st.set_page_config(
    page_title="Investment Research AI",
    page_icon="📈",
    layout="wide",
)

# ── CSS ────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
section[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(160deg, #1a237e 0%, #283593 100%);
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div { color: rgba(255,255,255,0.88) !important; }
section[data-testid="stSidebar"] .stCaption p { color: rgba(255,255,255,0.55) !important; font-size: 0.8em !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
section[data-testid="stSidebar"] img {
    border-radius: 10px;
    background: white;
    padding: 8px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25);
}

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1565c0 0%, #1a237e 100%) !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; letter-spacing: 0.03em !important;
    box-shadow: 0 2px 10px rgba(21,101,192,0.35) !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 18px rgba(21,101,192,0.5) !important;
    transform: translateY(-1px) !important;
}
/* Secondary button */
.stButton > button:not([kind="primary"]) {
    border-radius: 8px !important; border: 1.5px solid #c5cae9 !important;
    color: #546e7a !important; font-weight: 500 !important; background: white !important;
}

/* Ticker input */
.stTextInput > div > div > input {
    border-radius: 8px !important; border: 2px solid #e8eaf6 !important;
    font-size: 1.1em !important; font-weight: 700 !important;
    letter-spacing: 0.1em !important; background: white !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1565c0 !important;
    box-shadow: 0 0 0 3px rgba(21,101,192,0.1) !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: white !important; border-radius: 10px !important;
    padding: 14px 18px !important; border: 1px solid #e8eaf6 !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
}

/* Text area */
.stTextArea > div > div > textarea {
    border-radius: 8px !important; border: 1.5px solid #e8eaf6 !important;
    font-size: 0.9em !important; line-height: 1.6 !important;
}
.stTextArea > div > div > textarea:focus {
    border-color: #1565c0 !important;
    box-shadow: 0 0 0 3px rgba(21,101,192,0.1) !important;
}

/* Download button */
.stDownloadButton > button {
    border-radius: 8px !important; border: 1.5px solid #1565c0 !important;
    color: #1565c0 !important; font-weight: 600 !important; background: white !important;
}
.stAlert { border-radius: 10px !important; }
</style>""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────
_DEFAULTS = {
    "phase":         "idle",
    "thread":        None,
    "ticker":        "",
    "node_texts":    {},
    "iter_scores":   [],
    "score":         0.0,
    "missing":       [],
    "memo":          "",
    "total_results": 0,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

ss = st.session_state

_META = {
    "planner":         ("🧠", "Planner"),
    "search":          ("🔍", "Search"),
    "rag":             ("📄", "RAG"),
    "critic":          ("⚖️", "Critic"),
    "query_transform": ("🔄", "Query Transform"),
    "writer":          ("✍️", "Writer"),
}

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📈 Investment Research AI")
    st.caption("GenAI Group Project · IE University · 2026")
    st.divider()

    st.markdown("**Pipeline Graph**")

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
    st.markdown("**LangGraph Features**")
    for feat in [
        "MemorySaver checkpointer",
        "interrupt_before=['writer']",
        "graph.update_state() HITL",
        "@tool decorator on search",
        "draw_mermaid_png() viz",
        "Pydantic structured output",
        "Self-Corrective RAG loop",
    ]:
        st.caption(f"✅ {feat}")
    st.divider()
    st.caption("Score threshold: 6.0  ·  Max iterations: 3")


# ── Hero header ───────────────────────────────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, #1a237e 0%, #1565c0 60%, #0288d1 100%);
    border-radius: 14px; padding: 2rem 2.5rem 1.8rem; margin-bottom: 1.5rem; color: white;
">
    <div style="font-size:1.9rem; font-weight:700; letter-spacing:-0.01em; margin-bottom:0.4rem;">
        Autonomous Investment Research Pipeline
    </div>
    <div style="font-size:0.97rem; opacity:0.85; line-height:1.6;">
        Enter a stock ticker — the AI searches the web, retrieves earnings PDFs,
        self-critiques its research quality, and generates a professional investment memo
        in under 60 seconds.
    </div>
    <div style="margin-top:1.1rem; display:flex; gap:0.5rem; flex-wrap:wrap;">
        <span style="background:rgba(255,255,255,0.18);border-radius:20px;padding:3px 12px;font-size:0.8em;font-weight:500;">🔗 LangGraph</span>
        <span style="background:rgba(255,255,255,0.18);border-radius:20px;padding:3px 12px;font-size:0.8em;font-weight:500;">📄 RAG</span>
        <span style="background:rgba(255,255,255,0.18);border-radius:20px;padding:3px 12px;font-size:0.8em;font-weight:500;">⚖️ LLM-as-Judge</span>
        <span style="background:rgba(255,255,255,0.18);border-radius:20px;padding:3px 12px;font-size:0.8em;font-weight:500;">👤 Human-in-the-Loop</span>
        <span style="background:rgba(255,255,255,0.18);border-radius:20px;padding:3px 12px;font-size:0.8em;font-weight:500;">🔄 Self-Corrective</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Input row ─────────────────────────────────────────────────────
st.markdown("<div style='font-size:0.85em;font-weight:600;color:#546e7a;margin-bottom:4px;letter-spacing:0.05em;'>STOCK TICKER</div>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([2, 1.2, 3.8])
with c1:
    ticker_input = st.text_input(
        "Ticker", value="AAPL",
        placeholder="AAPL · TSLA · MSFT · NVDA",
        label_visibility="collapsed",
    )
with c2:
    run_btn = st.button("▶  Research", type="primary", use_container_width=True)
with c3:
    st.markdown("<div style='padding-top:6px;color:#90a4ae;font-size:0.82em;'>Try: AAPL · TSLA · MSFT · NVDA · GOOGL · AMZN</div>", unsafe_allow_html=True)


# ── Node HTML card ────────────────────────────────────────────────
def _node_card(state: str, icon: str, name: str, detail: str) -> str:
    cfg = {
        "waiting": ("#f8f9fc", "#c5cae9", "#9e9e9e", "#bdbdbd", "⏳"),
        "done":    ("#f0fdf4", "#4ade80", "#166534", "#555",    "✅"),
        "green":   ("#f0fdf4", "#4ade80", "#166534", "#555",    "🟢"),
        "yellow":  ("#fefce8", "#facc15", "#854d0e", "#555",    "🟡"),
        "red":     ("#fef2f2", "#f87171", "#991b1b", "#555",    "🔴"),
    }
    bg, border, title_c, detail_c, prefix = cfg.get(state, cfg["waiting"])
    return (
        f'<div style="background:{bg};border-left:3px solid {border};'
        f'border-radius:0 8px 8px 0;padding:9px 14px;margin:4px 0;">'
        f'<div style="font-weight:600;color:{title_c};font-size:0.88em;">'
        f'{prefix} {icon} {name}</div>'
        f'<div style="color:{detail_c};font-size:0.78em;margin-top:1px;">{detail}</div>'
        f'</div>'
    )


def _node_html(node_name: str, updates: dict) -> str:
    icon, name = _META.get(node_name, ("•", node_name))
    if node_name == "planner":
        n = len(updates.get("search_queries", []))
        return _node_card("done", icon, name, f"{n} targeted queries generated")
    if node_name == "search":
        ss.total_results += len(updates.get("search_results", []))
        it = updates.get("iteration", 1)
        return _node_card("done", icon, name, f"{ss.total_results} results collected · iteration {it}")
    if node_name == "rag":
        ctx = len(updates.get("rag_context", ""))
        return _node_card("done", icon, name, f"{ctx:,} chars retrieved from PDF")
    if node_name == "query_transform":
        n = len(updates.get("search_queries", []))
        return _node_card("done", icon, name, f"rewrote into {n} targeted queries")
    if node_name == "critic":
        score = updates.get("score", 0)
        ss.iter_scores.append(score)
        done  = score >= 6.0 or len(ss.iter_scores) >= 3
        state = "green" if score >= 7 else "yellow" if score >= 5 else "red"
        arrow = "→ proceeding to write" if done else "→ rewriting queries"
        return _node_card(state, icon, name, f"score {score}/10 · {arrow}")
    if node_name == "writer":
        memo = updates.get("memo", "")
        ss.memo = memo
        return _node_card("done", icon, name, f"memo ready · {len(memo):,} chars")
    return _node_card("done", icon, name, "complete")


# ── Score chart ───────────────────────────────────────────────────
def _score_chart(scores: list, ticker: str):
    if not scores:
        return
    import plotly.graph_objects as go
    dot_colors = ["#22c55e" if s >= 7 else "#eab308" if s >= 5 else "#ef4444" for s in scores]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(scores) + 1)), y=scores,
        mode="lines+markers",
        line=dict(color="#1565c0", width=2.5),
        marker=dict(size=11, color=dot_colors, line=dict(color="white", width=2)),
    ))
    fig.add_hline(y=6.0, line_dash="dash", line_color="#f97316",
                  annotation_text="Pass threshold 6.0", annotation_position="top right",
                  annotation_font_color="#f97316", annotation_font_size=11)
    fig.update_layout(
        title=dict(text=f"{ticker} — Research Quality Score", font=dict(size=13, color="#374151")),
        xaxis=dict(title="Iteration", tickmode="linear", dtick=1,
                   gridcolor="#f3f4f6", title_font_size=11),
        yaxis=dict(title="Score (0–10)", range=[0, 10.5],
                   gridcolor="#f3f4f6", title_font_size=11),
        height=220, margin=dict(t=40, b=30, l=40, r=20),
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Section card helpers ──────────────────────────────────────────
def _card_start(title: str, subtitle: str = ""):
    sub = f'<div style="color:#78909c;font-size:0.8em;margin-top:2px;">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div style="background:white;border-radius:12px;padding:1.2rem 1.4rem 0.6rem;
                border:1px solid #e8eaf6;box-shadow:0 1px 6px rgba(0,0,0,0.05);margin-bottom:0.4rem;">
        <div style="font-weight:700;color:#1a237e;font-size:1rem;margin-bottom:0.5rem;">
            {title}
        </div>{sub}
    """, unsafe_allow_html=True)

def _card_end():
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PHASE A — run button clicked, stream pipeline
# ══════════════════════════════════════════════════════════════════
if run_btn and ticker_input:
    from graph import graph_hitl

    ticker = ticker_input.strip().upper()
    thread = {"configurable": {"thread_id": f"{ticker}_{int(time.time())}"}}
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

    st.markdown("<hr style='border:none;border-top:1px solid #e8eaf6;margin:0.5rem 0 1rem;'>", unsafe_allow_html=True)
    left, right = st.columns([1, 1.7])

    with left:
        st.markdown("**🔄 Pipeline Progress**")
        slots = {k: st.empty() for k in _META}
        for k, (icon, name) in _META.items():
            slots[k].markdown(
                _node_card("waiting", icon, name, "waiting…"),
                unsafe_allow_html=True,
            )
        st.divider()
        mc1, mc2 = st.columns(2)
        m_iter  = mc1.empty()
        m_score = mc2.empty()
        m_iter.metric("Iterations", "—")
        m_score.metric("Score", "—")

    with right:
        st.markdown("**📝 Investment Memo**")
        right_area = st.empty()
        right_area.info("Pipeline is running… memo will appear here after the human review step.")

    for step in graph_hitl.stream(initial_state, thread, stream_mode="updates"):
        for node_name, updates in step.items():
            html = _node_html(node_name, updates)
            if node_name in slots:
                slots[node_name].markdown(html, unsafe_allow_html=True)
            ss.node_texts[node_name] = html
            if node_name == "search":
                m_iter.metric("Iterations", updates.get("iteration", 1))
            elif node_name == "critic":
                m_score.metric("Score", f"{updates.get('score', 0)}/10")

    with left:
        st.divider()
        _score_chart(ss.iter_scores, ticker)

    snapshot   = graph_hitl.get_state(thread)
    ss.score   = snapshot.values.get("score", 0)
    ss.missing = snapshot.values.get("missing_topics", [])
    ss.phase   = "paused" if snapshot.next else "done"


# ══════════════════════════════════════════════════════════════════
# PHASE B — persistent results display
# ══════════════════════════════════════════════════════════════════
elif ss.phase in ["paused", "done"] and ss.node_texts:
    st.markdown("<hr style='border:none;border-top:1px solid #e8eaf6;margin:0.5rem 0 1rem;'>", unsafe_allow_html=True)
    left, right = st.columns([1, 1.7])

    with left:
        st.markdown("**🔄 Pipeline Progress**")
        for html in ss.node_texts.values():
            st.markdown(html, unsafe_allow_html=True)
        if ss.iter_scores:
            st.divider()
            mc1, mc2 = st.columns(2)
            mc1.metric("Iterations", len(ss.iter_scores))
            mc2.metric("Score", f"{ss.score}/10")
            _score_chart(ss.iter_scores, ss.ticker)

    with right:
        st.markdown("**📝 Investment Memo**")
        if ss.memo:
            st.markdown(
                f'<div style="background:white;border-radius:12px;padding:1.4rem 1.6rem;'
                f'border:1px solid #e8eaf6;box-shadow:0 1px 6px rgba(0,0,0,0.05);'
                f'font-size:0.92em;line-height:1.75;color:#212121;">{ss.memo}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)
            st.download_button(
                "⬇️  Download Memo (.txt)", ss.memo,
                file_name=f"{ss.ticker}_memo.txt", mime="text/plain",
            )
        else:
            st.info("Memo will appear here after generation.")


# ══════════════════════════════════════════════════════════════════
# HITL SECTION
# ══════════════════════════════════════════════════════════════════
if ss.phase == "paused":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#fff8e1,#fffde7);
                border:1.5px solid #f9a825;border-radius:14px;
                padding:1.4rem 1.6rem 0.8rem;margin-top:1rem;">
        <div style="font-size:1.05rem;font-weight:700;color:#e65100;margin-bottom:0.3rem;">
            ⏸️ Human-in-the-Loop — Pipeline Paused Before Writer
        </div>
        <div style="font-size:0.85rem;color:#795548;line-height:1.5;">
            The research phase is complete. Review the score below, optionally add analyst
            instructions, then click <b>Generate Memo</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)
    hc1, hc2 = st.columns([1, 2])
    with hc1:
        st.metric(
            "Research Score", f"{ss.score} / 10",
            delta="✓ ready to write" if ss.score >= 6.0 else "max iterations reached",
        )
    with hc2:
        if ss.missing:
            st.markdown("<div style='font-size:0.82em;font-weight:600;color:#546e7a;margin-bottom:4px;'>Gaps identified by Critic:</div>", unsafe_allow_html=True)
            for m in ss.missing[:5]:
                st.markdown(f"<div style='font-size:0.82em;color:#607d8b;'>• {m}</div>", unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.85em;font-weight:600;color:#546e7a;margin:0.8rem 0 4px;'>Analyst instructions for the Writer <span style='font-weight:400;color:#90a4ae;'>(optional)</span></div>", unsafe_allow_html=True)
    feedback = st.text_area(
        "instructions",
        placeholder=(
            "Examples:\n"
            "• Focus on downside risks and regulatory threats\n"
            "• Write from a long-term (5-year) investor perspective\n"
            "• Give a clear Buy / Hold / Sell recommendation\n"
            "• Compare performance vs Microsoft and Google"
        ),
        key="hitl_feedback",
        height=110,
        label_visibility="collapsed",
    )

    gc1, gc2, _ = st.columns([1.2, 1, 3.8])
    with gc1:
        generate_btn = st.button("✍️  Generate Memo", type="primary", use_container_width=True)
    with gc2:
        skip_btn = st.button("⏭  Skip", use_container_width=True)

    if generate_btn or skip_btn:
        from graph import graph_hitl
        thread  = ss.thread
        fb_text = feedback.strip() if generate_btn else ""

        if fb_text:
            graph_hitl.update_state(thread, {"human_feedback": fb_text})
            st.info(f"📝 Analyst instruction injected: _{fb_text[:100]}{'…' if len(fb_text) > 100 else ''}_")

        st.markdown("**✍️ Generating memo…**")
        memo_live = st.empty()

        for step in graph_hitl.stream(None, thread, stream_mode="updates"):
            for node_name, updates in step.items():
                html = _node_html(node_name, updates)
                ss.node_texts[node_name] = html
                if node_name == "writer":
                    memo_live.markdown(ss.memo)

        ss.phase = "done"
        st.rerun()


# ── Idle state ────────────────────────────────────────────────────
if ss.phase == "idle":
    st.markdown("""
    <div style="background:white;border-radius:12px;padding:2rem 2.5rem;
                border:1px solid #e8eaf6;box-shadow:0 1px 6px rgba(0,0,0,0.05);
                text-align:center;margin-top:1rem;">
        <div style="font-size:2.5rem;margin-bottom:0.6rem;">📈</div>
        <div style="font-weight:700;color:#1a237e;font-size:1.1rem;margin-bottom:0.4rem;">
            Ready to research
        </div>
        <div style="color:#78909c;font-size:0.9rem;line-height:1.6;max-width:480px;margin:0 auto;">
            Enter a stock ticker above and click <b>Research</b>.<br>
            The pipeline will search the web, retrieve earnings data,
            evaluate quality, and generate a professional investment memo.
        </div>
        <div style="margin-top:1.2rem;display:flex;justify-content:center;gap:0.5rem;flex-wrap:wrap;">
            <span style="background:#e8eaf6;border-radius:20px;padding:4px 14px;font-size:0.82em;font-weight:600;color:#1a237e;">AAPL</span>
            <span style="background:#e8eaf6;border-radius:20px;padding:4px 14px;font-size:0.82em;font-weight:600;color:#1a237e;">TSLA</span>
            <span style="background:#e8eaf6;border-radius:20px;padding:4px 14px;font-size:0.82em;font-weight:600;color:#1a237e;">MSFT</span>
            <span style="background:#e8eaf6;border-radius:20px;padding:4px 14px;font-size:0.82em;font-weight:600;color:#1a237e;">NVDA</span>
            <span style="background:#e8eaf6;border-radius:20px;padding:4px 14px;font-size:0.82em;font-weight:600;color:#1a237e;">GOOGL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
