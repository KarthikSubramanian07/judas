import re
import uuid

# --- Keyword lists per scam type ---
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

URL_PATTERN = re.compile(
    r"(https?://[^\s]+|www\.[^\s]+|bit\.ly/[^\s]+|tinyurl[^\s]*)",
    re.IGNORECASE
)


def _keyword_score(text: str, keywords: list) -> float:
    """Return fraction of keywords found in text."""
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw in text_lower)
    return hits / len(keywords)


def _detect_scam_type(text: str) -> str:
    scores = {
        "phishing":      _keyword_score(text, PHISHING_KEYWORDS),
        "crypto":        _keyword_score(text, CRYPTO_KEYWORDS),
        "impersonation": _keyword_score(text, IMPERSONATION_KEYWORDS),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def analyze(text: str) -> dict:
    """
    Analyze input text for scam indicators.

    Returns:
        scam_score  : float 0-1, heuristic confidence
        scam_type   : phishing / crypto / impersonation / unknown
        session_id  : unique session identifier
    """
    text_lower = text.lower()

    # Component scores
    phishing_s      = _keyword_score(text, PHISHING_KEYWORDS)
    crypto_s        = _keyword_score(text, CRYPTO_KEYWORDS)
    impersonation_s = _keyword_score(text, IMPERSONATION_KEYWORDS)
    urgency_s       = _keyword_score(text, URGENCY_KEYWORDS)
    url_found       = 1.0 if URL_PATTERN.search(text) else 0.0

    # Weighted composite score
    raw_score = (
        phishing_s      * 0.25 +
        crypto_s        * 0.25 +
        impersonation_s * 0.20 +
        urgency_s       * 0.20 +
        url_found       * 0.10
    )

    # Clamp to 0-1
    scam_score = min(round(raw_score * 5, 2), 1.0)

    return {
        "scam_score": scam_score,
        "scam_type":  _detect_scam_type(text),
        "session_id": str(uuid.uuid4()),
    }
