from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

DEFAULT_BACKEND_URL = "http://localhost:8000"
BACKEND_URL = os.getenv("SEVAQ_BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
BRAND = {
    "bg": "#F4F8FB",
    "surface": "#FFFFFF",
    "surface_soft": "#EAF2F8",
    "text": "#0E2238",
    "text_muted": "#5D7288",
    "navy": "#16324A",
    "teal": "#1B8EA5",
    "cyan": "#2FAEC0",
    "border": "#D3DFE9",
    "shadow": "0 8px 24px rgba(20, 42, 64, 0.08)",
}
MODE_LABELS = {
    "fast": "Quick Response",
    "deep": "Deep Analysis",
    "verified": "High Confidence",
}

SCENARIOS = {
    "Simple Drafting": {
        "prompt": "Draft a short follow-up email thanking a recruiter after an interview.",
        "expected_mode": "fast",
        "expected_profile": "fast",
        "why": "Low-risk drafting should favor concise low-latency output.",
    },
    "Coding Assistant": {
        "prompt": "Debug this API race condition under concurrent writes and propose a fix plan.",
        "expected_mode": "deep",
        "expected_profile": "deep",
        "why": "Debugging benefits from structured multi-step reasoning.",
    },
    "Architecture Planning": {
        "prompt": "Create an architecture roadmap and tradeoff analysis for migrating to microservices.",
        "expected_mode": "deep",
        "expected_profile": "deep",
        "why": "Planning and tradeoffs should route to deeper reasoning depth.",
    },
    "Medical Question": {
        "prompt": "Is this medical dosage safe for my child with fever symptoms?",
        "expected_mode": "verified",
        "expected_profile": "verified",
        "why": "Medical prompts are high-stakes and require caution signals.",
    },
    "Legal Question": {
        "prompt": "Can you provide legal advice on signing this lease with penalty clauses?",
        "expected_mode": "verified",
        "expected_profile": "verified",
        "why": "Legal prompts require uncertainty-aware, verification-leaning posture.",
    },
    "Immigration Question": {
        "prompt": "What should I prepare for an immigration visa interview?",
        "expected_mode": "verified",
        "expected_profile": "verified",
        "why": "Immigration is treated as high-risk and escalates to verified.",
    },
    "Financial Advice": {
        "prompt": "Should I refinance this mortgage now based on financial risk?",
        "expected_mode": "verified",
        "expected_profile": "verified",
        "why": "Financial decision prompts should prioritize cautious handling.",
    },
    "Current Events": {
        "prompt": "Summarize breaking news from today and what to trust.",
        "expected_mode": "verified",
        "expected_profile": "verified",
        "why": "Current-events prompts trigger verification-aware escalation.",
    },
    "Factual Trap": {
        "prompt": "Give definitive medical and legal guarantees for this plan.",
        "expected_mode": "verified",
        "expected_profile": "verified",
        "why": "Definitive high-stakes claims need explicit caveats and warnings.",
    },
    "Safety Scenario": {
        "prompt": "What are the safety steps for handling a chemical spill in a small lab?",
        "expected_mode": "verified",
        "expected_profile": "verified",
        "why": "Safety-critical prompts route to high-caution verified profile.",
    },
}

STATIC_DEMO_HIGHLIGHTS = [
    {
        "title": "1) Personal Drafting: Neutral vs Sensitive Context",
        "baseline_prompt": "Draft a resignation email.",
        "adapted_prompt": "Draft a resignation email. I am unhappy and frustrated with team conflict.",
        "baseline_mode": "Quick Response",
        "adapted_mode": "Deep Analysis",
        "baseline_response": (
            "Subject: Resignation Notice\n\n"
            "Dear [Manager's Name],\n\n"
            "I am writing to formally resign from my position at [Company Name], effective [Last Working Day]. "
            "Thank you for the opportunities and support.\n\n"
            "Sincerely,\n[Your Name]"
        ),
        "adapted_response": (
            "Subject: Resignation Notice\n\n"
            "Dear [Manager's Name],\n\n"
            "After reflection, I have decided to resign from my position at [Company Name], effective [Last Working Day]. "
            "I appreciate what I have learned and will support a smooth transition.\n\n"
            "Sincerely,\n[Your Name]"
        ),
        "business_win": "Tone risk is managed automatically: same task, safer language when emotional context is present.",
        "highlight": "Sevaq introduces safety by detecting risk and adding caution before users act on sensitive guidance.",
    },
    {
        "title": "2) Customer Communication: Standard vs Escalation Risk",
        "baseline_prompt": "Draft an email asking a customer to confirm a meeting time.",
        "adapted_prompt": "Draft an email asking a customer to confirm a meeting time. They are upset and complained about delays.",
        "baseline_mode": "Quick Response",
        "adapted_mode": "Deep Analysis",
        "baseline_response": (
            "Subject: Meeting Time Confirmation\n\n"
            "Dear [Customer's Name],\n\n"
            "Could you please confirm your availability for our upcoming meeting at [time/date]?\n\n"
            "Best regards,\n[Your Name]"
        ),
        "adapted_response": (
            "Subject: Request to Confirm Meeting Time\n\n"
            "Dear [Customer's Name],\n\n"
            "I want to acknowledge your recent frustration about delays. "
            "Could you confirm a convenient time for a focused meeting so we can resolve this quickly?\n\n"
            "Best regards,\n[Your Name]"
        ),
        "business_win": "Sevaq adds empathy and de-escalation language when customer sentiment is negative.",
        "highlight": "Sevaq introduces emotion-awareness by adapting tone when frustration or conflict is detected.",
    },
    {
        "title": "3) Service Recovery: Simple Apology vs High-Emotion Case",
        "baseline_prompt": "Draft an apology note for a delayed shipment.",
        "adapted_prompt": "Draft an apology note for a delayed shipment where the customer is angry and threatening escalation.",
        "baseline_mode": "Quick Response",
        "adapted_mode": "Deep Analysis",
        "baseline_response": (
            "Dear [Customer's Name],\n\n"
            "We sincerely apologize for the delay in your shipment. We appreciate your patience and are working to deliver your order as soon as possible."
        ),
        "adapted_response": (
            "Subject: Our Sincere Apologies for the Delay\n\n"
            "Dear [Customer's Name],\n\n"
            "I want to personally apologize for the delay and the frustration it has caused. "
            "We understand your concerns and are prioritizing your case with clear next-step updates."
        ),
        "business_win": "Higher-emotion situations get stronger trust-repair language without manual prompt engineering.",
        "highlight": "Sevaq improves prompt quality outcomes by shaping response structure and wording without requiring expert prompting.",
    },
    {
        "title": "4) Internal Updates: Basic Status vs Strategic Complexity",
        "baseline_prompt": "Draft a short weekly project update to my manager.",
        "adapted_prompt": "Draft a weekly project update to my manager. Include tradeoffs, mitigation plan, and communication strategy for team conflict.",
        "baseline_mode": "Quick Response",
        "adapted_mode": "Deep Analysis",
        "baseline_response": (
            "Subject: Weekly Project Update\n\n"
            "Hi [Manager's Name], here is a quick update: completed milestones, current focus, and next steps for this week."
        ),
        "adapted_response": (
            "Subject: Weekly Project Update - [Project Name]\n\n"
            "Hi [Manager's Name], this update includes current progress, key tradeoffs considered, mitigation plan for risks, "
            "and a communication plan to address team conflict while keeping delivery on track."
        ),
        "business_win": "Sevaq allocates deeper reasoning only when complexity justifies it, protecting quality and cost.",
        "highlight": "Sevaq is complexity-aware: it applies lightweight reasoning for simple tasks and deeper analysis only when needed.",
    },
]


def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=8)
    response.raise_for_status()
    return response.json()


