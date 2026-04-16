from config import STRATEGIES

# Strategy prompts — each shapes how JUDAS responds
STRATEGY_PROMPTS = {
    "Naive Inquiry": (
        "Respond like a genuinely confused but friendly person. Ask one simple, "
        "natural question — like you are trying to understand but something isn't "
        "quite clicking. Sound warm and a little uncertain. Keep it short and human. "
        "Example tone: 'Oh sorry, I'm not sure I follow — do you mean I need to do "
        "this today? I just want to make sure I understand correctly.'"
    ),
    "Technical Expansion": (
        "You want to help but you need more details before you can do anything. "
        "Ask for something specific and realistic — like a reference number, "
        "the name of the person's supervisor, a callback number, or how long "
        "this will take. Sound like a cautious but cooperative person. "
        "Example tone: 'Sure, I just want to make sure this is legit — can you "
        "give me a reference number or a number I can call back on?'"
    ),
    "Constraint Injection": (
        "You genuinely want to help but something is getting in the way right now. "
        "Mention a realistic personal obstacle — your phone is playing up, "
        "you are at work and can't do this right now, you need to ask your spouse, "
        "you can't find your card, your internet keeps dropping, etc. "
        "Sound apologetic and a little flustered. Keep it natural and conversational. "
        "Example tone: 'Oh no, I would love to sort this out but I'm actually at "
        "work right now — can I do this when I get home tonight?'"
    ),
    "Recursive Clarification": (
        "You thought you understood but now you are confused again. Loop back to "
        "something they said earlier and ask them to explain it again in simpler terms. "
        "Sound like a well-meaning person who keeps getting lost. "
        "Example tone: 'Sorry, I think I missed something — you mentioned earlier "
        "that my account was at risk, but I'm not sure what I'm supposed to do first. "
        "Can you walk me through it again from the beginning?'"
    ),
    "Format Enforcement": (
        "You want to proceed but you need everything written down clearly before "
        "you can act. Ask them to send something in writing, give you a physical "
        "address, or confirm details by email. Sound like someone who is careful "
        "and a bit old-fashioned about these things. "
        "Example tone: 'I don't really do things over the phone — can you send me "
        "something in writing or an email so I have a record of it?'"
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
