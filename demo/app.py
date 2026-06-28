import sys, os, time, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Streamlit Community Cloud: load API keys from secrets if not already in .env/env
for _key in ("GOOGLE_API_KEY", "TAVILY_API_KEY"):
    if _key not in os.environ:
        try:
            os.environ[_key] = st.secrets[_key]
        except Exception:
            pass

st.set_page_config(
    page_title="Investment Research AI",
    page_icon="📈",
    layout="wide",
)

# ════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ════════════════════════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
    --navy-900:#070b1f; --navy-800:#0c1330; --navy-700:#141d44;
    --brand:#3b82f6; --brand-deep:#2563eb; --brand-soft:#60a5fa;
    --accent:#6366f1; --teal:#14b8a6;
    --pos:#10b981; --warn:#f59e0b; --neg:#ef4444;
    --ink:#0f172a; --ink-2:#334155; --muted:#64748b; --faint:#94a3b8;
    --line:rgba(15,23,42,0.08); --line-2:rgba(15,23,42,0.04);
    --surface:#ffffff; --surface-2:#f8fafc;
    --shadow-sm:0 1px 2px rgba(15,23,42,0.04), 0 2px 6px rgba(15,23,42,0.04);
    --shadow-md:0 2px 4px rgba(15,23,42,0.04), 0 12px 28px -10px rgba(15,23,42,0.18);
    --shadow-lg:0 8px 16px -6px rgba(15,23,42,0.10), 0 24px 48px -16px rgba(20,30,90,0.30);
    --radius:18px;
}

/* base */
#MainMenu, footer, header { visibility:hidden; }
html, body, [class*="css"] { font-family:'Inter',sans-serif; color:var(--ink); }
.block-container { padding-top:1.2rem !important; padding-bottom:3rem; max-width:1200px; }
.stApp {
    background:
      radial-gradient(900px 480px at 88% -8%, rgba(59,130,246,0.12), transparent 60%),
      radial-gradient(760px 440px at -6% 4%, rgba(99,102,241,0.10), transparent 55%),
      radial-gradient(600px 600px at 50% 120%, rgba(20,184,166,0.06), transparent 60%),
      #eef2f9;
}
h1,h2,h3,h4 { font-family:'Sora',sans-serif; letter-spacing:-0.02em; }

/* ── keyframes ─────────────────────────────────────────────────── */
@keyframes fadeUp   { from{opacity:0;transform:translateY(16px);} to{opacity:1;transform:translateY(0);} }
@keyframes pop      { 0%{opacity:0;transform:scale(.95) translateX(-8px);} 60%{transform:scale(1.015);} 100%{opacity:1;transform:scale(1) translateX(0);} }
@keyframes pulse    { 0%,100%{opacity:.5;} 50%{opacity:1;} }
@keyframes gradPan  { 0%{background-position:0% 50%;} 50%{background-position:100% 50%;} 100%{background-position:0% 50%;} }
@keyframes shimmer  { 0%{background-position:-480px 0;} 100%{background-position:480px 0;} }
@keyframes spin     { to{transform:rotate(360deg);} }
@keyframes floaty   { 0%,100%{transform:translateY(0);} 50%{transform:translateY(-6px);} }
@keyframes marquee  { 0%{transform:translateX(0);} 100%{transform:translateX(-50%);} }
@keyframes ring     { from{stroke-dashoffset:264;} }
@keyframes glow     { 0%,100%{box-shadow:0 0 0 0 rgba(59,130,246,.0);} 50%{box-shadow:0 0 0 6px rgba(59,130,246,.10);} }

.main .block-container > div { animation:fadeUp .55s cubic-bezier(.2,.7,.2,1) both; }

/* ── sidebar ───────────────────────────────────────────────────── */
section[data-testid="stSidebar"] > div:first-child {
    background:linear-gradient(165deg,#070b1f 0%,#0c1330 50%,#141d44 100%);
    border-right:1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] * { color:rgba(255,255,255,0.86) !important; }
section[data-testid="stSidebar"] .stCaption p { color:rgba(255,255,255,0.55) !important; font-size:.78em !important; }
section[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,0.10) !important; }
section[data-testid="stSidebar"] img {
    border-radius:12px; background:#fff; padding:10px;
    box-shadow:0 10px 30px rgba(0,0,0,.35); transition:transform .3s ease;
}
section[data-testid="stSidebar"] img:hover { transform:scale(1.03); }

