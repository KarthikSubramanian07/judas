import os
from dotenv import load_dotenv

load_dotenv()

# --- API ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"  # default — override via UI sidebar

AVAILABLE_MODELS = {
    "Llama 3.3 70B (Best Quality)":  "llama-3.3-70b-versatile",
    "Llama 3.1 8B (Fast / Fallback)": "llama-3.1-8b-instant",
    "Llama 4 Scout 17B":              "meta-llama/llama-4-scout-17b-16e-instruct",
}

# --- Strategy Engine ---
STRATEGIES = [
    "Naive Inquiry",
    "Technical Expansion",
    "Constraint Injection",
    "Recursive Clarification",
    "Format Enforcement",
]

# --- Taximeter ---
TOKENS_PER_WORD = 1.3

# Average tokens a cooperative (baseline) respondent uses per turn.
# Derived from: ~10 words per reply × 1.3 tokens/word = 13.
# A trusting, brief respondent typically answers in 1-2 short sentences (~10 words).
BASELINE_TOKENS_PER_TURN = 13

PRICING = {
    "low":  0.0000010,   # $ per token
    "mid":  0.0000030,
    "high": 0.0000080,
}

# --- Session ---
MAX_TURNS = 20