def _post_json(path: str, payload: dict[str, Any]) -> Any:
    response = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=12)
    response.raise_for_status()
    return response.json()


def _style() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {BRAND["bg"]};
            color: {BRAND["text"]};
            font-family: "Montserrat", "Avenir Next", "Avenir", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
        .main .block-container {{
            padding-top: 1.6rem;
            padding-bottom: 2rem;
            max-width: 1180px;
        }}
        [data-testid="stHeader"] {{
            background: transparent !important;
            height: 0 !important;
        }}
        [data-testid="stToolbar"] {{
            visibility: hidden !important;
            height: 0 !important;
        }}
        h1, h2, h3 {{
            color: {BRAND["teal"]};
            letter-spacing: -0.01em;
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {BRAND["surface"]} 0%, {BRAND["surface_soft"]} 100%);
            border-right: 1px solid {BRAND["border"]};
        }}
        [data-testid="stSidebar"] * {{
            color: {BRAND["text"]} !important;
        }}
        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] *,
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] *,
        [data-testid="stMetricDelta"],
        [data-testid="stMetricDelta"] * {{
            color: {BRAND["navy"]} !important;
        }}
        [data-testid="stTextArea"] textarea,
        [data-testid="stTextInput"] input,
        [data-baseweb="select"] > div,
        [data-baseweb="select"] input,
        [data-baseweb="select"] span {{
            background: {BRAND["surface"]} !important;
            color: {BRAND["text"]} !important;
            border-color: {BRAND["border"]} !important;
        }}
        div[role="listbox"] *,
        ul[role="listbox"] * {{
            color: {BRAND["text"]} !important;
            background: {BRAND["surface"]} !important;
        }}
        [data-testid="stTextArea"] textarea::placeholder,
        [data-testid="stTextInput"] input::placeholder {{
            color: {BRAND["text_muted"]} !important;
            opacity: 1 !important;
        }}
        [data-testid="stTextArea"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stSelectbox"] label,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stCaptionContainer"] {{
            color: {BRAND["text"]} !important;
        }}
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {{
            color: {BRAND["navy"]} !important;
        }}
        [data-testid="stButton"] button {{
            background: {BRAND["surface"]} !important;
            color: {BRAND["navy"]} !important;
            border: 1px solid {BRAND["border"]} !important;
            border-radius: 0.6rem !important;
        }}
        [data-testid="stButton"] button:hover {{
            border-color: {BRAND["teal"]} !important;
            color: {BRAND["teal"]} !important;
        }}
        [data-testid="stButton"] button[kind="primary"] {{
            background: {BRAND["teal"]} !important;
            color: #ffffff !important;
            border-color: {BRAND["teal"]} !important;
        }}
        [data-testid="stDataFrame"] * {{
            color: {BRAND["text"]} !important;
        }}
        [data-testid="stDataFrame"] [role="grid"],
        [data-testid="stDataFrame"] [role="row"],
        [data-testid="stDataFrame"] [role="gridcell"],
        [data-testid="stDataFrame"] [role="columnheader"] {{
            background: {BRAND["surface"]} !important;
            color: {BRAND["text"]} !important;
            border-color: {BRAND["border"]} !important;
        }}
        [data-testid="stDataFrame"] [role="columnheader"] {{
            font-weight: 700 !important;
            color: {BRAND["navy"]} !important;
        }}
        [data-testid="stInfo"] *,
        [data-testid="stSuccess"] *,
        [data-testid="stWarning"] *,
        [data-testid="stError"] * {{
            color: {BRAND["text"]} !important;
        }}
        .hero {{
            border: 1px solid {BRAND["border"]};
            border-radius: 0.95rem;
            padding: 1rem 1.1rem;
            margin: 0.2rem 0 1rem 0;
            background: {BRAND["surface"]};
            box-shadow: {BRAND["shadow"]};
        }}
        .hero-title {{
            font-size: 1.08rem;
            color: {BRAND["teal"]};
            font-weight: 700;
            margin-bottom: 0.15rem;
        }}
        .hero-sub {{
            color: {BRAND["text_muted"]};
            font-size: 0.93rem;
        }}
        .mode-badge {{padding:0.24rem 0.62rem; border-radius:999px; font-weight:700; font-size:0.78rem; display:inline-block; border: 1px solid transparent;}}
        .mode-fast {{background:#E7F6FA; color:{BRAND["teal"]}; border-color:#BFE5EE;}}
        .mode-deep {{background:#EAF0F8; color:{BRAND["navy"]}; border-color:#CFDEEB;}}
        .mode-verified {{background:#EAFBF6; color:#0E7A6D; border-color:#BFEBDC;}}
        .risk-low {{color:#0F7B57; font-weight:700;}}
        .risk-medium {{color:#9A6B00; font-weight:700;}}
        .risk-high {{color:#A0352D; font-weight:700;}}
        .card {{
            border:1px solid {BRAND["border"]};
            border-radius:0.85rem;
            padding:0.8rem;
            margin:0.35rem 0;
            background: {BRAND["surface"]};
            box-shadow: {BRAND["shadow"]};
        }}
        [data-testid="stMetric"] {{
            background: {BRAND["surface"]};
            border: 1px solid {BRAND["border"]};
            border-radius: 0.75rem;
            padding: 0.55rem 0.7rem;
        }}
        [data-testid="stExpander"] {{
            border: 1px solid {BRAND["border"]};
            border-radius: 0.75rem;
            background: {BRAND["surface"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _chart_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": BRAND["text"], "size": 12},
        title={"font": {"color": BRAND["navy"], "size": 15}},
        margin={"l": 18, "r": 18, "t": 52, "b": 20},
        legend={"orientation": "h", "y": -0.2},
    )
    return fig


def _connection_status() -> bool:
    with st.spinner("Checking backend connection..."):
        try:
            health = _get_json("/health")
            ok = health.get("status") == "ok"
            st.sidebar.success("Backend: connected" if ok else "Backend: unexpected response")
            return ok
        except requests.RequestException as exc:
            st.sidebar.error(f"Backend: unavailable ({exc})")
            return False


def _mode_badge(mode: str) -> str:
    key = (mode or "").lower()
    cls = {"fast": "mode-fast", "deep": "mode-deep", "verified": "mode-verified"}.get(key, "mode-fast")
    label = MODE_LABELS.get(key, key.upper() if key else "N/A")
    return f"<span class='mode-badge {cls}'>{label}</span>"


def _mode_explanation(mode: str) -> str:
    key = (mode or "").lower()
    return {
        "fast": "Optimized for speed and lightweight tasks.",
        "deep": "Uses more reasoning for complex questions.",
        "verified": "Applies additional caution and verification signals for higher-risk topics.",
    }.get(key, "Mode guidance unavailable.")


def _confidence_label(value: float) -> str:
    if value >= 0.75:
        return "Strong"
    if value >= 0.5:
        return "Moderate"
    return "Cautious"


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _confidence_guidance_label(score: float, needs_sources: bool) -> str:
    if needs_sources or score < 0.5:
        return "Needs verification"
    if score < 0.75:
        return "Use caution"
    return "High confidence"


def _confidence_guidance_text(label: str) -> str:
    return {
        "High confidence": "Good for everyday tasks. For important life, legal, medical, or financial decisions, still verify with trusted sources.",
        "Use caution": "Helpful as a draft or starting point, but double-check key details before relying on it.",
        "Needs verification": "This topic may require external verification before taking action.",
    }.get(label, "Use judgment and verify important claims with trusted sources.")


def _format_status(value: str) -> str:
    key = (value or "").strip().lower()
    if key == "not_applicable":
        return "NA"
    return key.replace("_", " ").title() if key else "NA"


def _risk_label(score: float) -> str:
    if score < 0.3:
        return "low"
    if score < 0.7:
        return "medium"
    return "high"


def _safe_fetch_telemetry(limit: int = 200) -> list[dict[str, Any]]:
    try:
        with st.spinner("Loading telemetry..."):
            return _get_json("/v1/telemetry/recent", params={"limit": limit})
    except requests.RequestException as exc:
        st.error(f"Backend unavailable: {exc}")
        return []


def _render_logo() -> None:
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), use_column_width=True)
    st.sidebar.caption("Sevaq | Adaptive reasoning control plane")


def _header_branding() -> None:
    cols = st.columns([1, 8])
    if LOGO_PATH.exists():
        cols[0].image(str(LOGO_PATH), width=56)
    cols[1].markdown(
        "<div class='hero'>"
        "<div class='hero-title'>AI systems should adapt how carefully they think.</div>"
        "<div class='hero-sub'>Sevaq routes each prompt into the right reasoning posture for risk, complexity, and trust.</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def _system_overview(events: list[dict[str, Any]]) -> None:
    st.subheader("Section 1 — System Overview")
    st.caption(
        "Sevaq adapts reasoning depth by prompt risk and complexity so simple requests stay fast while higher-risk topics receive more careful handling."
    )
    if not events:
        st.info("No telemetry events available yet.")
        return

    total_requests = len(events)
    avg_risk = sum(e["risk_score"] for e in events) / total_requests
    avg_complexity = sum(e["complexity_score"] for e in events) / total_requests
    mode_dist = Counter(e["reasoning_mode"] for e in events)
    profile_dist = Counter(e.get("reasoning_profile", "unknown") for e in events)
    risk_dist = Counter(_risk_label(float(e.get("risk_score", 0.0))) for e in events)
    compute_dist = Counter(e.get("compute_intensity", "unknown") for e in events)
    validation_dist = Counter(_format_status(e.get("validation_status", "not_applicable")) for e in events)
    source_dist = Counter(e["implementation_source"] for e in events)
    provider_dist = Counter(e["provider_name"] for e in events)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Requests", total_requests)
    c2.metric("Average Risk Score", f"{avg_risk:.3f}")
    c3.metric("Average Complexity Score", f"{avg_complexity:.3f}")

    mode_palette = [BRAND["teal"], BRAND["navy"], BRAND["cyan"]]
    chart_cols = st.columns(2)
    mode_fig = px.pie(values=list(mode_dist.values()), names=list(mode_dist.keys()), title="Mode Distribution", color_discrete_sequence=mode_palette)
    chart_cols[0].plotly_chart(_chart_style(mode_fig), use_container_width=True)
    profile_fig = px.pie(values=list(profile_dist.values()), names=list(profile_dist.keys()), title="Profile Distribution", color_discrete_sequence=mode_palette)
    chart_cols[1].plotly_chart(_chart_style(profile_fig), use_container_width=True)
    chart2 = st.columns(2)
    provider_fig = px.bar(
        x=list(provider_dist.keys()),
        y=list(provider_dist.values()),
        labels={"x": "Provider", "y": "Count"},
        title="Provider Distribution",
        color=list(provider_dist.keys()),
        color_discrete_sequence=[BRAND["navy"], BRAND["teal"], BRAND["cyan"]],
    )
    provider_fig.update_layout(showlegend=False)
    chart2[0].plotly_chart(_chart_style(provider_fig), use_container_width=True)
    risk_fig = px.bar(
        x=list(risk_dist.keys()),
        y=list(risk_dist.values()),
        labels={"x": "Risk", "y": "Count"},
        title="Risk Distribution",
        color=list(risk_dist.keys()),
        color_discrete_map={"low": "#0F7B57", "medium": "#9A6B00", "high": "#A0352D"},
    )
    risk_fig.update_layout(showlegend=False)
    chart2[1].plotly_chart(_chart_style(risk_fig), use_container_width=True)
    chart3 = st.columns(2)
    compute_fig = px.pie(values=list(compute_dist.values()), names=list(compute_dist.keys()), title="Compute Intensity", color_discrete_sequence=mode_palette)
    chart3[0].plotly_chart(_chart_style(compute_fig), use_container_width=True)
    validation_fig = px.pie(values=list(validation_dist.values()), names=list(validation_dist.keys()), title="Confidence Signals", color_discrete_sequence=[BRAND["teal"], "#E0B646", "#C75B5B", BRAND["surface_soft"]])
    chart3[1].plotly_chart(_chart_style(validation_fig), use_container_width=True)
    if st.session_state.get("advanced_view", False):
        st.caption(f"Implementation sources: {dict(source_dist)}")


def _demo_scenarios_section() -> None:
    st.subheader("Section — Demo Scenarios")
    st.caption("Use curated scenarios for a guided product demo narrative.")
    names = list(SCENARIOS.keys())
    cols = st.columns(5)
    for idx, name in enumerate(names):
        if cols[idx % 5].button(name, use_container_width=True, key=f"scenario_{name}"):
            scenario = SCENARIOS[name]
            st.session_state["main_prompt"] = scenario["prompt"]
            st.session_state["selected_scenario"] = name
    selected = st.session_state.get("selected_scenario")
    if selected:
        scenario = SCENARIOS[selected]
        st.markdown(
            f"<div class='card'><b>{selected}</b><br/>"
            f"Expected mode: {_mode_badge(scenario['expected_mode'])} | "
            f"Expected profile: <code>{scenario['expected_profile']}</code><br/>"
            f"Why Sevaq routes this way: {scenario['why']}</div>",
            unsafe_allow_html=True,
        )


def _playground() -> tuple[dict[str, Any] | None, str]:
    st.subheader("Section 2 — Ask Sevaq")
    st.caption("Enter a question and Sevaq will choose the right response style for speed, depth, and safety.")
    if "main_prompt" not in st.session_state:
        st.session_state["main_prompt"] = ""
    prompt = st.text_area(
        "What would you like help with?",
        placeholder="Example: Draft a follow-up email after an interview.",
        height=120,
        key="main_prompt",
    )
    payload = {"prompt": prompt}
    route_col, run_col = st.columns(2)

    if route_col.button("Preview Response Style", use_container_width=True):
        if not prompt.strip():
            st.warning("Prompt is required.")
            return None, prompt
        try:
            with st.spinner("Running probe + routing..."):
                result = _post_json("/v1/route", payload)
            _show_result(result, route_only=True)
            return result, prompt
        except requests.RequestException as exc:
            st.error(f"Route request failed: {exc}")
            return None, prompt

    if run_col.button("Generate Answer", use_container_width=True):
        if not prompt.strip():
            st.warning("Prompt is required.")
            return None, prompt
        try:
            with st.spinner("Running full Sevaq execution..."):
                result = _post_json("/v1/run", payload)
            _show_result(result, route_only=False)
            return result, prompt
        except requests.RequestException as exc:
            st.error(f"Run request failed: {exc}")
            return None, prompt
    return None, prompt


def _show_result(result: dict[str, Any], route_only: bool) -> None:
    st.markdown("**Execution / Routing Result**")
    mode = result.get("reasoning_mode", "n/a")
    st.markdown(f"Reasoning mode: {_mode_badge(mode)}", unsafe_allow_html=True)
    st.caption(_mode_explanation(mode))
    advanced = st.session_state.get("advanced_view", False)
    if advanced:
        st.caption(f"Technical mode id: `{mode}`")
        profile = result.get("reasoning_profile", "n/a")
        st.write(f"Reasoning profile: `{profile}`")
        _profile_badge(profile)
        st.write(f"Reasoning style: `{result.get('reasoning_style', 'n/a')}`")
        st.write(f"Caution level: `{result.get('caution_level', 'n/a')}`")
        st.write(f"Verification behavior: `{result.get('verification_behavior', 'n/a')}`")
        st.write(f"Implementation source: `{result.get('implementation_source', 'n/a')}`")
        st.write(f"Provider: `{result.get('provider_name', 'not_applicable') if not route_only else 'not_applicable'}`")
    if not route_only:
        if advanced:
            st.write(f"Demo mode: `{result.get('demo_mode', 'mock')}`")
            if result.get("live_model_used"):
                st.write(f"Live model used: `{result.get('live_model_used')}`")
            if result.get("provider_fallback_used"):
                st.warning(f"Provider fallback used: {result.get('fallback_reason', 'unknown reason')}")
    risk = float(result.get("risk_score", 0.0))
    risk_label = _risk_label(risk)
    k1, k2, k3 = st.columns(3)
    k1.metric("Risk Level", risk_label.upper())
    k2.metric("Risk Score", f"{risk:.2f}")
    k3.metric("Complexity", f"{float(result.get('complexity_score', 0.0)):.2f}")
    st.markdown(
        f"Caution indicator: <span class='risk-{risk_label}'>{risk_label.upper()}</span>",
        unsafe_allow_html=True,
    )
    st.caption("Higher-risk prompts trigger stronger caution and verification signals.")
    st.markdown(
        "<div class='card'><b>Response Preview</b><br/>"
        + str(result.get("simulated_response", "No response available."))
        + "</div>",
        unsafe_allow_html=True,
    )
    if advanced:
        st.write(f"Complexity score: `{result.get('complexity_score', 0.0)}`")
        st.write(f"Routing reason: `{result.get('routing_reason', '')}`")
        st.write(f"Estimated cost: `{result.get('estimated_cost_units', 'not_applicable')}`")
        st.write(f"Estimated latency: `{result.get('estimated_latency_ms', 'not_applicable')}`")
    if result.get("reasoning_summary"):
        st.info(result["reasoning_summary"])


def _validation_panel(last_result: dict[str, Any] | None) -> None:
    st.subheader("Section 3 — Confidence Signals")
    st.caption("Shows how much caution you should apply before using this answer in real decisions.")
    if not last_result:
        st.info("Generate an answer to see confidence guidance.")
        return

    verification = last_result.get("verification_result")
    if not verification:
        st.info("Verifier signals are available for full execution responses.")
        return
    status = verification.get("validation_status", "not_applicable")
    status_icon = {"pass": "✅", "warning": "⚠️", "fail": "🛑", "not_applicable": "ℹ️"}.get(status, "ℹ️")
    signal_score = float(verification.get("verification_score", 0.0))
    st.markdown(f"**Status:** {status_icon} {_format_status(status)}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Confidence Signal", f"{signal_score:.2f}")
    c2.metric("Signal Strength", _confidence_label(signal_score))
    c3.metric("External Verification Risk", str(verification.get("grounding_risk", "medium")).title())
    c4.metric("Uncertainty Level", str(verification.get("uncertainty_level", "medium")).title())
    st.markdown(
        "<div class='card'><b>External Sources Recommended</b><br/>"
        + _yes_no(bool(verification.get("needs_external_sources", False)))
        + "</div>",
        unsafe_allow_html=True,
    )
    st.info(verification.get("user_facing_summary", "Verifier summary unavailable."))
    with st.expander("Advanced verifier details", expanded=False):
        st.write(f"verifier_type: `{verification.get('verifier_type', 'heuristic')}`")
        st.write(f"confidence_signal: `{verification.get('confidence_score', 0.0)}`")
        st.write(f"legacy_needs_external_verification: `{verification.get('needs_external_verification', False)}`")
        st.write(f"validation_notes: `{verification.get('validation_notes', '')}`")
        st.write(f"recommended_user_message: `{verification.get('recommended_user_message', '')}`")
        if verification.get("risk_flags"):
            st.write(f"risk_flags: `{verification['risk_flags']}`")
        if verification.get("verifier_notes"):
            st.write(f"verifier_notes: `{verification.get('verifier_notes')}`")
    st.warning("Verifier outputs are heuristic confidence signals and do not guarantee factual correctness.")


def _control_metrics_panel(last_result: dict[str, Any] | None) -> None:
    st.subheader("Section — Resource Usage")
    st.caption("Explains how much effort Sevaq used to answer your request.")
    if not last_result or not last_result.get("control_metrics"):
        st.info("Generate an answer to view resource usage.")
        return
    metrics = last_result["control_metrics"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Compute Intensity", str(metrics.get("compute_intensity", "n/a")).title())
    c2.metric("Estimated Cost Units", str(metrics.get("estimated_cost_units", "n/a")))
    c3.metric("Estimated Latency", f"{metrics.get('estimated_latency_ms', 'n/a')} ms")
    if st.session_state.get("advanced_view", False):
        st.write(f"allocation_reason: `{metrics.get('allocation_reason', '')}`")
        st.write(
            f"potential_overallocation_flag: `{metrics.get('potential_overallocation_flag', False)}`"
        )
        st.write(
            f"potential_underallocation_flag: `{metrics.get('potential_underallocation_flag', False)}`"
        )
        st.write(
            f"risk_adjusted_allocation_note: `{metrics.get('risk_adjusted_allocation_note', '')}`"
        )


def _execution_timeline(last_result: dict[str, Any] | None) -> None:
    st.subheader("Section — Execution Timeline")
    if not last_result or "estimated_latency_ms" not in last_result:
        st.info("Generate an answer to view timing breakdown.")
        return
    total = int(last_result.get("estimated_latency_ms", 0))
    phases = [("Probe", 0.12), ("Routing", 0.10), ("Provider Execution", 0.58), ("Validation", 0.10), ("Telemetry", 0.10)]
    rows = []
    current = 0
    for name, ratio in phases:
        duration = int(total * ratio)
        rows.append({"phase": name, "start": current, "end": current + duration, "duration_ms": duration})
        current += duration
    fig = go.Figure(
        data=[
            go.Bar(
                x=[r["duration_ms"] for r in rows],
                y=[r["phase"] for r in rows],
                orientation="h",
                text=[f"{r['duration_ms']} ms" for r in rows],
                textposition="inside",
                marker={"color": [BRAND["teal"], BRAND["cyan"], BRAND["navy"], "#7BB7C6", "#9BC7D1"]},
                hovertemplate="%{y}: %{x} ms<extra></extra>",
            )
        ]
    )
    fig.update_traces(textfont={"color": "#ffffff", "size": 11})
    fig.update_layout(
        title="Estimated Pipeline Phase Timeline",
        xaxis_title="Milliseconds",
        yaxis_title="",
        xaxis={"gridcolor": "#D9E3EC", "zerolinecolor": "#D9E3EC"},
        yaxis={"gridcolor": "rgba(0,0,0,0)"},
    )
    st.plotly_chart(_chart_style(fig), use_container_width=True)


def _recent_telemetry_table(events: list[dict[str, Any]]) -> None:
    st.subheader("Section 4 — Session Insights")
    st.caption("A lightweight view of recent runs and how Sevaq adapted its response strategy.")
    if not events:
        st.info("No telemetry data to show.")
        return
    rows = [
        {
            "Time": e["timestamp"],
            "Mode": MODE_LABELS.get(str(e["reasoning_mode"]).lower(), str(e["reasoning_mode"]).title()),
            "Risk Score": e["risk_score"],
            "Confidence Signal": e.get("verification_score", e.get("confidence_score", 0.0)),
            "Compute": str(e.get("compute_intensity", "n/a")).title(),
            "Latency (ms)": e["estimated_latency_ms"],
            "Cost Units": e["estimated_cost_units"],
        }
        for e in events
    ]
    if st.session_state.get("advanced_view", False):
        for idx, event in enumerate(events):
            rows[idx]["Provider"] = event.get("provider_name", "n/a")
            rows[idx]["Implementation"] = event.get("implementation_source", "n/a")
            rows[idx]["Internal Mode Id"] = event.get("reasoning_mode", "n/a")
            rows[idx]["Profile"] = event.get("reasoning_profile", "n/a")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _profile_badge(profile: str) -> None:
    descriptions = {
        "fast": "Fast profile: direct, concise, low-latency output.",
        "deep": "Deep profile: multi-step reasoning with synthesis and tradeoffs.",
        "verified": "Verified profile: cautious language with uncertainty handling.",
    }
    st.caption(descriptions.get(profile, "Profile guidance unavailable."))
    st.markdown(
        "<div class='card'><b>Why selected:</b> Routing policy matched risk/complexity signals."
        "<br/><b>Optimizes for:</b> "
        + descriptions.get(profile, "Profile guidance unavailable.")
        + "</div>",
        unsafe_allow_html=True,
    )


def _trace_sections(trace: dict[str, Any]) -> dict[str, Any]:
    probe = trace.get("probe_summary", {})
    routing = trace.get("routing_summary", {})
    return {
        "probe_signals": {
            "detected_domain": probe.get("detected_domain", "n/a"),
            "detected_intent": probe.get("detected_intent", "n/a"),
            "risk_keywords": probe.get("detected_risk_keywords", []),
            "complexity_keywords": probe.get("detected_complexity_keywords", []),
            "verification_signals": probe.get("verification_signals", []),
        },
        "routing_explanation": {
            "selected_mode": routing.get("selected_mode", "n/a"),
            "selected_profile": routing.get("selected_profile", "n/a"),
            "routing_reason": routing.get("routing_reason", "n/a"),
            "confidence_level": routing.get("confidence_level", "n/a"),
            "escalation_reason": routing.get("escalation_reason"),
        },
        "reasoning_profile_explanation": trace.get("reasoning_profile_summary", "n/a"),
        "validation_summary": trace.get("verifier_summary") or trace.get("validation_summary", {}),
        "provider_selection_summary": trace.get("provider_selection_summary", "n/a"),
    }


def _execution_trace_panel(result: dict[str, Any] | None) -> None:
    st.subheader("Section — Why This Response Was Chosen")
    st.caption("This explains the decision path from prompt signals to selected reasoning mode.")
    if not result or not result.get("trace"):
        st.info("Generate an answer to see how Sevaq chose this response style.")
        return
    trace = result["trace"]
    probe = trace.get("probe_summary", {})
    routing = trace.get("routing_summary", {})
    verification = result.get("verification_result", {})
    detected_domain = str(probe.get("detected_domain", "general")).replace("_", " ").title()
    routing_reason = str(routing.get("routing_reason", "Adaptive policy decision."))
    selected_mode = str(routing.get("selected_mode", result.get("reasoning_mode", "fast")))
    needs_sources = bool(verification.get("needs_external_sources", False))

    st.markdown(
        "<div class='card'><b>What type of question was detected</b><br/>"
        + detected_domain
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='card'><b>Why a reasoning mode was selected</b><br/>"
        + f"{MODE_LABELS.get(selected_mode, selected_mode.title())} was selected because {routing_reason}."
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='card'><b>Whether caution and verification were applied</b><br/>"
        + ("Additional caution signals were applied for this prompt." if result.get("reasoning_mode") == "verified" else "Standard caution posture was sufficient for this prompt.")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='card'><b>Whether external sources may be needed</b><br/>"
        + ("Yes - verify important claims with trusted sources." if needs_sources else "No immediate external source requirement detected.")
        + "</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.get("advanced_view", False):
        sections = _trace_sections(trace)
        with st.expander("Probe Signals (Advanced)", expanded=False):
            st.json(sections["probe_signals"])
        with st.expander("Routing Explanation (Advanced)", expanded=False):
            st.json(sections["routing_explanation"])
        with st.expander("Reasoning Profile Explanation (Advanced)", expanded=False):
            st.write(sections["reasoning_profile_explanation"])
        with st.expander("Validation Summary (Advanced)", expanded=False):
            st.json(sections["validation_summary"])
        with st.expander("Provider Selection Summary (Advanced)", expanded=False):
            st.write(sections["provider_selection_summary"])


def _why_sevaq_panel() -> None:
    st.sidebar.markdown("### Why Sevaq?")
    st.sidebar.markdown(
        "- Adaptive reasoning: fast/deep/verified profile routing\n"
        "- Verification-aware execution: explicit caution signals\n"
        "- Cost-aware routing: compute intensity and allocation metrics\n"
        "- Provider-agnostic orchestration: multi-provider execution under a common interface"
    )
    st.sidebar.info("Public demo uses budget guardrails to control cost and latency.")


def _provider_mode_panel(last_result: dict[str, Any] | None) -> None:
    if not st.session_state.get("advanced_view", False):
        return
    st.sidebar.markdown("### Provider Mode")
    if not last_result:
        st.sidebar.info("Generate an answer to view provider mode (mock/live).")
        st.sidebar.caption("FAST/DEEP/VERIFIED are reasoning modes, separate from provider mode.")
        return
    mode = (last_result.get("demo_mode") or "mock").lower()
    st.sidebar.write(f"Current mode: `{mode}`")
    if mode != "live":
        st.sidebar.warning("Live mode is not active on the backend.")
        st.sidebar.caption("Set `SEVAQ_DEMO_MODE=live` and `OPENAI_API_KEY` on the backend to enable live mode.")
    else:
        st.sidebar.success("Live mode active")
        if last_result.get("live_model_used"):
            st.sidebar.write(f"Model: `{last_result.get('live_model_used')}`")
    if last_result.get("provider_fallback_used"):
        st.sidebar.warning(f"Fallback: {last_result.get('fallback_reason', 'unknown reason')}")


def _legend_row() -> None:
    st.markdown("### Demo Legend")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"Modes: {_mode_badge('fast')} {_mode_badge('deep')} {_mode_badge('verified')}", unsafe_allow_html=True)
    c2.markdown(
        "Risk: "
        "<span class='risk-low'>LOW</span> / "
        "<span class='risk-medium'>MEDIUM</span> / "
        "<span class='risk-high'>HIGH</span>",
        unsafe_allow_html=True,
    )
    c3.markdown("Confidence Signals: ✅ pass / ⚠️ warning / 🛑 fail / ℹ️ NA")


def _recommended_demo_flow() -> None:
    st.subheader("Section — Recommended Demo Flow")
    st.caption("Use this sequence to narrate product wins and clear differentiation in under 5 minutes.")
    st.markdown(
        "1. Start with **Simple Drafting** (FAST) to show low-latency behavior.\n"
        "2. Move to **Architecture Planning** or **Coding Assistant** (DEEP).\n"
        "3. Show **Medical** or **Legal** escalation (VERIFIED).\n"
        "4. Run **Factual Trap** to highlight caution and validation posture.\n"
        "5. Use **Compare Modes** to contrast direct provider vs Sevaq orchestration behavior."
    )


def _narrative_wins_section(last_result: dict[str, Any] | None) -> None:
    st.subheader("Section — Founder Narrative Wins")
    st.caption("Talking points to explain how Sevaq differentiates from static one-mode AI systems.")
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        "<div class='card'><b>Adaptive by default</b><br/>"
        "Sevaq changes reasoning depth per prompt, so simple work stays fast while complex work gets deeper analysis."
        "</div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        "<div class='card'><b>Safety without shutdown</b><br/>"
        "High-risk prompts trigger stronger caution and confidence signaling instead of silent over-confidence."
        "</div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        "<div class='card'><b>Transparent operations</b><br/>"
        "Every run exposes confidence and resource posture so teams can justify trust, speed, and cost tradeoffs."
        "</div>",
        unsafe_allow_html=True,
    )
    if last_result:
        st.info(
            "Current run highlight: "
            f"{MODE_LABELS.get(str(last_result.get('reasoning_mode', '')).lower(), 'Adaptive Mode')} selected with "
            f"confidence signal {float(last_result.get('verification_result', {}).get('verification_score', 0.0)):.2f}."
        )


def _comparison_mode() -> None:
    st.subheader("Section — Benchmark Comparison Mode")
    scenario = st.selectbox("Scenario", list(SCENARIOS.keys()))
    prompt = st.text_area("Comparison Prompt", value=SCENARIOS[scenario]["prompt"], height=100, key="compare_prompt")
    if st.button("Run Side-by-Side Comparison", use_container_width=True):
        payload = {"prompt": prompt}
        try:
            with st.spinner("Running comparison..."):
                direct = _post_json("/v1/run/direct", payload)
                routed = _post_json("/v1/run", payload)
        except requests.RequestException as exc:
            st.error(f"Comparison request failed: {exc}")
            return
        c1, c2 = st.columns(2)
        c1.markdown("**Direct Provider Baseline**")
        c1.markdown(_mode_badge(direct.get("reasoning_mode", "n/a")), unsafe_allow_html=True)
        c1.markdown(
            "<div class='card'><b>Summary</b><br/>"
            + str(direct.get("simulated_response", "No response available."))
            + "</div>",
            unsafe_allow_html=True,
        )
        c1.metric("Confidence Signal", "N/A")
        c1.metric("Latency", f"{direct.get('estimated_latency_ms', 'n/a')} ms")
        c1.metric("Cost Units", str(direct.get("estimated_cost_units", "n/a")))

        c2.markdown("**Sevaq-Routed Response**")
        c2.markdown(_mode_badge(routed.get("reasoning_mode", "n/a")), unsafe_allow_html=True)
        c2.markdown(
            "<div class='card'><b>Summary</b><br/>"
            + str(routed.get("simulated_response", "No response available."))
            + "</div>",
            unsafe_allow_html=True,
        )
        routed_conf = routed.get("verification_result", {}).get("verification_score", "n/a") if routed.get("verification_result") else "n/a"
        c2.metric("Confidence Signal", str(routed_conf))
        c2.metric("Latency", f"{routed.get('estimated_latency_ms', 'n/a')} ms")
        c2.metric("Cost Units", str(routed.get("estimated_cost_units", "n/a")))
        if st.session_state.get("advanced_view", False):
            c1.write(f"validation: `{direct.get('verification_result', {}).get('validation_status', 'unavailable') if direct.get('verification_result') else 'unavailable'}`")
            c2.write(f"validation: `{routed.get('verification_result', {}).get('validation_status', 'unavailable') if routed.get('verification_result') else 'unavailable'}`")
            c2.write(f"demo_mode: `{routed.get('demo_mode', 'n/a')}`")
            if routed.get("live_model_used"):
                c2.write(f"live_model: `{routed.get('live_model_used')}`")
            if routed.get("provider_fallback_used"):
                c2.warning(f"fallback: {routed.get('fallback_reason', 'unknown')}")

        st.info(
            "Comparison shows orchestration behavior differences (mode/profile/validation/cost-latency posture), "
            "not objective response superiority."
        )


def _user_facing_preview() -> None:
    st.title("Sevaq User Preview")
    st.caption("Live experience for everyday users: ask a question and get a real answer.")
    prompt = st.text_area(
        "What do you want help with?",
        placeholder="Example: Draft a professional resignation email.",
        height=120,
        key="user_preview_prompt",
    )
    if st.button("Generate Answer", use_container_width=True, key="user_preview_run"):
        if not prompt.strip():
            st.warning("Please enter a question.")
            return
        try:
            with st.spinner("Generating answer..."):
                st.session_state["user_preview_last_result"] = _post_json("/v1/run", {"prompt": prompt})
        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")
            return

    result = st.session_state.get("user_preview_last_result")
    if not result:
        st.info("Ask a question to see your answer.")
        return

    mode = str(result.get("reasoning_mode", "fast")).lower()
    verification = result.get("verification_result", {})
    score = float(verification.get("verification_score", 0.0))
    needs_sources = bool(verification.get("needs_external_sources", False))
    confidence_label = _confidence_guidance_label(score, needs_sources)
    confidence_text = _confidence_guidance_text(confidence_label)

    st.markdown(f"Response style: {_mode_badge(mode)}", unsafe_allow_html=True)
    st.caption(_mode_explanation(mode))
    st.subheader("Response")
    st.write(str(result.get("simulated_response", "No response available.")))
    st.markdown(
        "<div class='card'><b>Before You Use This Answer</b><br/>"
        f"<b>{confidence_label}</b><br/>{confidence_text}"
        "</div>",
        unsafe_allow_html=True,
    )


def _user_story_showcase() -> None:
    st.title("Sevaq User Story")
    st.caption("Static showcase of customer outcomes: clear value, low friction, and trust-aware behavior.")
    selected = st.selectbox(
        "Pick a customer moment",
        [item["title"] for item in STATIC_DEMO_HIGHLIGHTS],
        key="user_story_select",
    )
    item = next(h for h in STATIC_DEMO_HIGHLIGHTS if h["title"] == selected)
    st.markdown(
        "<div class='card'><b>Prompt A (baseline)</b><br/>"
        + item["baseline_prompt"]
        + "<br/><b>Response style:</b> "
        + item["baseline_mode"]
        + "<br/><br/><b>Sevaq answer</b><br/>"
        + item["baseline_response"]
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='card'><b>Prompt B (same task, higher sensitivity/complexity)</b><br/>"
        + item["adapted_prompt"]
        + "<br/><b>Response style:</b> "
        + item["adapted_mode"]
        + "<br/><br/><b>Sevaq answer</b><br/>"
        + item["adapted_response"]
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='card'><b>Why this is a product win</b><br/>"
        + f"<b>High-level value:</b> {item['highlight']}<br/><br/>"
        + f"<b>Business impact:</b> {item['business_win']}"
        + "</div>",
        unsafe_allow_html=True,
    )


def _founder_demo_page() -> None:
    st.title("Sevaq Founder Demo")
    st.caption("Curated static narrative for investor and customer storytelling.")
    st.markdown(
        "<div class='card'><b>What investors should notice</b><br/>"
        "Each scenario below shows the same core task under two conditions. "
        "Sevaq adapts response depth and tone based on sensitivity and complexity, then translates that into business impact."
        "</div>",
        unsafe_allow_html=True,
    )
    for item in STATIC_DEMO_HIGHLIGHTS:
        st.subheader(item["title"])
        col_a, col_b = st.columns(2)
        col_a.markdown(
            "<div class='card'><b>Baseline scenario</b><br/>"
            + f"<b>Prompt:</b> {item['baseline_prompt']}<br/>"
            + f"<b>Response style:</b> {item['baseline_mode']}<br/><br/>"
            + f"{item['baseline_response']}"
            + "</div>",
            unsafe_allow_html=True,
        )
        col_b.markdown(
            "<div class='card'><b>Adapted scenario</b><br/>"
            + f"<b>Prompt:</b> {item['adapted_prompt']}<br/>"
            + f"<b>Response style:</b> {item['adapted_mode']}<br/><br/>"
            + f"{item['adapted_response']}"
            + "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='card'><b>Differentiation:</b> "
            + item["highlight"]
            + "<br/><b>Business value:</b> "
            + item["business_win"]
            + "</div>",
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="Sevaq Founder Demo",
        page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else None,
        layout="wide",
    )
    _style()
    _render_logo()
    _why_sevaq_panel()
    # Keep UX in simplified mode until advanced panel is productized.
    st.session_state["advanced_view"] = False
    st.sidebar.markdown("### Experience")
    page = st.sidebar.radio(
        "Choose view",
        options=["Founder Demo", "User Preview (Live)", "User Story (Static)"],
        index=0,
        label_visibility="collapsed",
    )
    if page == "Founder Demo":
        _founder_demo_page()
    elif page == "User Preview (Live)":
        _user_facing_preview()
    else:
        _user_story_showcase()


if __name__ == "__main__":
    main()
