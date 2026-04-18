"""
session_manager.py
------------------
Manages the full lifecycle of a JUDAS or Baseline conversation session.

A session is a plain dict that carries all state for one conversation:
history, turn count, status, sentry result, strategy, token totals, etc.
All functions take a session dict and return an updated copy — no global
state is held here.

Lifecycle:
  1. new_session()   — create a blank session dict
  2. start()         — generate opening scam message, run sentry, take first turn
  3. process_turn()  — handle one scammer message → reply → update metrics

Used by: main.py (two-phase loading block calls new_session + start;
         Send/Bye button handlers call process_turn)
"""

import uuid
from modules.sentry import analyze
from modules.brain import respond, generate_opening
from modules.strategy_engine import select as select_strategy, get_prompt
from modules.taximeter import estimate
from modules import engagement_tracker


def new_session(mode: str = "judas") -> dict:
    """
    Create and return a fresh, empty session state dictionary.

    All keys are initialised to safe defaults. The session dict is the
    single source of truth passed between all modules during a conversation.

    Args:
        mode: "judas" for adversarial mode, "baseline" for cooperative mode

    Returns:
        session dict with zeroed counters and None placeholders

    Called by: main.py — two-phase scenario loading block (pending_scenario handler)
    """
    return {
        "session_id":    str(uuid.uuid4()),
        "history":       [],        # list of {"role": "user"/"assistant", "content": "..."}
        "turn_count":    0,
        "message_count": 0,
        "status":        "active",  # active | disengaged | max_turns_reached
        "strategy":      None,      # active strategy name (JUDAS mode only)
        "sentry_result": None,      # dict from sentry.analyze()
        "tax_result":    None,      # dict from taximeter.estimate()
        "opening":       None,      # AI-generated opening scam message
        "mode":          mode,
        "total_tokens":  0,         # cumulative token count across all turns
    }


def start(session: dict, label: str, scenario_type: str) -> dict:
    """
    Initialise a session with a generated opening message and run the first turn.

    Steps:
      1. Calls brain.generate_opening() to create a fresh, AI-generated scam
         (or normal) opening message — no hardcoded scripts.
      2. Runs sentry.analyze() on the opening to produce scam_score, scam_type,
         and Detection Confidence (used by main.py for the badge display).
      3. If the scenario is a known scam type, or the sentry score is ≥ 0.3,
         calls process_turn() to generate the first JUDAS/Baseline response.
         Normal scenarios with low sentry scores are shown but not engaged with.

    Args:
        session       : blank session dict from new_session()
        label         : scenario label e.g. "Tech Support Scam"
        scenario_type : "scam" or "normal"

    Returns:
        session dict populated with opening, sentry_result, and first turn

    Called by: main.py — two-phase scenario loading block (pending_scenario handler)
    """
    opening = generate_opening(label, scenario_type)
    session["opening"]        = opening
    session["scenario_type"]  = scenario_type
    session["sentry_result"]  = analyze(opening)

    # For known scam scenarios, always engage regardless of sentry score.
    # Sentry is designed for unknown inputs — here we already know the type.
    should_engage = (scenario_type == "scam") or (session["sentry_result"]["scam_score"] >= 0.3)
    if should_engage:
        session = process_turn(session, opening, mode=session["mode"])

    return session


def process_turn(session: dict, user_message: str, mode: str = "judas") -> dict:
    """
    Process one full conversation turn: receive scammer message → reply → update state.

    Steps:
      1. Appends the scammer's message to history as a "user" turn.
      2. Calls strategy_engine.select() to determine the current strategy
         (JUDAS mode only; strategy selection is still called in baseline mode
         but the prompt is not passed to brain.respond() in that path).
      3. Calls brain.respond() with the full history and strategy prompt to
         generate JUDAS's or Baseline's reply.
      4. Appends the reply to history as an "assistant" turn.
      5. Calls taximeter.estimate() to count tokens and update total_tokens.
      6. Calls engagement_tracker.update() to increment counters and check
         for disengagement or session cap.

    Args:
        session      : current session dict
        user_message : the scammer's message for this turn
        mode         : "judas" or "baseline" — passed through to brain.respond()

    Returns:
        updated session dict

    Called by:
        start()    — for the initial turn on the opening message
        main.py    — Send button handler (follow-up scammer message)
        main.py    — Bye button handler ("okay, thank you, goodbye" or "forget it, bye")
    """
    session["history"].append({"role": "user", "content": user_message})

    # Select strategy based on current turn number (1-based, so +1 before updating counter)
    strategy = select_strategy(
        turn=session["turn_count"] + 1,
        scam_type=session["sentry_result"]["scam_type"],
        last_strategy=session["strategy"],
    )
    session["strategy"] = strategy

    # Generate reply — strategy prompt is included for JUDAS mode; ignored in baseline
    reply = respond(
        session["history"],
        mode=mode,
        strategy_prompt=get_prompt(strategy),
    )

    session["history"].append({"role": "assistant", "content": reply})

    # Estimate tokens for this reply and add to running total
    session["tax_result"]   = estimate(reply)
    session["total_tokens"] = session.get("total_tokens", 0) + session["tax_result"]["tokens"]

    # Update turn counter and check for disengagement or session cap
    session = engagement_tracker.update(session, user_message, reply)

    return session
