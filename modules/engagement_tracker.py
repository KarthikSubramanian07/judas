"""
engagement_tracker.py
---------------------
Tracks conversation progress and determines session status after each turn.

Responsibilities:
- Increments turn and message counters
- Detects when the scammer appears to be disengaging (based on keywords)
- Enforces the MAX_TURNS session limit
- Provides a human-readable label for each status code

Used by: session_manager.process_turn()
         main.py (get_status_label for metrics display and comparison table)
"""

from config import MAX_TURNS


def update(session: dict, new_user_message: str, new_reply: str) -> dict:
    """
    Update engagement metrics after each conversation turn.

    Increments turn_count and message_count, then evaluates whether the
    session should remain active, be marked as disengaged (scammer gave up),
    or capped at MAX_TURNS.

    Args:
        session         : current session dict (modified in place and returned)
        new_user_message: the scammer's message this turn — checked for disengagement signals
        new_reply       : JUDAS/Baseline response this turn (unused here, reserved for future scoring)

    Returns:
        updated session dict

    Called by: session_manager.process_turn()
    """
    session["turn_count"]    = session.get("turn_count", 0) + 1
    session["message_count"] = session.get("message_count", 0) + 2  # one user + one assistant message

    # Check exit conditions in priority order: cap first, then disengagement
    if session["turn_count"] >= MAX_TURNS:
        session["status"] = "max_turns_reached"
    elif _is_disengaging(new_user_message):
        session["status"] = "disengaged"
    else:
        session["status"] = "active"

    return session


def _is_disengaging(text: str) -> bool:
    """
    Detect whether the scammer's message contains disengagement signals.

    Checks for common phrases a frustrated scammer might use when giving up
    (e.g. "forget it", "bye", "waste of time"). Case-insensitive substring match.

    Args:
        text: the scammer's latest message

    Returns:
        True if the message suggests the scammer is abandoning the conversation

    Called by: update() — internal use only
    """
    disengage_signals = [
        "forget it", "never mind", "stop", "bye", "goodbye",
        "leave me alone", "not interested", "go away", "done",
        "this is pointless", "waste of time"
    ]
    text_lower = text.lower()
    return any(signal in text_lower for signal in disengage_signals)


def get_status_label(status: str) -> str:
    """
    Convert an internal status code to a human-readable display string.

    Args:
        status: one of "active", "disengaged", "max_turns_reached"

    Returns:
        Display string for use in the UI metrics and comparison table

    Called by: main.py — Session Metrics box, comparison table Engagement Status row
    """
    labels = {
        "active":            "Active",
        "disengaged":        "Disengaged",
        "max_turns_reached": "Max Turns Reached",
    }
    return labels.get(status, "Unknown")
