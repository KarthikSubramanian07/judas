from config import TOKENS_PER_WORD, PRICING

# Baseline: a minimal one-line response word count
BASELINE_WORD_COUNT = 10


def estimate(text: str) -> dict:
    """
    Estimate token usage and cost for a given response text.

    Args:
        text : response string from Brain

    Returns:
        tokens        : estimated token count
        cost_low      : low-tier cost estimate in USD
        cost_mid      : mid-tier cost estimate in USD
        cost_high     : high-tier cost estimate in USD
        effort_mult   : effort multiplier vs baseline response
    """
    word_count = len(text.split())
    tokens = round(word_count * TOKENS_PER_WORD)

    cost_low  = round(tokens * PRICING["low"],  6)
    cost_mid  = round(tokens * PRICING["mid"],  6)
    cost_high = round(tokens * PRICING["high"], 6)

    # Effort multiplier: how much harder is this vs a baseline one-liner
    baseline_tokens = round(BASELINE_WORD_COUNT * TOKENS_PER_WORD)
    effort_mult = round(tokens / baseline_tokens, 2)

    return {
        "tokens":      tokens,
        "cost_low":    cost_low,
        "cost_mid":    cost_mid,
        "cost_high":   cost_high,
        "effort_mult": effort_mult,
    }