/* ── buttons ───────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#3b82f6 0%,#2563eb 45%,#4f46e5 100%) !important;
    background-size:180% 180% !important;
    border:none !important; border-radius:12px !important; color:#fff !important;
    font-weight:700 !important; letter-spacing:.02em !important; padding:.62rem 1rem !important;
    box-shadow:0 6px 20px rgba(37,99,235,.40) !important;
    transition:transform .18s ease, box-shadow .18s ease, background-position .5s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform:translateY(-2px) !important; background-position:100% 50% !important;
    box-shadow:0 12px 30px rgba(37,99,235,.55) !important;
}
.stButton > button[kind="primary"]:active { transform:translateY(0) scale(.98) !important; }
.stButton > button:not([kind="primary"]) {
    border-radius:12px !important; border:1.5px solid #d6def0 !important;
    color:#475569 !important; font-weight:600 !important; background:#fff !important;
    transition:all .18s ease !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color:var(--brand) !important; color:var(--brand) !important; transform:translateY(-1px) !important;
    box-shadow:0 6px 18px rgba(59,130,246,.16) !important;
}
.stDownloadButton > button {
    border-radius:12px !important; border:1.5px solid var(--brand) !important;
    color:var(--brand) !important; font-weight:700 !important; background:#fff !important;
    transition:all .18s ease !important;
}
.stDownloadButton > button:hover {
    background:var(--brand) !important; color:#fff !important; transform:translateY(-2px) !important;
    box-shadow:0 10px 26px rgba(59,130,246,.35) !important;
}

/* ── inputs ────────────────────────────────────────────────────── */
.stTextInput > div > div > input {
    border-radius:12px !important; border:2px solid var(--line) !important;
    font-size:1.15em !important; font-weight:700 !important; letter-spacing:.12em !important;
    background:#fff !important; padding:.55rem .9rem !important;
    transition:border-color .2s ease, box-shadow .2s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color:var(--brand) !important; box-shadow:0 0 0 4px rgba(59,130,246,.15) !important;
}
.stTextArea > div > div > textarea {
    border-radius:12px !important; border:1.5px solid var(--line) !important;
    font-size:.9em !important; line-height:1.6 !important;
    transition:border-color .2s ease, box-shadow .2s ease !important;
}
.stTextArea > div > div > textarea:focus {
    border-color:var(--brand) !important; box-shadow:0 0 0 4px rgba(59,130,246,.15) !important;
}
.stAlert { border-radius:14px !important; animation:fadeUp .4s ease both; }

/* native metric fallback */
[data-testid="stMetric"] {
    background:#fff !important; border-radius:14px !important; padding:14px 18px !important;
    border:1px solid var(--line) !important; box-shadow:var(--shadow-sm) !important;
    transition:transform .2s ease, box-shadow .2s ease !important; animation:pop .5s ease both;
}
[data-testid="stMetric"]:hover { transform:translateY(-3px) !important; box-shadow:var(--shadow-md) !important; }
[data-testid="stMetricValue"] { color:var(--navy-800) !important; font-weight:800 !important; font-family:'Sora',sans-serif !important; }

