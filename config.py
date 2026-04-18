"""
config.py
---------
Central configuration for JUDAS. All tuneable constants and environment
variables are defined here so they can be changed in one place without
hunting through module files.

Used by: brain.py, strategy_engine.py, taximeter.py, engagement_tracker.py,
         main.py (BASELINE_TOKENS_PER_TURN, MAX_TURNS, AVAILABLE_MODELS)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

# Loaded from .env file — required for all LLM calls in brain.py
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Default model used by brain._call_api().
# Can be overridden at runtime via brain.GROQ_MODEL_OVERRIDE (set by the
# sidebar model selector in main.py without requiring a restart).
GROQ_MODEL = "llama-3.3-70b-versatile"

# Models available in the sidebar dropdown in main.py.
# Key = display label, value = Groq model ID.
AVAILABLE_MODELS = {
    "Llama 3.3 70B (Best Quality)":   "llama-3.3-70b-versatile",
    "Llama 3.1 8B (Fast / Fallback)": "llama-3.1-8b-instant",
    "Llama 4 Scout 17B":              "meta-llama/llama-4-scout-17b-16e-instruct",
}

# ---------------------------------------------------------------------------
# Strategy Engine
# ---------------------------------------------------------------------------

# Ordered list of the five JUDAS engagement strategies.
# Used by strategy_engine.py (implicitly via STRATEGY_PROMPTS dict keys)
# and displayed in the sidebar strategy expanders in main.py.
STRATEGIES = [
    "Naive Inquiry",
    "Technical Expansion",
    "Constraint Injection",
    "Recursive Clarification",
    "Format Enforcement",
]

# ---------------------------------------------------------------------------
# Taximeter
# ---------------------------------------------------------------------------

# Approximate tokens per word for token count estimation in taximeter.estimate().
# Based on the common rule of thumb: 1 token ≈ 0.75 words → 1 word ≈ 1.3 tokens.
TOKENS_PER_WORD = 1.3

# Average tokens a cooperative (baseline) respondent uses per turn.
# Derived from: ~10 words per reply × 1.3 tokens/word = 13.
# A trusting, brief respondent typically answers in 1-2 short sentences (~10 words).
# Used by main.py as the fallback baseline_per_turn when no actual baseline
# session has been run yet (i.e. before st.session_state.baseline_avg_tokens is set).
BASELINE_TOKENS_PER_TURN = 13

# Token cost tiers in USD per token — used by taximeter.estimate().
# Three tiers cover the range of common LLM API pricing bands.
PRICING = {
    "low":  0.0000010,   # budget models
    "mid":  0.0000030,   # mid-range models
    "high": 0.0000080,   # premium models
}

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

# Maximum number of turns before a session is automatically ended.
# Prevents runaway sessions and keeps demos focused.
# Used by engagement_tracker.update() and referenced in main.py warning message.
MAX_TURNS = 20
