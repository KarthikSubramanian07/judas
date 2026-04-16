from config import MAX_TURNS


def update(session: dict, new_user_message: str, new_reply: str) -> dict:
    """
    Update engagement metrics after each turn.

    Args:
        session         : current session dict
        new_user_message: the scammer's message this turn
        new_reply       : JUDAS response this turn

    Returns:
        updated session dict with engagement metrics
    """
    session["turn_count"]    = session.get("turn_count", 0) + 1
    session["message_count"] = session.get("message_count", 0) + 2  # user + assistant

    # Detect drop-off conditions
    if session["turn_count"] >= MAX_TURNS:
        session["status"] = "max_turns_reached"
    elif _is_disengaging(new_user_message):
        session["status"] = "disengaged"
    else:
        session["status"] = "active"

    return session


def _is_disengaging(text: str) -> bool:
    """Detect if the scammer appears to be giving up."""
    disengage_signals = [
        "forget it", "never mind", "stop", "bye", "goodbye",
        "leave me alone", "not interested", "go away", "done",
        "this is pointless", "waste of time"
    ]
    text_lower = text.lower()
    return any(signal in text_lower for signal in disengage_signals)


def get_status_label(status: str) -> str:
    labels = {
        "active":           "Active",
        "disengaged":       "Disengaged",
        "max_turns_reached": "Max Turns Reached",
    }
    return labels.get(status, "Unknown")
