import os
from dotenv import load_dotenv

load_dotenv()

# --- API ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

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

PRICING = {
    "low":  0.0000010,   # $ per token
    "mid":  0.0000030,
    "high": 0.0000080,
}

# --- Session ---
MAX_TURNS = 20
