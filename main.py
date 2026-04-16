import json
import streamlit as st
from config import GROQ_API_KEY, GROQ_MODEL, MAX_TURNS
from modules.sentry import analyze
from modules.brain import respond

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
if "brain_response" not in st.session_state:
    st.session_state.brain_response = None

# --- Scenario buttons ---
st.subheader("Select a Scam Scenario")
cols = st.columns(len(scenarios))

for i, scenario in enumerate(scenarios):
    with cols[i]:
        if st.button(scenario["label"], key=scenario["id"]):
            st.session_state.selected_scenario = scenario
            st.session_state.sentry_result = analyze(scenario["opening"])
            # Build initial history and get Brain response
            history = [{"role": "user", "content": scenario["opening"]}]
            with st.spinner("JUDAS is thinking..."):
                st.session_state.brain_response = respond(history)

# --- Show selected scenario + results ---
if st.session_state.selected_scenario:
    st.divider()
    scenario = st.session_state.selected_scenario
    result = st.session_state.sentry_result

    st.subheader(f"Scenario: {scenario['label']}")
    st.info(scenario["opening"])

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
        st.success("Low scam indicators.")

    # Brain response
    st.divider()
    st.subheader("JUDAS Response")
    if st.session_state.brain_response:
        st.success(st.session_state.brain_response)
