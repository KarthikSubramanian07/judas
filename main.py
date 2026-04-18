import json
import streamlit as st
from config import MAX_TURNS, AVAILABLE_MODELS, BASELINE_TOKENS_PER_TURN
import modules.brain as brain
from modules.brain import scammer_reply
from modules.engagement_tracker import get_status_label
from modules import session_manager

st.set_page_config(page_title="JUDAS", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    /* Page background */
    .stApp { background-color: #f5f7fa; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #dde3ee;
    }

    /* Title */
    h1 { color: #1a2340 !important; letter-spacing: 1px; }
    h2, h3 { color: #2c3e6b !important; }

    /* Body text */
    p, li, label { color: #3a4a6b !important; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #dde3ee;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    [data-testid="stMetricLabel"] { color: #6b7a99 !important; font-size: 0.78rem !important; }
    [data-testid="stMetricValue"] { color: #1a2340 !important; font-size: 1.1rem !important; }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background-color: #ffffff;
        border: 1px solid #dde3ee;
        border-radius: 10px;
        margin-bottom: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }

    /* Buttons */
    .stButton > button {
        background-color: #ffffff;
        color: #2c3e6b;
        border: 1px solid #c2cce0;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #eef1f9;
        border-color: #4a6cf7;
        color: #1a2340;
    }

    /* Text area */
    .stTextArea textarea {
        background-color: #ffffff;
        color: #1a2340;
        border: 1px solid #c2cce0;
        border-radius: 8px;
    }

    /* Radio buttons */
    [data-testid="stRadio"] label { color: #2c3e6b !important; }

    /* Divider */
    hr { border-color: #dde3ee !important; }

    /* Table */
    table {
        background-color: #ffffff !important;
        color: #2c3e6b !important;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    thead tr th {
        background-color: #eef1f9 !important;
        color: #1a2340 !important;
        font-weight: 600;
        padding: 10px 14px !important;
    }
    tbody tr td {
        padding: 10px 14px !important;
        border-bottom: 1px solid #dde3ee !important;
        color: #2c3e6b !important;
    }
    tbody tr:hover td { background-color: #f5f7fa !important; }

    /* Info / warning / success boxes */
    [data-testid="stAlert"] { border-radius: 10px; }

    /* Caption */
    [data-testid="stCaptionContainer"] { color: #8a96b0 !important; }

    /* Help icon tooltip */
    [data-testid="stTooltipHoverTarget"] { color: #4a6cf7 !important; font-size: 1rem !important; }

    /* Sidebar strategy expander labels */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p { font-size: 0.75rem !important; }

    /* Tighten gap between mode radio and scenario dropdown */
    [data-testid="stRadio"] { margin-bottom: 6px !important; }
    [data-testid="stSelectbox"] { margin-top: 0 !important; }

    /* Always-visible scrollbar for conversation container */
    [data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar { width: 7px; }
    [data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-track { background: #eef1f9; border-radius: 4px; }
    [data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-thumb { background: #c2cce0; border-radius: 4px; }
    [data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-thumb:hover { background: #4a6cf7; }
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] { overflow-y: scroll !important; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Model Selector ---
with st.sidebar:
    st.header("Settings")
    selected_label = st.selectbox(
        "LLM Model",
        options=list(AVAILABLE_MODELS.keys()),
        index=0,
        help="Switch models if you hit a rate limit",
    )
    selected_model = AVAILABLE_MODELS[selected_label]

    # Override the model used by brain module at runtime
    brain.GROQ_MODEL_OVERRIDE = selected_model

    st.caption(f"Active: `{selected_model}`")
    st.divider()
    st.caption("Switch to **Llama 3.1 8B** if you hit a rate limit.")

    st.divider()
    st.header("Strategies")
    st.caption(
        "JUDAS rotates through five strategies as the conversation progresses. "
        "Each one is designed to waste more of the scammer's time."
    )

    strategies_info = [
        (
            "Naive Inquiry",
            "Turn 1",
            "Plays confused and friendly. Asks simple innocent questions as if something isn't quite clicking. "
            "Forces the scammer to re-explain their pitch from scratch.",
        ),
        (
            "Technical Expansion",
            "Turns 2–3",
            "Requests verifiable details before agreeing to anything — reference numbers, "
            "supervisor names, callback numbers. Makes the scammer fabricate specifics on the spot.",
        ),
        (
            "Constraint Injection",
            "Turns 4–5",
            "Introduces realistic personal obstacles. Phone issues, being at work, needing to "
            "ask a spouse, can't find a card. Delays action without outright refusing.",
        ),
        (
            "Recursive Clarification",
            "Turns 6–7",
            "Loops back to earlier parts of the conversation asking for re-explanation. "
            "The scammer must repeat themselves while getting no closer to their goal.",
        ),
        (
            "Format Enforcement",
            "Turn 8+",
            "Demands everything in writing — a letter, an email, a physical address. "
            "Old-fashioned and cautious. Impossible for a scammer to satisfy quickly.",
        ),
    ]

    for name, turns, description in strategies_info:
        with st.expander(f"{name}  ·  {turns}"):
            st.caption(description)

st.markdown("""
<div style="padding: 1.5rem 0 0.5rem 0;">
    <h1 style="font-size:2.4rem; font-weight:800; color:#1a2340; letter-spacing:2px; margin-bottom:4px;">
        JUDAS
    </h1>
    <p style="color:#4a6cf7; font-size:1rem; letter-spacing:3px; font-weight:500; margin:0;">
        ADVERSARIAL FRAUD DISRUPTOR
    </p>
    <p style="color:#8a96b0; font-size:0.85rem; letter-spacing:2px; margin-top:4px;">
        DETECT &nbsp;·&nbsp; ENGAGE &nbsp;·&nbsp; EXHAUST
    </p>
    <p style="color:#6b7a99; font-size:0.82rem; font-style:italic; margin-top:6px; letter-spacing:0.3px;">
        Making AI-powered fraud expensive, one wasted minute at a time.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# --- Load scenarios ---
with open("data/scenarios.json") as f:
    scenarios = json.load(f)

# --- Session state ---
if "session" not in st.session_state:
    st.session_state.session = None
if "selected_scenario" not in st.session_state:
    st.session_state.selected_scenario = None
if "ai_draft" not in st.session_state:
    st.session_state.ai_draft = ""
if "draft_version" not in st.session_state:
    st.session_state.draft_version = 0
if "mode" not in st.session_state:
    st.session_state.mode = "baseline"
if "baseline_session" not in st.session_state:
    st.session_state.baseline_session = None
if "scenario_version" not in st.session_state:
    st.session_state.scenario_version = 0
if "baseline_done" not in st.session_state:
    st.session_state.baseline_done = False
if "top_error" not in st.session_state:
    st.session_state.top_error = None
if "baseline_avg_tokens" not in st.session_state:
    st.session_state.baseline_avg_tokens = None
if "baseline_last_scenario" not in st.session_state:
    st.session_state.baseline_last_scenario = None
if "scroll_to_analysis" not in st.session_state:
    st.session_state.scroll_to_analysis = False
if "baseline_complete_msg" not in st.session_state:
    st.session_state.baseline_complete_msg = False
if "pending_scenario" not in st.session_state:
    st.session_state.pending_scenario = None

# --- Two-phase scenario loading (runs before columns to avoid stale-content duplication) ---
if st.session_state.pending_scenario:
    pending = st.session_state.pending_scenario
    with st.spinner(f"Generating '{pending['label']}' scenario..."):
        try:
            sess = session_manager.new_session(mode=st.session_state.mode)
            sess = session_manager.start(sess, pending["label"], pending["type"])
            st.session_state.session = sess
            if st.session_state.mode == "baseline":
                st.session_state.baseline_done = True
                st.session_state.baseline_last_scenario = pending["label"]
                if sess["turn_count"] > 0:
                    st.session_state.baseline_avg_tokens = round(
                        sess["total_tokens"] / sess["turn_count"], 1
                    )
            else:
                st.session_state.baseline_session = None
        except RuntimeError as e:
            st.session_state.top_error = str(e)
    st.session_state.pending_scenario = None
    st.rerun()

# Show soft popup once after baseline bye — fades out after 8 seconds
if st.session_state.baseline_complete_msg:
    st.markdown(
        '<div style="position:fixed;bottom:28px;right:28px;z-index:9999;'
        'background:#2e7d32;color:#ffffff;padding:12px 18px;border-radius:8px;'
        'font-size:0.84rem;font-family:sans-serif;box-shadow:0 4px 14px rgba(0,0,0,0.22);'
        'animation:judas-fadeout 0.6s ease 8s forwards;">'
        '&#10003;&nbsp; Baseline complete — switch to <b>JUDAS</b> mode to compare.'
        '</div>'
        '<style>@keyframes judas-fadeout{from{opacity:1}to{opacity:0}}</style>',
        unsafe_allow_html=True,
    )
    st.session_state.baseline_complete_msg = False

# --- Mode + Scenario (left) / Instructions (right) ---
col_left_ctrl, col_right_info = st.columns([2, 3], gap="medium")

with col_left_ctrl:
    mode = st.radio(
        "Mode",
        options=["baseline", "judas"],
        format_func=lambda x: "Baseline" if x == "baseline" else "JUDAS",
        horizontal=True,
        key="mode_radio",
    )
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        st.session_state.session = None
        st.session_state.selected_scenario = None
        st.session_state.ai_draft = ""
        st.session_state.draft_version = 0
        st.session_state.scenario_version += 1
        st.session_state.top_error = None
        st.rerun()

    scenario_options = ["— Select a scenario —"] + [s["label"] for s in scenarios]
    # In JUDAS mode, auto-select the last baseline scenario
    default_index = 0
    if st.session_state.mode == "judas" and st.session_state.baseline_last_scenario:
        try:
            default_index = scenario_options.index(st.session_state.baseline_last_scenario)
        except ValueError:
            default_index = 0
    is_judas = st.session_state.mode == "judas"
    selected_label = st.selectbox(
        "Select a Scenario",
        options=scenario_options,
        index=default_index,
        key=f"scenario_select_{st.session_state.scenario_version}",
        label_visibility="collapsed",
        disabled=is_judas,
    )

with col_right_info:
    if st.session_state.mode == "baseline":
        st.markdown(
            '<div style="background:#e8f4fd;border-left:3px solid #4a90d9;border-radius:6px;'
            'padding:8px 12px;font-size:0.78rem;line-height:1.8;color:#1a2340;">'
            '<b>Baseline Mode</b> — cooperative, non-resistant respondent.<br>'
            '1. Select a scenario from the dropdown.<br>'
            '2. Click <b>Simulate Reply</b> or type a scammer follow-up.<br>'
            '3. Click <b>Send</b> to see a brief cooperative response.<br>'
            '4. Click <b>Bye</b> when done and note the turn count and tokens used.<br>'
            '5. Switch to <b>JUDAS</b> mode to compare.'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:#e8f4fd;border-left:3px solid #4a90d9;border-radius:6px;'
            'padding:8px 12px;font-size:0.78rem;line-height:1.8;color:#1a2340;margin-bottom:6px;">'
            '<b>JUDAS Mode</b> — adaptive AI that wastes scammer time using rotating strategies.<br>'
            '1. The scenario is automatically set to match your last Baseline run.<br>'
            '2. Click <b>Simulate Reply</b> or type a scammer follow-up.<br>'
            '3. Click <b>Send</b> to see JUDAS respond.<br>'
            '4. Watch the <b>Strategy</b> change as the conversation progresses.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="background:#edf7ee;border-left:3px solid #3a9e4f;border-radius:6px;'
            'padding:8px 12px;font-size:0.78rem;line-height:1.8;color:#1a2340;">'
            '<b>Comparison Analysis</b> — after the session ends, a table compares JUDAS vs Baseline '
            'across turns, tokens, effort, and outcome.<br>'
            'Click <b>Bye</b> at any point to end the session and view results.'
            '</div>',
            unsafe_allow_html=True,
        )

if selected_label != "— Select a scenario —":
    scenario = next(s for s in scenarios if s["label"] == selected_label)
    current = st.session_state.selected_scenario
    if current is None or current["label"] != selected_label:
        if st.session_state.mode == "judas" and scenario["type"] == "normal":
            st.session_state.top_error = (
                f"**{scenario['label']}** is not a scam scenario — JUDAS has nothing to engage with. "
                "Please select one of the scam scenarios to run a JUDAS simulation."
            )
            st.session_state.scenario_version += 1
            st.rerun()
        elif st.session_state.mode == "judas" and not st.session_state.baseline_done:
            st.session_state.top_error = (
                "Please run a **Baseline** simulation first. "
                "Switch to Baseline mode, select a scenario, and complete at least one turn — "
                "then return to JUDAS mode to compare."
            )
            st.session_state.scenario_version += 1
            st.rerun()
        else:
            st.session_state.top_error = None
            st.session_state.selected_scenario = scenario
            st.session_state.session = None
            st.session_state.ai_draft = ""
            st.session_state.draft_version = 0
            st.session_state.pending_scenario = scenario
            st.rerun()

# --- Persistent error banner ---
if st.session_state.top_error:
    st.markdown("<br>", unsafe_allow_html=True)
    st.error(st.session_state.top_error)

# --- Show conversation ---
if st.session_state.session:
    sess = st.session_state.session
    scenario = st.session_state.selected_scenario
    result = sess["sentry_result"]

    col_title, col_mode_badge = st.columns([4, 1])
    with col_title:
        st.subheader(f"Scenario: {scenario['label']}")
    with col_mode_badge:
        if sess["mode"] == "judas":
            st.success("JUDAS Mode")
        else:
            st.warning("Baseline Mode")

    # Sentry metrics
    score_pct = round(result["scam_score"] * 100)
    if score_pct >= 70:
        conf_label = "High"
        conf_color = "#c0392b"
        conf_bg    = "#fdecea"
    elif score_pct >= 40:
        conf_label = "Medium"
        conf_color = "#d97706"
        conf_bg    = "#fff8e8"
    else:
        conf_label = "Low"
        conf_color = "#2e7d32"
        conf_bg    = "#edf7ee"

    col1, col2, col3 = st.columns(3)
    col1.metric("Scam Score", f"{score_pct}%")
    col2.metric("Scam Type", result["scam_type"].capitalize())
    col3.markdown(
        f'<div style="background:{conf_bg};border:1px solid {conf_color};border-radius:10px;'
        f'padding:12px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
        f'<div style="color:#6b7a99;font-size:0.78rem;font-weight:500;">Detection Confidence</div>'
        f'<div style="color:{conf_color};font-size:1.1rem;font-weight:700;margin-top:4px;">'
        f'{conf_label} &nbsp;({score_pct}%)</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    score = result["scam_score"]
    is_known_scam = sess.get("scenario_type") == "scam"

    if score >= 0.6:
        st.error("High scam likelihood detected.")
    elif score >= 0.3 or is_known_scam:
        st.warning("Moderate scam indicators found.")
    else:
        st.success("This does not appear to be a scam. JUDAS will not engage.")
        st.divider()
        st.subheader("Message Received")
        st.info(sess["opening"])
        st.stop()

    # Two-column layout: conversation left, input right
    st.divider()
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.subheader("Conversation")
        with st.container(height=480):
            for msg in sess["history"]:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.caption("SCAMMER")
                        st.write(msg["content"])
                else:
                    resp_label = "JUDAS" if sess["mode"] == "judas" else "RESPONDENT"
                    with st.chat_message("assistant"):
                        st.caption(resp_label)
                        st.write(msg["content"])

    with col_right:
        # Pre-initialise so handlers below can reference these regardless of active state
        follow_up    = ""
        send_clicked = False
        bye_clicked  = False

        if sess["status"] == "active":
            st.subheader("Continue Conversation")

            lbl_col, gen_col = st.columns([2, 3])
            lbl_col.markdown(
                '<span style="font-size:0.82rem;color:#3a4a6b;font-weight:500;">Scammer reply</span>',
                unsafe_allow_html=True,
            )
            gen_placeholder = gen_col.empty()

            follow_up = st.text_area(
                "Scammer reply:",
                value=st.session_state.ai_draft,
                placeholder="Type the next scammer message or click Simulate Reply",
                key=f"scammer_ta_{st.session_state.draft_version}",
                height=160,
                label_visibility="collapsed",
            )

            col_simulate, col_send, col_bye = st.columns([1, 1, 1])
            with col_simulate:
                if st.button(
                    "Simulate Reply",
                    key=f"ai_btn_{sess['turn_count']}",
                    use_container_width=True,
                    help="Let AI generate a realistic follow-up scammer message",
                ):
                    try:
                        gen_placeholder.markdown(
                            '<span style="font-size:0.82rem;color:#c0392b;font-style:italic;">'
                            'Generating reply…</span>',
                            unsafe_allow_html=True,
                        )
                        draft = scammer_reply(sess["history"])
                        st.session_state.ai_draft = draft
                        st.session_state.draft_version += 1
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))

            with col_send:
                send_clicked = st.button(
                    "Send",
                    key=f"send_turn_{sess['turn_count']}",
                    use_container_width=True,
                )

            with col_bye:
                bye_clicked = st.button(
                    "Bye",
                    key=f"bye_turn_{sess['turn_count']}",
                    use_container_width=True,
                    help="Simulate the scammer disengaging",
                )
        else:
            st.subheader("Session Ended")
            st.markdown(
                f"""<div style="padding:16px; background:#f5f7fa; border:1px solid #dde3ee;
                                border-radius:10px; color:#3a4a6b; font-size:0.9rem;">
                        {get_status_label(sess['status'])}
                    </div>""",
                unsafe_allow_html=True,
            )

        # --- Session Metrics box — sits below continue/ended in the right column ---
        if sess["strategy"] or sess["mode"] == "baseline":
            baseline_per_turn = st.session_state.baseline_avg_tokens or BASELINE_TOKENS_PER_TURN
            baseline_source   = "measured from your last Baseline run" if st.session_state.baseline_avg_tokens else "estimated (~10 words \u00d7 1.3 tokens/word)"
            turns             = max(sess["turn_count"], 1)
            baseline_total    = turns * baseline_per_turn
            judas_total       = sess["total_tokens"]
            session_effort    = round(judas_total / baseline_total, 1) if judas_total else 0.0

            strategy_tooltip = (
                "Naive Inquiry \u2014 Plays confused, asks simple innocent questions to slow things down.&#10;"
                "Technical Expansion \u2014 Requests reference numbers, supervisor names, callback numbers.&#10;"
                "Constraint Injection \u2014 Introduces realistic personal obstacles to delay action.&#10;"
                "Recursive Clarification \u2014 Loops back and re-asks earlier questions from the start.&#10;"
                "Format Enforcement \u2014 Demands written confirmation, email, or physical address."
            )
            effort_tooltip = (
                f"Effort Multiplier = JUDAS tokens \u00f7 (turns \u00d7 baseline tokens per turn)&#10;"
                f"= {judas_total} \u00f7 ({turns} \u00d7 {baseline_per_turn})&#10;"
                f"= {judas_total} \u00f7 {baseline_total}&#10;"
                f"= {session_effort}x&#10;&#10;"
                f"Baseline tokens per turn: {baseline_per_turn} ({baseline_source}).&#10;"
                f"A cooperative target would generate ~{baseline_total} tokens across {turns} turn(s).&#10;"
                f"JUDAS generated {judas_total} tokens \u2014 {session_effort}x more content for the scammer to process."
            )

            tokens_val  = str(judas_total) if sess["tax_result"] else "—"
            status_val  = get_status_label(sess["status"])

            def _metric_card(label, value, tooltip=None):
                tip = f' title="{tooltip}"' if tooltip else ""
                tip_icon = (
                    f' &nbsp;<span{tip} style="cursor:help;color:#4a6cf7;font-weight:700;font-size:0.7rem;">&#9432;</span>'
                    if tooltip else ""
                )
                return (
                    f'<div style="background:#f5f7fa;border:1px solid #e4e9f2;border-radius:6px;padding:6px 10px;">'
                    f'<div style="color:#8a96b0;font-size:0.68rem;font-weight:500;line-height:1.2;">{label}{tip_icon}</div>'
                    f'<div style="color:#c45c00;font-size:0.82rem;font-weight:600;margin-top:3px;line-height:1.2;">{value}</div>'
                    f'</div>'
                )

            if sess["mode"] == "judas":
                strategy_val = sess["strategy"] or "—"
                effort_val   = f"{session_effort}x" if sess["tax_result"] else "—"
                cards = [
                    _metric_card("Turn",     str(sess["turn_count"])),
                    _metric_card("Messages", str(sess["message_count"])),
                    _metric_card("Tokens",   tokens_val),
                    _metric_card("Status",   status_val),
                    _metric_card("Strategy", strategy_val, strategy_tooltip),
                    _metric_card("Effort",   effort_val,   effort_tooltip),
                ]
                grid_cols = "repeat(3,1fr)"
            else:
                cards = [
                    _metric_card("Turn",     str(sess["turn_count"])),
                    _metric_card("Messages", str(sess["message_count"])),
                    _metric_card("Status",   status_val),
                    _metric_card("Tokens",   tokens_val),
                ]
                grid_cols = "repeat(2,1fr)"

            cards_html = "".join(cards)
            st.markdown(
                f'<div style="border:1px solid #dde3ee;border-radius:8px;padding:10px 12px;'
                f'background:#ffffff;margin-top:4px;">'
                f'<div style="font-size:0.68rem;font-weight:600;color:#8a96b0;letter-spacing:0.8px;'
                f'text-transform:uppercase;margin-bottom:8px;">Session Metrics</div>'
                f'<div style="display:grid;grid-template-columns:{grid_cols};gap:6px;">'
                f'{cards_html}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        elif sess["status"] == "disengaged" and sess["mode"] == "baseline":
            st.warning("The scammer appears to have disengaged.")
        elif sess["status"] == "max_turns_reached" and sess["mode"] == "baseline":
            st.warning(f"Maximum session length of {MAX_TURNS} turns reached.")

        # Thinking placeholder lives below session metrics
        thinking_placeholder = st.empty()

        if send_clicked and follow_up.strip():
            try:
                thinking_placeholder.markdown(
                    '<div style="font-size:0.82rem;color:#c0392b;font-style:italic;padding:6px 0;">'
                    'JUDAS is thinking…</div>',
                    unsafe_allow_html=True,
                )
                sess = session_manager.process_turn(sess, follow_up.strip(), mode=sess["mode"])
                st.session_state.session = sess
                if sess["mode"] == "baseline" and sess["turn_count"] > 0:
                    st.session_state.baseline_avg_tokens = round(sess["total_tokens"] / sess["turn_count"], 1)
                st.session_state.ai_draft = ""
                st.session_state.draft_version += 1
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))

        if bye_clicked:
            try:
                thinking_placeholder.markdown(
                    '<div style="font-size:0.82rem;color:#c0392b;font-style:italic;padding:6px 0;">'
                    'JUDAS is thinking…</div>',
                    unsafe_allow_html=True,
                )
                bye_msg = "forget it, bye" if sess["mode"] == "judas" else "okay, thank you, goodbye"
                sess = session_manager.process_turn(sess, bye_msg, mode=sess["mode"])
                st.session_state.session = sess
                if sess["mode"] == "baseline" and sess["turn_count"] > 0:
                    st.session_state.baseline_avg_tokens = round(sess["total_tokens"] / sess["turn_count"], 1)
                if sess["mode"] == "judas":
                    st.session_state.scroll_to_analysis = True
                else:
                    st.session_state.baseline_complete_msg = True
                st.session_state.ai_draft = ""
                st.session_state.draft_version += 1
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))

    # --- Comparison panel (shown after metrics when session ends in judas mode) ---
    if sess["status"] != "active" and sess["mode"] == "judas":
        import warnings
        import pandas as pd
        import streamlit.components.v1 as _components

        if st.session_state.scroll_to_analysis:
            st.toast("Analysis complete — results are shown below.", icon="✅")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _components.html(
                    """<script>
                    setTimeout(function() {
                        window.parent.scrollTo({
                            top: window.parent.document.body.scrollHeight,
                            behavior: 'smooth'
                        });
                    }, 400);
                    </script>""",
                    height=1,
                )
            st.session_state.scroll_to_analysis = False

        st.divider()
        st.subheader("Session Analysis — JUDAS vs Baseline")
        st.caption(
            "Baseline represents a cooperative, non-resistant respondent. "
            "JUDAS uses adaptive strategies to maximise scammer effort and time spent."
        )

        baseline_tokens_per_turn = st.session_state.baseline_avg_tokens or BASELINE_TOKENS_PER_TURN
        baseline_total_tokens    = max(sess["turn_count"] * baseline_tokens_per_turn, 1)
        judas_total_tokens       = sess["total_tokens"]
        effort_mult              = round(judas_total_tokens / baseline_total_tokens, 1)
        avg_judas_tokens         = round(judas_total_tokens / max(sess["turn_count"], 1))

        # Time estimates: ~90 seconds per turn for a scammer to read + respond
        avg_sec_per_turn    = 90
        n_turns             = max(sess["turn_count"], 1)
        baseline_time_s     = n_turns * avg_sec_per_turn
        judas_time_s        = round(effort_mult * baseline_time_s)
        time_wasted_s       = judas_time_s - baseline_time_s

        def _fmt_time(secs: int) -> str:
            secs = int(secs)
            if secs < 60:
                return f"~{secs}s"
            m, s = divmod(secs, 60)
            return f"~{m}m {s}s" if s else f"~{m}m"

        data = {
            "Metric": [
                "Conversation Turns",
                "Total Tokens Used",
                "Avg Tokens per Response",
                "Effort Multiplier",
                "Scammer Time (est.)",
                "Engagement Status",
            ],
            "Baseline": [
                str(sess["turn_count"]),
                str(baseline_total_tokens),
                str(baseline_tokens_per_turn),
                "1.0x",
                _fmt_time(baseline_time_s),
                "Cooperative — scammer advances quickly",
            ],
            "JUDAS": [
                str(sess["turn_count"]),
                str(judas_total_tokens),
                str(avg_judas_tokens),
                f"{effort_mult}x",
                _fmt_time(judas_time_s),
                get_status_label(sess["status"]),
            ],
            "What This Means": [
                "Number of exchanges before the scammer disengaged or session ended.",
                "More tokens from JUDAS means the scammer had to read and process longer, more complex replies.",
                "JUDAS responses are significantly longer, forcing the scammer to invest more time per turn.",
                f"JUDAS required {effort_mult}x more token effort from the scammer compared to a cooperative target.",
                f"JUDAS wasted an extra {_fmt_time(time_wasted_s)} of scammer time vs a cooperative target (est. 90s/turn).",
                "JUDAS prolonged the interaction — a cooperative baseline would have concluded far sooner.",
            ],
        }

        st.table(pd.DataFrame(data))

        if effort_mult >= 3:
            st.success(
                f"JUDAS forced the scammer to process {effort_mult}x more content than they would have with a "
                f"cooperative baseline respondent — meaning the scammer had to invest {effort_mult}x more time "
                f"and effort for zero result. This is a strong disruption score."
            )
        elif effort_mult >= 1.5:
            st.info(
                f"JUDAS generated an effort score of {effort_mult}x against the baseline — the scammer had to "
                f"process {effort_mult}x more content compared to a cooperative target who would simply comply. "
                f"Running more turns will drive this score higher as JUDAS continues to delay and exhaust."
            )
        else:
            st.warning(
                f"JUDAS effort score is {effort_mult}x against the baseline. The session was short so the "
                f"disruption impact is limited. Run more turns before clicking Bye to build a stronger contrast."
            )

        # Scale impact statement
        intercepts_100    = 100
        intercepts_1000   = 1_000
        hours_100         = round((time_wasted_s * intercepts_100) / 3600, 1)
        hours_1000        = round((time_wasted_s * intercepts_1000) / 3600, 1)
        st.markdown(
            f'<div style="background:#f0f4ff;border:1px solid #c5cde8;border-radius:10px;'
            f'padding:14px 18px;margin-top:12px;">'
            f'<div style="color:#1a2340;font-weight:700;font-size:0.9rem;margin-bottom:6px;">'
            f'Scale Impact</div>'
            f'<div style="color:#2c3e6b;font-size:0.85rem;line-height:1.7;">'
            f'At this effort score of <b>{effort_mult}x</b>, each JUDAS intercept wastes '
            f'<b>{_fmt_time(time_wasted_s)}</b> of scammer time over a cooperative target.<br>'
            f'&bull;&nbsp; <b>100 intercepts/day</b> &rarr; <b>~{hours_100} scammer-hours wasted daily</b><br>'
            f'&bull;&nbsp; <b>1,000 intercepts/day</b> &rarr; <b>~{hours_1000} scammer-hours wasted daily</b><br>'
            f'<span style="color:#6b7a99;font-size:0.8rem;">At scale, the economics of AI-powered mass fraud collapse.</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
