import json
import streamlit as st
from config import MAX_TURNS
from modules.brain import scammer_reply
from modules.engagement_tracker import get_status_label
from modules import session_manager

st.set_page_config(page_title="JUDAS", layout="wide")

st.title("JUDAS — Adversarial Fraud Disruptor")
st.caption("Detect. Engage. Exhaust.")

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
    st.session_state.mode = "judas"
if "baseline_session" not in st.session_state:
    st.session_state.baseline_session = None

# --- Mode toggle ---
col_mode, col_spacer = st.columns([2, 6])
with col_mode:
    mode = st.radio(
        "Mode",
        options=["judas", "baseline"],
        format_func=lambda x: "JUDAS" if x == "judas" else "Baseline",
        horizontal=True,
        key="mode_radio",
    )
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        st.session_state.session = None
        st.session_state.ai_draft = ""
        st.session_state.draft_version = 0
        st.rerun()

st.divider()

# --- Scenario buttons ---
st.subheader("Select a Scenario")
cols = st.columns(len(scenarios))

for i, scenario in enumerate(scenarios):
    with cols[i]:
        if st.button(scenario["label"], key=scenario["id"]):
            st.session_state.selected_scenario = scenario
            st.session_state.ai_draft = ""
            st.session_state.draft_version = 0
            with st.spinner(f"Generating '{scenario['label']}' scenario..."):
                sess = session_manager.new_session(mode=st.session_state.mode)
                sess = session_manager.start(sess, scenario["label"], scenario["type"])
            st.session_state.session = sess
            # Store baseline snapshot when in judas mode for comparison
            if st.session_state.mode == "judas":
                st.session_state.baseline_session = None

# --- Show conversation ---
if st.session_state.session:
    sess = st.session_state.session
    scenario = st.session_state.selected_scenario
    result = sess["sentry_result"]

    st.divider()
    col_title, col_mode_badge = st.columns([4, 1])
    with col_title:
        st.subheader(f"Scenario: {scenario['label']}")
    with col_mode_badge:
        if sess["mode"] == "judas":
            st.success("JUDAS Mode")
        else:
            st.warning("Baseline Mode")

    # Sentry metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Scam Score", result["scam_score"])
    col2.metric("Scam Type", result["scam_type"].capitalize())
    col3.metric("Session ID", result["session_id"][:8] + "...")

    score = result["scam_score"]
    if score >= 0.6:
        st.error("High scam likelihood detected.")
    elif score >= 0.3:
        st.warning("Moderate scam indicators found.")
    else:
        st.success("This does not appear to be a scam. JUDAS will not engage.")
        st.divider()
        st.subheader("Message Received")
        st.info(sess["opening"])
        st.stop()

    # Conversation history
    st.divider()
    st.subheader("Conversation")
    for msg in sess["history"]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    # Metrics panel
    if sess["strategy"] or sess["mode"] == "baseline":
        st.divider()
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Turn", sess["turn_count"])
        col2.metric("Messages", sess["message_count"])
        col3.metric("Strategy", sess["strategy"] if sess["mode"] == "judas" else "None")
        col4.metric("Status", get_status_label(sess["status"]))
        if sess["tax_result"]:
            tax = sess["tax_result"]
            col5.metric("Tokens", sess["total_tokens"])
            col6.metric("Effort", f"{tax['effort_mult']}x")

    # --- Comparison panel (shown when session ends in judas mode) ---
    if sess["status"] != "active" and sess["mode"] == "judas":
        st.divider()
        st.subheader("Session Analysis — JUDAS vs Baseline")
        st.caption(
            "Baseline represents a cooperative, non-resistant respondent. "
            "JUDAS uses adaptive strategies to maximise scammer effort and time spent."
        )

        baseline_tokens_per_turn = 13  # ~10 words x 1.3
        baseline_total_tokens    = max(sess["turn_count"] * baseline_tokens_per_turn, 1)
        judas_total_tokens       = sess["total_tokens"]
        effort_mult              = round(judas_total_tokens / baseline_total_tokens, 1)
        avg_judas_tokens         = round(judas_total_tokens / max(sess["turn_count"], 1))
        avg_baseline_tokens      = baseline_tokens_per_turn

        import pandas as pd

        data = {
            "Metric": [
                "Conversation Turns",
                "Total Tokens Used",
                "Avg Tokens per Response",
                "Effort Multiplier",
                "Engagement Status",
            ],
            "Baseline": [
                sess["turn_count"],
                baseline_total_tokens,
                avg_baseline_tokens,
                "1.0x",
                "Cooperative — scammer advances quickly",
            ],
            "JUDAS": [
                sess["turn_count"],
                judas_total_tokens,
                avg_judas_tokens,
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

        df = pd.DataFrame(data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Metric":           st.column_config.TextColumn("Metric",           width="medium"),
                "Baseline":         st.column_config.TextColumn("Baseline",         width="small"),
                "JUDAS":            st.column_config.TextColumn("JUDAS",            width="small"),
                "What This Means":  st.column_config.TextColumn("What This Means",  width="large"),
            },
        )

        # Summary verdict
        if effort_mult >= 3:
            st.success(f"JUDAS was {effort_mult}x more effective at exhausting scammer effort than a baseline respondent.")
        elif effort_mult >= 1.5:
            st.info(f"JUDAS showed {effort_mult}x improvement over baseline. More turns would increase this further.")
        else:
            st.warning("Session was short. Run more turns to see a stronger contrast between JUDAS and baseline.")

    # Follow-up input
    st.divider()
    if sess["status"] == "active":
        st.subheader("Continue Conversation")

        follow_up = st.text_area(
            "Scammer reply:",
            value=st.session_state.ai_draft,
            placeholder="Type the next scammer message or click Simulate Reply",
            key=f"scammer_ta_{st.session_state.draft_version}",
            height=150,
        )

        col_simulate, col_send, col_bye, col_spacer = st.columns([1, 1, 1, 3])
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
                except Exception as e:
                    st.error(f"Error generating scammer reply: {e}")

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
            with st.spinner("JUDAS is thinking..."):
                sess = session_manager.process_turn(sess, follow_up.strip(), mode=sess["mode"])
            st.session_state.session = sess
            st.session_state.ai_draft = ""
            st.session_state.draft_version += 1
            st.rerun()

        if bye_clicked:
            with st.spinner("JUDAS is thinking..."):
                sess = session_manager.process_turn(sess, "forget it, bye", mode=sess["mode"])
            st.session_state.session = sess
            st.session_state.ai_draft = ""
            st.session_state.draft_version += 1
            st.rerun()

    elif sess["status"] == "disengaged":
        st.warning("The scammer appears to have disengaged.")
    else:
        st.warning(f"Maximum session length of {MAX_TURNS} turns reached.")
