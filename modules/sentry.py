"""
sentry.py
---------
Scam detection module. Analyses incoming text for fraud indicators using
weighted keyword scoring across four signal categories, then returns a
composite scam score and a classified scam type.

Design: fully heuristic — no ML model required. Fast, transparent, and
explainable. Intended for known-format scam scenarios; novel or subtle
scams may score lower than expected.

Used by: session_manager.start() — runs on the opening message of every session
         main.py — displays scam_score (as %), scam_type, and Detection Confidence badge
"""

import re
import uuid

# ---------------------------------------------------------------------------
# Keyword lists per scam category
# Each list is a representative (not exhaustive) set of signals.
# Scoring is fraction-based: hits / total keywords in the list.
# ---------------------------------------------------------------------------

PHISHING_KEYWORDS = [
    "verify", "account", "suspended", "click here", "login",
    "password", "credentials", "update your", "confirm your", "bank"
]

CRYPTO_KEYWORDS = [
    "bitcoin", "crypto", "wallet", "investment", "guaranteed",
    "return", "double", "binance", "ethereum", "token",
    "withdraw", "profit", "passive income", "risk free",
    "get rich", "financial freedom", "trading bot", "multiply",
    "investor", "returns", "ground floor", "limited opportunity",
    "projected", "disrupt", "per annum", "investment specialist",
    "exclusive offer", "high returns", "substantial returns",
    "unique opportunity", "discerning investor", "portfolio"
]

IMPERSONATION_KEYWORDS = [
    "irs", "microsoft", "amazon", "paypal", "government",
    "social security", "tech support", "refund", "arrest warrant", "officer"
]

URGENCY_KEYWORDS = [
    "urgent", "immediately", "act now", "limited time", "expire",
    "24 hours", "final notice", "last chance", "warning",
    "guaranteed", "100%", "200%", "risk-free", "no risk", "instant"
]

# Detects any URL-like pattern — presence of a link adds to the scam score
URL_PATTERN = re.compile(
    r"(https?://[^\s]+|www\.[^\s]+|bit\.ly/[^\s]+|tinyurl[^\s]*)",
    re.IGNORECASE
)


def _keyword_score(text: str, keywords: list) -> float:
    """
    Return the fraction of keywords from the given list found in text.

    A score of 1.0 means every keyword was present; 0.0 means none were.
    Used as a normalised sub-score for each scam category.

    Args:
        text    : input text to scan (will be lower-cased internally)
        keywords: list of keyword strings to check for

    Returns:
        float between 0.0 and 1.0

    Called by: analyze(), _detect_scam_type() — internal use only
    """
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw in text_lower)
    return hits / len(keywords)


def _detect_scam_type(text: str) -> str:
    """
    Classify the dominant scam type based on keyword scoring.

    Runs _keyword_score for phishing, crypto, and impersonation categories,
    then returns the category with the highest score. Returns "unknown" if
    no category scores above zero.

    Args:
        text: input message to classify

    Returns:
        one of "phishing", "crypto", "impersonation", or "unknown"

    Called by: analyze() — internal use only
    """
    scores = {
        "phishing":      _keyword_score(text, PHISHING_KEYWORDS),
        "crypto":        _keyword_score(text, CRYPTO_KEYWORDS),
        "impersonation": _keyword_score(text, IMPERSONATION_KEYWORDS),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def analyze(text: str) -> dict:
    """
    Analyse input text for scam indicators and return a scored result.

    Computes a weighted composite scam score from five sub-scores:
      - Phishing keywords   (weight 0.25)
      - Crypto keywords     (weight 0.25)
      - Impersonation words (weight 0.20)
      - Urgency signals     (weight 0.20)
      - URL presence        (weight 0.10)

    The raw weighted sum is scaled by 5 and clamped to [0.0, 1.0] to
    amplify sensitivity at low keyword densities (short messages).

    Args:
        text: the opening scam message to evaluate

    Returns:
        dict with:
          scam_score  — float 0–1, heuristic fraud confidence
          scam_type   — "phishing" / "crypto" / "impersonation" / "unknown"
          session_id  — unique UUID for this analysis run

    Called by: session_manager.start()
               Result stored in session["sentry_result"] and read by main.py
               for the Scam Score %, Scam Type, and Detection Confidence badge
    """
    # Compute sub-scores for each signal category
    phishing_s      = _keyword_score(text, PHISHING_KEYWORDS)
    crypto_s        = _keyword_score(text, CRYPTO_KEYWORDS)
    impersonation_s = _keyword_score(text, IMPERSONATION_KEYWORDS)
    urgency_s       = _keyword_score(text, URGENCY_KEYWORDS)
    url_found       = 1.0 if URL_PATTERN.search(text) else 0.0

    # Weighted composite — multiply by 5 to amplify sparse signals
    raw_score = (
        phishing_s      * 0.25 +
        crypto_s        * 0.25 +
        impersonation_s * 0.20 +
        urgency_s       * 0.20 +
        url_found       * 0.10
    )

    # Clamp to [0.0, 1.0]
    scam_score = min(round(raw_score * 5, 2), 1.0)

    return {
        "scam_score": scam_score,
        "scam_type":  _detect_scam_type(text),
        "session_id": str(uuid.uuid4()),
    }
