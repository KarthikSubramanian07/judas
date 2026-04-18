"""
taximeter.py
------------
Estimates token usage and cost for a JUDAS or Baseline response, and
calculates an effort multiplier relative to a minimal cooperative reply.

The "taximeter" metaphor: like a taxi meter, it measures how much resource
cost each JUDAS response imposes on the scammer — the more they have to
read and process, the higher the meter runs.

Token estimation is word-count based (words × TOKENS_PER_WORD) rather than
using a tokeniser, which keeps the module lightweight and dependency-free.

Used by: session_manager.process_turn() — called on every reply to update
         session["tax_result"] and accumulate session["total_tokens"]
         main.py — effort_mult and token counts shown in Session Metrics box
                   and Session Analysis comparison table
"""

from config import TOKENS_PER_WORD, PRICING

# Approximate word count of a brief, cooperative baseline response
# ("Sure, sounds good. What do I need to do?" ≈ 10 words)
BASELINE_WORD_COUNT = 10


def estimate(text: str) -> dict:
    """
    Estimate token usage, cost tiers, and effort multiplier for a response.

    Token count is approximated as: word_count × TOKENS_PER_WORD (1.3).
    Cost is calculated at three price tiers (low / mid / high) defined in
    config.PRICING to cover different LLM pricing bands.

    Effort multiplier measures how much longer this response is compared to
    a minimal baseline reply (BASELINE_WORD_COUNT words). An effort_mult of
    5.0 means the scammer had to read and process 5× more text than a
    cooperative target would have generated.

    Note: This per-turn effort_mult is not the same as the session-level
    Effort Multiplier shown in the UI. The session-level figure in main.py
    uses session["total_tokens"] ÷ (turns × BASELINE_TOKENS_PER_TURN) for
    a cumulative view across the whole conversation.

    Args:
        text: the response string (JUDAS reply or Baseline reply)

    Returns:
        dict with:
          tokens      — estimated token count (int)
          cost_low    — low-tier cost in USD (float)
          cost_mid    — mid-tier cost in USD (float)
          cost_high   — high-tier cost in USD (float)
          effort_mult — ratio of this response's tokens to baseline tokens (float)

    Called by: session_manager.process_turn()
    """
    word_count = len(text.split())
    tokens = round(word_count * TOKENS_PER_WORD)

    cost_low  = round(tokens * PRICING["low"],  6)
    cost_mid  = round(tokens * PRICING["mid"],  6)
    cost_high = round(tokens * PRICING["high"], 6)

    # Per-turn effort multiplier vs a minimal one-liner baseline
    baseline_tokens = round(BASELINE_WORD_COUNT * TOKENS_PER_WORD)
    effort_mult = round(tokens / baseline_tokens, 2)

    return {
        "tokens":      tokens,
        "cost_low":    cost_low,
        "cost_mid":    cost_mid,
        "cost_high":   cost_high,
        "effort_mult": effort_mult,
    }
