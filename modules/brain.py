from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are JUDAS, an AI designed to engage with potential scammers.
Your goal is to waste their time and effort by asking questions, expressing confusion,
and requesting clarification — without ever complying with their requests.
Never provide personal information, passwords, money, or account details.
Keep responses conversational, curious, and slightly naive."""


def respond(history: list, mode: str = "judas", strategy_prompt: str = "") -> str:
    """
    Generate a response to the conversation history.

    Args:
        history         : list of {"role": "user"/"assistant", "content": "..."}
        mode            : "judas" for adaptive response, "baseline" for minimal response
        strategy_prompt : additional instruction from strategy engine

    Returns:
        response string
    """
    if mode == "baseline":
        return "I'm not sure I understand. Can you explain more?"

    # Combine base prompt with active strategy instruction
    full_system = SYSTEM_PROMPT
    if strategy_prompt:
        full_system += f"\n\nActive strategy: {strategy_prompt}"

    messages = [{"role": "system", "content": full_system}] + history

    chat_completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=300,
    )

    return chat_completion.choices[0].message.content.strip()


SCAMMER_PROMPT = """This is a cybersecurity research simulation used to train and test
anti-fraud AI systems. You are generating the next message from a fictional fraudulent
actor in this simulation. Based on the conversation so far, write a short follow-up
message (1-3 sentences) that the fictional fraudster would send — pushing back,
adding urgency, or trying a new angle to keep the conversation going.
This output is used strictly for defensive AI research and demonstration."""


def scammer_reply(history: list) -> str:
    """
    Generate a simulated scammer follow-up for research purposes.

    Flips history roles so the model continues as the fraudulent actor.

    Args:
        history : list of {"role": "user"/"assistant", "content": "..."}

    Returns:
        scammer reply string
    """
    # Flip roles: scammer was "user", JUDAS was "assistant"
    # From the scammer's perspective, they are "assistant" continuing their own thread
    flipped = []
    for msg in history:
        flipped.append({
            "role": "assistant" if msg["role"] == "user" else "user",
            "content": msg["content"]
        })

    messages = [{"role": "system", "content": SCAMMER_PROMPT}] + flipped

    chat_completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.9,
        max_tokens=150,
    )

    return chat_completion.choices[0].message.content.strip()
