import json
import streamlit as st
from config import GROQ_API_KEY, GROQ_MODEL, MAX_TURNS
from modules.sentry import analyze
from modules.brain import respond, scammer_reply, generate_opening
from modules.taximeter import estimate
from modules.strategy_engine import select as select_strategy, get_prompt

st.set_page_config(page_title="JUDAS", layout="wide")

st.title("JUDAS — Adversarial Fraud Disruptor")
st.caption("Detect. Engage. Exhaust.")

st.divider()

# --- Load scenarios ---
with open("data/scenarios.json") as f:
    scenarios = json.load(f)

# --- Session state ---
if "selected_scenario" not in st.session_state:
    st.session_state.selected_scenario = None
if "sentry_result" not in st.session_state:
    st.session_state.sentry_result = None
if "strategy" not in st.session_state:
    st.session_state.strategy = None
if "turn" not in st.session_state:
    st.session_state.turn = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "tax_result" not in st.session_state:
    st.session_state.tax_result = None
if "ai_draft" not in st.session_state:
    st.session_state.ai_draft = ""
if "draft_version" not in st.session_state:
    st.session_state.draft_version = 0
if "generated_opening" not in st.session_state:
    st.session_state.generated_opening = ""


def run_turn(user_message: str):
    """Process one conversation turn end-to-end."""
    st.session_state.turn += 1
    st.session_state.history.append({"role": "user", "content": user_message})

    scam_type = st.session_state.sentry_result["scam_type"]
    strategy = select_strategy(
        turn=st.session_state.turn,
        scam_type=scam_type,
        last_strategy=st.session_state.strategy,
    )
    st.session_state.strategy = strategy

    with st.spinner("JUDAS is thinking..."):
        reply = respond(
            st.session_state.history,
            strategy_prompt=get_prompt(strategy),
        )

    st.session_state.history.append({"role": "assistant", "content": reply})
    st.session_state.tax_result = estimate(reply)


# --- Scenario buttons ---
st.subheader("Select a Scenario")
cols = st.columns(len(scenarios))

for i, scenario in enumerate(scenarios):
    with cols[i]:
        if st.button(scenario["label"], key=scenario["id"]):
            st.session_state.selected_scenario = scenario
            st.session_state.history = []
            st.session_state.turn = 0
            st.session_state.strategy = None
            st.session_state.tax_result = None
            st.session_state.ai_draft = ""
            st.session_state.draft_version = 0
            with st.spinner(f"Generating '{scenario['label']}' scenario..."):
                opening = generate_opening(scenario["label"], scenario["type"])
            st.session_state.generated_opening = opening
            sentry = analyze(opening)
            st.session_state.sentry_result = sentry
            if sentry["scam_score"] >= 0.3:
                run_turn(opening)

# --- Show conversation ---
if st.session_state.selected_scenario:
    st.divider()
    scenario = st.session_state.selected_scenario
    result = st.session_state.sentry_result

    st.subheader(f"Scenario: {scenario['label']}")

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
        st.info(st.session_state.generated_opening)
        st.stop()

    # Conversation history
    st.divider()
    st.subheader("Conversation")
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    # Strategy + taximeter
    if st.session_state.strategy:
        st.divider()
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Turn", st.session_state.turn)
        col2.metric("Strategy", st.session_state.strategy)
        if st.session_state.tax_result:
            tax = st.session_state.tax_result
            col3.metric("Tokens", tax["tokens"])
            col4.metric("Cost Mid", f"${tax['cost_mid']:.6f}")
            col5.metric("Effort", f"{tax['effort_mult']}x")

    # Follow-up input
    st.divider()
    if st.session_state.turn < MAX_TURNS:
        st.subheader("Continue Conversation")

        follow_up = st.text_area(
            "Scammer reply:",
            value=st.session_state.ai_draft,
            placeholder="Type the next scammer message or click Simulate Reply",
            key=f"scammer_ta_{st.session_state.draft_version}",
            height=150,
        )

        col_simulate, col_send, col_spacer = st.columns([1, 1, 4])
        with col_simulate:
            if st.button(
                "Simulate Reply",
                key=f"ai_btn_{st.session_state.turn}",
                use_container_width=True,
                help="Let AI generate a realistic follow-up scammer message",
            ):
                try:
                    with st.spinner("Generating scammer reply..."):
                        draft = scammer_reply(st.session_state.history)
                    st.session_state.ai_draft = draft
                    st.session_state.draft_version += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating scammer reply: {e}")

        with col_send:
            send_clicked = st.button("Send", key=f"send_turn_{st.session_state.turn}", use_container_width=True)

        if send_clicked:
            if follow_up.strip():
                st.session_state.ai_draft = ""
                st.session_state.draft_version += 1
                run_turn(follow_up.strip())
                st.rerun()
    else:
        st.warning(f"Maximum session length of {MAX_TURNS} turns reached.")
