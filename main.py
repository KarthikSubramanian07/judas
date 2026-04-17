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
            try:
                with st.spinner(f"Generating '{scenario['label']}' scenario..."):
                    sess = session_manager.new_session(mode=st.session_state.mode)
                    sess = session_manager.start(sess, scenario["label"], scenario["type"])
                st.session_state.session = sess
                if st.session_state.mode == "baseline":
                    st.session_state.baseline_done = True
                    st.session_state.baseline_last_scenario = scenario["label"]
                    if sess["turn_count"] > 0:
                        st.session_state.baseline_avg_tokens = round(sess["total_tokens"] / sess["turn_count"], 1)
                else:
                    st.session_state.baseline_session = None
            except RuntimeError as e:
                st.session_state.top_error = str(e)

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
    col1, col2 = st.columns(2)
    col1.metric("Scam Score", result["scam_score"])
    col2.metric("Scam Type", result["scam_type"].capitalize())

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
        if sess["status"] == "active":
            st.subheader("Continue Conversation")

            follow_up = st.text_area(
                "Scammer reply:",
                value=st.session_state.ai_draft,
                placeholder="Type the next scammer message or click Simulate Reply",
                key=f"scammer_ta_{st.session_state.draft_version}",
                height=180,
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
                        with st.spinner("Generating scammer reply..."):
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

            if send_clicked and follow_up.strip():
                try:
                    with st.spinner("JUDAS is thinking..."):
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
                    with st.spinner("JUDAS is thinking..."):
                        sess = session_manager.process_turn(sess, "forget it, bye", mode=sess["mode"])
                    st.session_state.session = sess
                    if sess["mode"] == "baseline" and sess["turn_count"] > 0:
                        st.session_state.baseline_avg_tokens = round(sess["total_tokens"] / sess["turn_count"], 1)
                    if sess["mode"] == "judas":
                        st.session_state.scroll_to_analysis = True
                    st.session_state.ai_draft = ""
                    st.session_state.draft_version += 1
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
        else:
            st.subheader("Session Ended")
            st.markdown(
                f"""<div style="padding:16px; background:#f5f7fa; border:1px solid #dde3ee;
                                border-radius:10px; color:#3a4a6b; font-size:0.9rem;">
                        {get_status_label(sess['status'])}
                    </div>""",
                unsafe_allow_html=True,
            )

    # Metrics panel — shown below the input section
    if sess["strategy"] or sess["mode"] == "baseline":
        st.divider()
        st.subheader("Session Metrics")

        strategy_tooltip = (
            "Naive Inquiry — Plays confused, asks simple innocent questions to slow things down.\n"
            "Technical Expansion — Requests reference numbers, supervisor names, callback numbers.\n"
            "Constraint Injection — Introduces realistic personal obstacles to delay action.\n"
            "Recursive Clarification — Loops back and re-asks earlier questions from the start.\n"
            "Format Enforcement — Demands written confirmation, email, or physical address."
        )
        baseline_per_turn  = st.session_state.baseline_avg_tokens or BASELINE_TOKENS_PER_TURN
        baseline_source    = "measured from your last Baseline run" if st.session_state.baseline_avg_tokens else "estimated (~10 words \u00d7 1.3 tokens/word)"
        turns              = max(sess["turn_count"], 1)
        baseline_total     = turns * baseline_per_turn
        judas_total        = sess["total_tokens"]
        session_effort     = round(judas_total / baseline_total, 1) if judas_total else 0.0

        effort_tooltip = (
            f"Effort Multiplier = JUDAS tokens \u00f7 (turns \u00d7 baseline tokens per turn)\n"
            f"= {judas_total} \u00f7 ({turns} \u00d7 {baseline_per_turn})\n"
            f"= {judas_total} \u00f7 {baseline_total}\n"
            f"= {session_effort}x\n\n"
            f"Baseline tokens per turn: {baseline_per_turn} ({baseline_source}).\n"
            f"A cooperative target would generate ~{baseline_total} tokens across {turns} turn(s).\n"
            f"JUDAS generated {judas_total} tokens — {session_effort}x more content for the scammer to process."
        )

        tokens_val = str(judas_total) if sess["tax_result"] else "—"

        rows = (
            f"<tr><td>Turn</td><td>{sess['turn_count']}</td></tr>"
            f"<tr><td>Messages</td><td>{sess['message_count']}</td></tr>"
            f"<tr><td>Status</td><td>{get_status_label(sess['status'])}</td></tr>"
            f"<tr><td>Tokens</td><td>{tokens_val}</td></tr>"
        )

        if sess["mode"] == "judas":
            strategy_val = sess["strategy"] or "—"
            effort_val   = f"{session_effort}x" if sess["tax_result"] else "—"
            rows += (
                f"<tr><td>Strategy &nbsp;"
                f'<span title="{strategy_tooltip}" style="cursor:help;color:#4a6cf7;font-weight:700;">&#9432;</span>'
                f"</td><td>{strategy_val}</td></tr>"
                f"<tr><td>Effort &nbsp;"
                f'<span title="{effort_tooltip}" style="cursor:help;color:#4a6cf7;font-weight:700;">&#9432;</span>'
                f"</td><td>{effort_val}</td></tr>"
            )

        metrics_html = (
            "<table>"
            "<thead><tr><th>Metric</th><th>Value</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )
        st.markdown(metrics_html, unsafe_allow_html=True)

    elif sess["status"] == "disengaged" and sess["mode"] == "baseline":
        st.warning("The scammer appears to have disengaged.")
    elif sess["status"] == "max_turns_reached" and sess["mode"] == "baseline":
        st.warning(f"Maximum session length of {MAX_TURNS} turns reached.")

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

        data = {
            "Metric": [
                "Conversation Turns",
                "Total Tokens Used",
                "Avg Tokens per Response",
                "Effort Multiplier",
                "Engagement Status",
            ],
            "Baseline": [
                str(sess["turn_count"]),
                str(baseline_total_tokens),
                str(baseline_tokens_per_turn),
                "1.0x",
                "Cooperative — scammer advances quickly",
            ],
            "JUDAS": [
                str(sess["turn_count"]),
                str(judas_total_tokens),
                str(avg_judas_tokens),
                f"{effort_mult}x",
                get_status_label(sess["status"]),
            ],
            "What This Means": [
                "Number of exchanges before the scammer disengaged or session ended.",
                "More tokens from JUDAS means the scammer had to read and process longer, more complex replies.",
                "JUDAS responses are significantly longer, forcing the scammer to invest more time per turn.",
                f"JUDAS required {effort_mult}x more token effort from the scammer compared to a cooperative target.",
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
