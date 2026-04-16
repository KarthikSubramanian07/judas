from config import STRATEGIES

# Strategy prompts — each shapes how JUDAS responds
STRATEGY_PROMPTS = {
    "Naive Inquiry": (
        "You are confused and curious. Ask simple, innocent questions about "
        "what the person means. Act like you genuinely want to understand but "
        "keep getting confused by their explanations."
    ),
    "Technical Expansion": (
        "Ask highly technical and detailed questions. Request specific technical "
        "documentation, serial numbers, official reference codes, or step-by-step "
        "verification procedures before you can proceed."
    ),
    "Constraint Injection": (
        "Introduce personal constraints and complications that prevent you from "
        "complying. You have no access to your account right now, your phone is "
        "broken, you need a family member's permission, your internet is slow, etc."
    ),
    "Recursive Clarification": (
        "Every answer they give raises more questions. Loop back to earlier points "
        "and ask for clarification again. Act like you keep forgetting what they said "
        "and need them to repeat and re-explain everything."
    ),
    "Format Enforcement": (
        "Insist that all information must be provided in a very specific format — "
        "numbered lists, official letterhead, specific form codes, or written "
        "confirmation before you can take any action."
    ),
}


def select(turn: int, scam_type: str, last_strategy: str = None) -> str:
    """
    Select a strategy based on session state.

    Args:
        turn          : current turn number (1-based)
        scam_type     : detected scam type from Sentry
        last_strategy : strategy used in previous turn

    Returns:
        strategy name string
    """
    if turn == 1:
        return "Naive Inquiry"
    elif turn <= 3:
        return "Technical Expansion"
    elif turn <= 5:
        return "Constraint Injection"
    elif turn <= 7:
        return "Recursive Clarification"
    else:
        return "Format Enforcement"


def get_prompt(strategy: str) -> str:
    """Return the system prompt addition for a given strategy."""
    return STRATEGY_PROMPTS.get(strategy, "")
