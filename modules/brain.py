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