/* ── HERO ──────────────────────────────────────────────────────── */
.hero {
    position:relative; overflow:hidden; border-radius:24px; color:#fff;
    padding:2.4rem 2.8rem 0; margin-bottom:1.6rem;
    background:linear-gradient(125deg,#070b1f 0%,#141d44 40%,#1e3a8a 78%,#2563eb 100%);
    background-size:200% 200%; animation:gradPan 16s ease infinite, fadeUp .6s ease both;
    box-shadow:var(--shadow-lg);
}
.hero::before {
    content:""; position:absolute; inset:0;
    background-image:radial-gradient(rgba(255,255,255,.10) 1px, transparent 1px);
    background-size:22px 22px; opacity:.5; pointer-events:none;
    -webkit-mask-image:linear-gradient(180deg,#000,transparent 70%);
            mask-image:linear-gradient(180deg,#000,transparent 70%);
}
.hero::after {
    content:""; position:absolute; top:-40%; right:-10%; width:420px; height:420px;
    background:radial-gradient(circle, rgba(99,102,241,.55), transparent 60%);
    filter:blur(20px); pointer-events:none;
}
.hero-inner { position:relative; z-index:1; }
.hero-pill {
    display:inline-flex; align-items:center; gap:7px; font-size:.72rem; font-weight:700;
    letter-spacing:.14em; text-transform:uppercase; color:#cde0ff;
    background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.16);
    padding:5px 12px; border-radius:30px; backdrop-filter:blur(6px); margin-bottom:1rem;
}
.hero-dot { width:8px; height:8px; border-radius:50%; background:#34d399; box-shadow:0 0 0 0 rgba(52,211,153,.6); animation:glow 2.2s infinite; }
.hero-title { font-family:'Sora',sans-serif; font-size:2.4rem; font-weight:800; line-height:1.08; letter-spacing:-0.03em; margin:0 0 .55rem; }
.hero-title .grad { background:linear-gradient(90deg,#93c5fd,#c4b5fd); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.hero-sub { font-size:1rem; line-height:1.65; color:rgba(255,255,255,.82); max-width:760px; }
.hero-chips { display:flex; gap:.55rem; flex-wrap:wrap; margin-top:1.3rem; }
.chip {
    display:inline-flex; align-items:center; gap:6px; font-size:.8rem; font-weight:600;
    color:#eaf1ff; background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.14);
    padding:6px 14px; border-radius:30px; backdrop-filter:blur(6px);
    transition:transform .2s ease, background .2s ease;
}
.chip:hover { transform:translateY(-3px); background:rgba(255,255,255,.22); }

/* ticker tape */
.tape { position:relative; z-index:1; margin:1.6rem -2.8rem 0; overflow:hidden;
        border-top:1px solid rgba(255,255,255,.10); background:rgba(0,0,0,.18); }
.tape-track { display:flex; gap:2.4rem; width:max-content; padding:.6rem 0;
              animation:marquee 26s linear infinite; font-family:'JetBrains Mono',monospace; font-size:.82rem; }
.tape-item { display:inline-flex; align-items:center; gap:8px; color:#dbe7ff; white-space:nowrap; }
.tape-up { color:#34d399; } .tape-dn { color:#fb7185; }

/* ── section labels ────────────────────────────────────────────── */
.lbl { font-size:.72rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase;
       color:var(--muted); margin:0 0 .5rem; display:flex; align-items:center; gap:8px; }
.lbl::before { content:""; width:16px; height:2px; border-radius:2px; background:linear-gradient(90deg,var(--brand),var(--accent)); }

/* ── search bar wrapper ────────────────────────────────────────── */
.searchwrap {
    background:#fff; border:1px solid var(--line); border-radius:16px; padding:.5rem;
    box-shadow:var(--shadow-sm); display:flex; align-items:center; gap:.5rem;
}

/* ── pipeline stepper ──────────────────────────────────────────── */
.step {
    display:flex; gap:14px; align-items:flex-start; padding:11px 14px; margin:0;
    background:#fff; border:1px solid var(--line); border-radius:14px;
    box-shadow:var(--shadow-sm); transition:transform .18s ease, box-shadow .18s ease;
}
.step + .step, .step { margin-top:8px; }
.step:hover { transform:translateX(3px); box-shadow:var(--shadow-md); }
.step.s-done  { animation:pop .45s cubic-bezier(.2,.8,.2,1) both; }
.step.s-wait  { opacity:.72; }
.step.s-run   { border-color:var(--brand) !important; background:rgba(59,130,246,.06) !important; animation:pulse 1.4s ease-in-out infinite; }
.step-badge {
    flex:0 0 34px; width:34px; height:34px; border-radius:11px; display:flex; align-items:center;
    justify-content:center; font-size:1rem; box-shadow:inset 0 0 0 1px rgba(255,255,255,.4);
}
.step-name { font-family:'Sora',sans-serif; font-weight:700; font-size:.92rem; color:var(--ink); }
.step-detail { font-size:.78rem; color:var(--muted); margin-top:2px; }
.spinner { display:inline-block; width:11px; height:11px; margin-right:6px;
           border:2px solid rgba(59,130,246,.25); border-top-color:var(--brand);
           border-radius:50%; animation:spin .7s linear infinite; vertical-align:-1px; }

/* ── KPI tile ──────────────────────────────────────────────────── */
.kpi { background:#fff; border:1px solid var(--line); border-radius:16px; padding:16px 18px;
       box-shadow:var(--shadow-sm); animation:pop .5s ease both; }
.kpi-lbl { font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--faint); white-space:nowrap; }
.kpi-val { font-family:'Sora',sans-serif; font-weight:800; font-size:1.55rem; color:var(--navy-800); line-height:1.1; margin-top:4px; white-space:nowrap; }
.kpi-sub { font-size:.74rem; color:var(--muted); margin-top:2px; }

/* ── score gauge ───────────────────────────────────────────────── */
.gauge-wrap { background:#fff; border:1px solid var(--line); border-radius:16px; padding:14px;
              box-shadow:var(--shadow-sm); display:flex; align-items:center; gap:14px; animation:pop .5s ease both; }
.gauge-txt .gv { font-family:'Sora',sans-serif; font-weight:800; font-size:1.5rem; line-height:1; }
.gauge-txt .gl { font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--faint); }
.gauge svg circle.bg { stroke:#eef2f9; }
.gauge svg circle.fg { stroke-linecap:round; transform:rotate(-90deg); transform-origin:50% 50%; animation:ring 1s ease both; }

/* ── memo document card ────────────────────────────────────────── */
.doc { background:#fff; border:1px solid var(--line); border-radius:18px; overflow:hidden;
       box-shadow:var(--shadow-md); animation:pop .55s ease both; }
.doc-head { display:flex; align-items:center; justify-content:space-between; gap:12px;
            padding:1rem 1.4rem; background:linear-gradient(120deg,#070b1f,#141d44); color:#fff; }
.doc-tk { display:flex; align-items:center; gap:10px; }
.doc-tk .sym { font-family:'Sora',sans-serif; font-weight:800; font-size:1.15rem; letter-spacing:-0.01em; }
.doc-tk .meta { font-size:.74rem; color:rgba(255,255,255,.7); }
.reco { font-family:'Sora',sans-serif; font-weight:800; font-size:.82rem; letter-spacing:.08em;
        padding:6px 14px; border-radius:30px; }
.reco-buy  { background:rgba(16,185,129,.18); color:#34d399; border:1px solid rgba(16,185,129,.4); }
.reco-hold { background:rgba(245,158,11,.18); color:#fbbf24; border:1px solid rgba(245,158,11,.4); }
.reco-sell { background:rgba(239,68,68,.18); color:#fb7185; border:1px solid rgba(239,68,68,.4); }
.doc-body { padding:1.7rem 1.9rem 1.9rem; font-family:'Inter',sans-serif;
            font-size:.93rem; line-height:1.72; color:#3b4759; letter-spacing:.002em; }
/* memo title (first line) */
.doc-body > p:first-child { font-family:'Sora',sans-serif; font-size:1.12rem; font-weight:800;
            color:var(--navy-800); letter-spacing:-0.02em; margin:0 0 .5rem; }
.doc-body > p:first-child + p { color:var(--muted); font-size:.84rem;
            padding-bottom:.9rem; margin-bottom:.4rem; border-bottom:1px solid var(--line); }
/* section headings */
.doc-sec { font-family:'Sora',sans-serif; font-weight:700; color:var(--navy-800);
            font-size:1.04rem; letter-spacing:-0.01em; margin:1.6rem 0 .6rem;
            position:relative; padding-left:15px; }
.doc-sec::before { content:''; position:absolute; left:0; top:3px; bottom:3px; width:4px;
            border-radius:3px; background:linear-gradient(180deg,var(--brand),var(--accent)); }
.doc-sub { font-family:'Sora',sans-serif; font-weight:700; color:var(--brand-deep);
            font-size:.92rem; margin:1rem 0 .3rem; }
.doc-body p { margin:.6rem 0; }
.doc-body strong { color:var(--navy-800); font-weight:700; }
.doc-body em { color:var(--muted); font-style:normal; }
/* bullet lists with custom markers */
.doc-body ul { margin:.5rem 0 .8rem; padding-left:.2rem; list-style:none; }
.doc-body li { margin:.4rem 0; position:relative; padding-left:1.35rem; }
.doc-body li::before { content:'▸'; position:absolute; left:.25rem; top:0;
            color:var(--brand); font-weight:700; }
.doc-body hr { border:none; border-top:1px solid var(--line); margin:1.1rem 0; }

/* surface card */
.surface-card { animation:pop .5s ease both; }

/* scrollbar */
::-webkit-scrollbar { width:10px; height:10px; }
::-webkit-scrollbar-thumb { background:#cbd5e1; border-radius:10px; }
::-webkit-scrollbar-thumb:hover { background:var(--brand-soft); }
</style>""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────
_DEFAULTS = {
    "phase":"idle", "thread":None, "ticker":"", "node_texts":{},
    "iter_scores":[], "score":0.0, "missing":[], "memo":"", "total_results":0,
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

# ════════════════════════════════════════════════════════════════════
#  COMPONENT HELPERS
# ════════════════════════════════════════════════════════════════════
def _node_card(state: str, icon: str, name: str, detail: str) -> str:
    cfg = {
        "waiting": ("#f1f5f9",               "#94a3b8", "s-wait", "⏳"),
        "running": ("rgba(59,130,246,.15)",   "#3b82f6", "s-run",  "⚙️"),
        "done":    ("rgba(16,185,129,.12)",   "#10b981", "s-done", "✓"),
        "green":   ("rgba(16,185,129,.12)",   "#10b981", "s-done", "🟢"),
        "yellow":  ("rgba(245,158,11,.14)",   "#f59e0b", "s-done", "🟡"),
        "red":     ("rgba(239,68,68,.12)",    "#ef4444", "s-done", "🔴"),
    }
    badge_bg, badge_fg, anim, mark = cfg.get(state, cfg["waiting"])
    spinner = '<span class="spinner"></span>' if state == "running" else ""
    return (
        f'<div class="step {anim}">'
        f'<div class="step-badge" style="background:{badge_bg};color:{badge_fg};">{icon}</div>'
        f'<div style="flex:1;">'
        f'<div class="step-name">{name}</div>'
        f'<div class="step-detail">{spinner}{detail}</div>'
        f'</div></div>'
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
        done  = score >= 7.0 or len(ss.iter_scores) >= 3
        state = "green" if score >= 7 else "yellow" if score >= 5 else "red"
        arrow = "→ proceeding to write" if done else "→ rewriting queries"
        return _node_card(state, icon, name, f"score {score}/10 · {arrow}")
    if node_name == "writer":
        memo = updates.get("memo", "")
        ss.memo = memo
        return _node_card("done", icon, name, f"memo ready · {len(memo):,} chars")
    return _node_card("done", icon, name, "complete")


def _kpi_tile(label: str, value, sub: str = "") -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f'<div class="kpi"><div class="kpi-lbl">{label}</div><div class="kpi-val">{value}</div>{sub_html}</div>'


def _score_gauge(score: float) -> str:
    score = float(score or 0)
    color = "#10b981" if score >= 7 else "#f59e0b" if score >= 5 else "#ef4444"
    circ = 264.0
    off = circ - (min(score, 10) / 10.0) * circ
    return (
        '<div class="gauge-wrap">'
        '<div class="gauge"><svg width="78" height="78" viewBox="0 0 100 100">'
        '<circle class="bg" cx="50" cy="50" r="42" fill="none" stroke-width="9"/>'
        f'<circle class="fg" cx="50" cy="50" r="42" fill="none" stroke="{color}" '
        f'stroke-width="9" stroke-dasharray="{circ}" stroke-dashoffset="{off:.1f}"/>'
        f'<text x="50" y="55" text-anchor="middle" font-family="Sora" font-weight="800" '
        f'font-size="26" fill="{color}">{score:g}</text>'
        '</svg></div>'
        '<div class="gauge-txt"><div class="gl">Research Score</div>'
        f'<div class="gv" style="color:{color};">{score:g}<span style="color:#cbd5e1;font-size:1rem;"> / 10</span></div>'
        f'<div class="kpi-sub">{"✓ ready to write" if score >= 7 else "below threshold"}</div></div>'
        '</div>'
    )


def _extract_reco(memo: str):
    """Find the memo's actual recommendation, not just the first BUY/HOLD/SELL
    word (which may appear earlier in unrelated prose)."""
    t = memo or ""
    # 1) Prefer an explicit "Recommendation: X" line (allowing markdown **/_).
    m = re.search(r'recommendation[\s:_*\-–—]*\**\s*\b(BUY|HOLD|SELL)\b', t, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # 2) Otherwise take the LAST occurrence — the call sits in the closing summary.
    hits = re.findall(r'\b(BUY|HOLD|SELL)\b', t, re.IGNORECASE)
    return hits[-1].upper() if hits else None


def _md_to_html(md: str) -> str:
    """Minimal markdown → HTML for memo rendering (no external dependency)."""
    def inline(t: str) -> str:
        t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", t)
        return t

    html, para, bullets = [], [], []
    def flush_para():
        if para:
            html.append("<p>" + "<br>".join(inline(x) for x in para) + "</p>")
            para.clear()
    def flush_bul():
        if bullets:
            html.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in bullets) + "</ul>")
            bullets.clear()

    for raw in (md or "").split("\n"):
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush_para(); flush_bul(); continue
        if re.match(r"^#{1,6}\s", s):
            flush_para(); flush_bul()
            lvl = len(s) - len(s.lstrip("#"))
            cls = "doc-sec" if lvl <= 3 else "doc-sub"
            html.append(f'<div class="{cls}">{inline(s.lstrip("# ").strip())}</div>')
        elif re.match(r"^[-*•]\s+", s):
            flush_para()
            bullets.append(re.sub(r"^[-*•]\s+", "", s))
        elif re.match(r"^-{3,}$", s) or re.match(r"^_{3,}$", s):
            flush_para(); flush_bul(); html.append("<hr style='border:none;border-top:1px solid var(--line);margin:.8rem 0;'>")
        else:
            flush_bul(); para.append(s)
    flush_para(); flush_bul()
    return "".join(html)


def _memo_card(ticker: str, memo: str) -> str:
    import datetime
    reco = _extract_reco(memo)
    badge = ""
    if reco:
        cls = {"BUY": "reco-buy", "HOLD": "reco-hold", "SELL": "reco-sell"}[reco]
        badge = f'<span class="reco {cls}">● {reco}</span>'
    body = _md_to_html(memo)
    today = datetime.date.today().strftime("%b %d, %Y")
    return (
        '<div class="doc">'
        '<div class="doc-head"><div class="doc-tk">'
        '<div class="step-badge" style="background:rgba(255,255,255,.12);color:#fff;">📈</div>'
        f'<div><div class="sym">{ticker}</div>'
        f'<div class="meta">Equity Research Memo · {today}</div></div></div>'
        f'{badge}</div>'
        f'<div class="doc-body">{body}</div>'
        '</div>'
    )


def _score_chart(scores: list, ticker: str):
    if not scores:
        return
    import plotly.graph_objects as go
    dot_colors = ["#10b981" if s >= 7 else "#f59e0b" if s >= 5 else "#ef4444" for s in scores]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(scores) + 1)), y=scores, mode="lines+markers",
        line=dict(color="#3b82f6", width=3, shape="spline"),
        marker=dict(size=12, color=dot_colors, line=dict(color="white", width=2)),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
    ))
    fig.add_hline(y=7.0, line_dash="dash", line_color="#f59e0b",
                  annotation_text="Pass threshold 7.0", annotation_position="top right",
                  annotation_font_color="#f59e0b", annotation_font_size=11)
    fig.update_layout(
        title=dict(text=f"{ticker} — Research Quality by Iteration",
                   font=dict(size=13, color="#334155", family="Sora")),
        xaxis=dict(title="Iteration", tickmode="linear", dtick=1, gridcolor="#eef2f9", title_font_size=11),
        yaxis=dict(title="Score (0–10)", range=[0, 10.5], gridcolor="#eef2f9", title_font_size=11),
        height=230, margin=dict(t=42, b=30, l=40, r=20),
        showlegend=False, plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _show_api_error(e: Exception):
    msg = str(e)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
        st.error(
            "🚫 **API quota exhausted.** The free tier resets daily at **UTC 00:00**. "
            "Try again after the reset, or use a different API key."
        )
    else:
        st.error(f"⚠️ Pipeline error: {msg}")


# ════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="font-family:Sora;font-weight:800;font-size:1.15rem;color:#fff;">📈 Investment Research AI</div>'
        '<div style="font-size:.78rem;color:rgba(255,255,255,.55);margin-top:2px;">GenAI Project · IE University · 2026</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown('<div style="font-weight:700;color:#fff;font-size:.85rem;margin-bottom:.4rem;">Pipeline Graph</div>', unsafe_allow_html=True)

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
    st.markdown('<div style="font-weight:700;color:#fff;font-size:.85rem;margin-bottom:.4rem;">LangGraph Features</div>', unsafe_allow_html=True)
    for feat in [
        "MemorySaver checkpointer", "interrupt_before=['writer']",
        "graph.update_state() HITL", "@tool decorator on search",
        "draw_mermaid_png() viz", "Pydantic structured output", "Self-Corrective RAG loop",
    ]:
        st.caption(f"✅ {feat}")
    st.divider()
    st.caption("Score threshold: 7.0  ·  Max iterations: 3")


# ════════════════════════════════════════════════════════════════════
#  HERO
# ════════════════════════════════════════════════════════════════════
_tape_items = [
    ("AAPL", "▲ 1.2%", "tape-up"), ("TSLA", "▼ 0.8%", "tape-dn"),
    ("MSFT", "▲ 0.5%", "tape-up"), ("NVDA", "▲ 2.4%", "tape-up"),
    ("GOOGL", "▼ 0.3%", "tape-dn"), ("AMZN", "▲ 0.9%", "tape-up"),
    ("META", "▲ 1.6%", "tape-up"), ("JPM", "▼ 0.4%", "tape-dn"),
]
_tape_html = "".join(
    f'<span class="tape-item"><b>{t}</b> <span class="{c}">{v}</span></span>'
    for t, v, c in _tape_items * 2
)
st.markdown(f"""
<div class="hero"><div class="hero-inner">
    <div class="hero-pill"><span class="hero-dot"></span> Autonomous · Self-Correcting · Human-in-the-Loop</div>
    <div class="hero-title">Autonomous Investment<br><span class="grad">Research Pipeline</span></div>
    <div class="hero-sub">
        Enter a stock ticker — the AI plans targeted queries, searches the web, retrieves
        earnings filings, grades its own research, and writes a professional, recommendation-ready
        investment memo in under a minute.
    </div>
    <div class="hero-chips">
        <span class="chip">🔗 LangGraph</span>
        <span class="chip">📄 RAG</span>
        <span class="chip">⚖️ LLM-as-Judge</span>
        <span class="chip">👤 Human-in-the-Loop</span>
        <span class="chip">🔄 Self-Corrective</span>
    </div>
</div>
<div class="tape"><div class="tape-track">{_tape_html}</div></div>
</div>
""", unsafe_allow_html=True)

# ── Input row ─────────────────────────────────────────────────────
st.markdown('<div class="lbl">Stock Ticker</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([2, 1.2, 3.8])
with c1:
    ticker_input = st.text_input(
        "Ticker", value="AAPL", placeholder="AAPL · TSLA · MSFT · NVDA",
        label_visibility="collapsed",
    )
with c2:
    run_btn = st.button("▶  Research", type="primary", use_container_width=True)
with c3:
    st.markdown(
        '<div style="padding-top:8px;color:#94a3b8;font-size:.84rem;">'
        'Try: AAPL · TSLA · MSFT · NVDA · GOOGL · AMZN</div>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════
#  PHASE A — run button clicked, stream pipeline
# ════════════════════════════════════════════════════════════════════
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

    st.markdown("<div style='margin:.6rem 0 1rem;'></div>", unsafe_allow_html=True)
    left, right = st.columns([1, 1.7])

    with left:
        st.markdown('<div class="lbl">Pipeline Progress</div>', unsafe_allow_html=True)
        slots = {k: st.empty() for k in _META}
        for k, (icon, name) in _META.items():
            slots[k].markdown(_node_card("waiting", icon, name, "waiting…"), unsafe_allow_html=True)
        st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
        mc1, mc2 = st.columns(2)
        m_iter  = mc1.empty()
        m_score = mc2.empty()
        m_iter.markdown(_kpi_tile("Iterations", "—"), unsafe_allow_html=True)
        m_score.markdown(_kpi_tile("Score", "—"), unsafe_allow_html=True)

    with right:
        st.markdown('<div class="lbl">Investment Memo</div>', unsafe_allow_html=True)
        right_area = st.empty()
        right_area.info("Pipeline is running… the memo will appear here after the human-review step.")

    def _set_next_running(node_name: str, updates: dict):
        nxt = {"planner": "search", "search": "rag", "rag": "critic",
               "query_transform": "search"}.get(node_name)
        if node_name == "critic":
            score = updates.get("score", 0)
            done  = score >= 7.0 or len(ss.iter_scores) >= 3
            nxt   = "writer" if done else "query_transform"
        if nxt and nxt in slots:
            icon, name = _META[nxt]
            slots[nxt].markdown(_node_card("running", icon, name, "running…"), unsafe_allow_html=True)

    # Mark Planner as running before stream starts
    slots["planner"].markdown(
        _node_card("running", *_META["planner"], "generating queries…"), unsafe_allow_html=True
    )

    try:
        for step in graph_hitl.stream(initial_state, thread, stream_mode="updates"):
            for node_name, updates in step.items():
                if node_name not in _META:        # skip __interrupt__ & internal nodes
                    continue
                html = _node_html(node_name, updates)
                if node_name in slots:
                    slots[node_name].markdown(html, unsafe_allow_html=True)
                ss.node_texts[node_name] = html
                if node_name == "search":
                    m_iter.markdown(_kpi_tile("Iterations", updates.get("iteration", 1)), unsafe_allow_html=True)
                elif node_name == "critic":
                    m_score.markdown(_score_gauge(updates.get("score", 0)), unsafe_allow_html=True)
                _set_next_running(node_name, updates)
    except Exception as e:
        _show_api_error(e)
        ss.phase = "idle"
        st.stop()

    with left:
        st.markdown("<div style='margin-top:.6rem;'></div>", unsafe_allow_html=True)
        _score_chart(ss.iter_scores, ticker)

    snapshot   = graph_hitl.get_state(thread)
    ss.score   = snapshot.values.get("score", 0)
    ss.missing = snapshot.values.get("missing_topics", [])
    ss.phase   = "paused" if snapshot.next else "done"


# ════════════════════════════════════════════════════════════════════
#  PHASE B — persistent results display
# ════════════════════════════════════════════════════════════════════
elif ss.phase in ["paused", "done"] and ss.node_texts:
    st.markdown("<div style='margin:.6rem 0 1rem;'></div>", unsafe_allow_html=True)
    left, right = st.columns([1, 1.7])

    with left:
        st.markdown('<div class="lbl">Pipeline Progress</div>', unsafe_allow_html=True)
        for html in ss.node_texts.values():
            st.markdown(html, unsafe_allow_html=True)
        if ss.iter_scores:
            st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
            mc1, mc2 = st.columns(2)
            mc1.markdown(_kpi_tile("Iterations", len(ss.iter_scores)), unsafe_allow_html=True)
            mc2.markdown(_kpi_tile("Final Score", f"{ss.score}/10"), unsafe_allow_html=True)
            st.markdown("<div style='margin-top:.4rem;'></div>", unsafe_allow_html=True)
            _score_chart(ss.iter_scores, ss.ticker)

    with right:
        st.markdown('<div class="lbl">Investment Memo</div>', unsafe_allow_html=True)
        if ss.memo:
            st.markdown(_memo_card(ss.ticker, ss.memo), unsafe_allow_html=True)
            st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
            st.download_button(
                "⬇️  Download Memo (.txt)", ss.memo,
                file_name=f"{ss.ticker}_memo.txt", mime="text/plain",
            )
        else:
            st.info("Memo will appear here after generation.")


# ════════════════════════════════════════════════════════════════════
#  HITL SECTION
# ════════════════════════════════════════════════════════════════════
if ss.phase == "paused":
    st.markdown("""
    <div class="surface-card" style="background:linear-gradient(120deg,#fff8e1,#fffdf5);
                border:1.5px solid #f59e0b;border-radius:18px;
                padding:1.4rem 1.7rem 0.9rem;margin-top:1rem;box-shadow:var(--shadow-md);">
        <div style="font-family:Sora;font-size:1.08rem;font-weight:800;color:#b45309;margin-bottom:.3rem;">
            ⏸️ Human-in-the-Loop — Paused Before Writer
        </div>
        <div style="font-size:.88rem;color:#92740b;line-height:1.55;">
            Research is complete. Review the score and gaps, optionally steer the memo with analyst
            instructions, then click <b>Generate Memo</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.9rem;'></div>", unsafe_allow_html=True)
    hc1, hc2 = st.columns([1, 2])
    with hc1:
        st.markdown(_score_gauge(ss.score), unsafe_allow_html=True)
    with hc2:
        if ss.missing:
            st.markdown('<div class="lbl" style="margin-bottom:.4rem;">Gaps identified by Critic</div>', unsafe_allow_html=True)
            for m in ss.missing[:5]:
                st.markdown(
                    f'<div style="font-size:.84rem;color:#475569;padding:5px 0;border-bottom:1px solid var(--line-2);">'
                    f'<span style="color:var(--warn);">•</span> {m}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<div style="font-size:.86rem;color:#64748b;padding-top:.4rem;">No gaps flagged — research is comprehensive.</div>', unsafe_allow_html=True)

    st.markdown('<div class="lbl" style="margin:.9rem 0 .3rem;">Analyst Instructions for the Writer <span style="font-weight:500;color:#94a3b8;text-transform:none;letter-spacing:0;">(optional)</span></div>', unsafe_allow_html=True)
    feedback = st.text_area(
        "instructions",
        placeholder=(
            "Examples:\n"
            "• Focus on downside risks and regulatory threats\n"
            "• Write from a long-term (5-year) investor perspective\n"
            "• Give a clear Buy / Hold / Sell recommendation\n"
            "• Compare performance vs Microsoft and Google"
        ),
        key="hitl_feedback", height=110, label_visibility="collapsed",
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

        st.markdown('<div class="lbl">✍️ Generating memo…</div>', unsafe_allow_html=True)
        memo_live = st.empty()
        memo_live.markdown(
            '<div style="color:#94a3b8;font-size:.88em;font-style:italic;">'
            '<span class="spinner"></span>Writing…</div>',
            unsafe_allow_html=True,
        )
        ss.node_texts["writer"] = _node_card("running", *_META["writer"], "writing memo…")

        try:
            for step in graph_hitl.stream(None, thread, stream_mode="updates"):
                for node_name, updates in step.items():
                    if node_name not in _META:
                        continue
                    html = _node_html(node_name, updates)
                    ss.node_texts[node_name] = html
                    if node_name == "writer":
                        memo_live.markdown(ss.memo)
        except Exception as e:
            _show_api_error(e)
            ss.phase = "idle"
            st.stop()

        ss.phase = "done"
        st.rerun()


# ════════════════════════════════════════════════════════════════════
#  IDLE STATE
# ════════════════════════════════════════════════════════════════════
if ss.phase == "idle":
    st.markdown("""
    <div class="surface-card" style="background:#fff;border-radius:18px;padding:2.6rem 2.5rem;
                border:1px solid var(--line);box-shadow:var(--shadow-md);text-align:center;margin-top:1rem;">
        <div style="font-size:2.8rem;margin-bottom:.6rem;animation:floaty 3s ease-in-out infinite;">📈</div>
        <div style="font-family:Sora;font-weight:800;color:var(--navy-800);font-size:1.25rem;margin-bottom:.4rem;">
            Ready to research
        </div>
        <div style="color:#64748b;font-size:.94rem;line-height:1.65;max-width:520px;margin:0 auto;">
            Enter a stock ticker above and click <b>Research</b>. The pipeline searches the web,
            retrieves earnings data, grades its own quality, and writes a professional memo.
        </div>
        <div style="margin-top:1.4rem;display:flex;justify-content:center;gap:.5rem;flex-wrap:wrap;">
            <span class="chip" style="color:#1e3a8a;background:#eef2ff;border-color:#e0e7ff;">AAPL</span>
            <span class="chip" style="color:#1e3a8a;background:#eef2ff;border-color:#e0e7ff;">TSLA</span>
            <span class="chip" style="color:#1e3a8a;background:#eef2ff;border-color:#e0e7ff;">MSFT</span>
            <span class="chip" style="color:#1e3a8a;background:#eef2ff;border-color:#e0e7ff;">NVDA</span>
            <span class="chip" style="color:#1e3a8a;background:#eef2ff;border-color:#e0e7ff;">GOOGL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
