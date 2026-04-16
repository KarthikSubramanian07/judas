import uuid
from modules.sentry import analyze
from modules.brain import respond, generate_opening
from modules.strategy_engine import select as select_strategy, get_prompt
from modules.taximeter import estimate
from modules import engagement_tracker


def new_session() -> dict:
    """Create a fresh session state dict."""
    return {
        "session_id":    str(uuid.uuid4()),
        "history":       [],
        "turn_count":    0,
        "message_count": 0,
        "status":        "active",
        "strategy":      None,
        "sentry_result": None,
        "tax_result":    None,
        "opening":       None,
    }


def start(session: dict, label: str, scenario_type: str) -> dict:
    """
    Generate an opening message and run the first JUDAS turn.

    Args:
        session       : fresh session dict from new_session()
        label         : scenario label e.g. "Fake Investment Offer"
        scenario_type : "scam" or "normal"

    Returns:
        updated session dict
    """
    opening = generate_opening(label, scenario_type)
    session["opening"] = opening
    session["sentry_result"] = analyze(opening)

    # Only engage if scam score is high enough
    if session["sentry_result"]["scam_score"] >= 0.3:
        session = process_turn(session, opening)

    return session


def process_turn(session: dict, user_message: str, mode: str = "judas") -> dict:
    """
    Process one full conversation turn.

    Args:
        session      : current session dict
        user_message : scammer's message this turn
        mode         : "judas" or "baseline"

    Returns:
        updated session dict
    """
    session["history"].append({"role": "user", "content": user_message})

    strategy = select_strategy(
        turn=session["turn_count"] + 1,
        scam_type=session["sentry_result"]["scam_type"],
        last_strategy=session["strategy"],
    )
    session["strategy"] = strategy

    reply = respond(
        session["history"],
        mode=mode,
        strategy_prompt=get_prompt(strategy),
    )

    session["history"].append({"role": "assistant", "content": reply})
    session["tax_result"] = estimate(reply)
    session = engagement_tracker.update(session, user_message, reply)

    return session
