from typing import Dict, Any

BLOCKED_KEYWORDS = ["spam", "scam", "offensive_placeholder"]


def moderate_post(content: str) -> Dict[str, Any]:
    """
    STUB: Moderate post content for policy violations.
    Real implementation would use an LLM or content moderation API.
    Returns a dict with score and decision.
    """
    content_lower = content.lower()
    flagged = any(kw in content_lower for kw in BLOCKED_KEYWORDS)
    score = 0.95 if not flagged else 0.2

    return {
        "score": score,
        "decision": "rejected" if flagged else "approved",
        "reasons": ["blocked keyword detected"] if flagged else [],
        "auto_actioned": True,
    }


def is_safe_content(content: str) -> bool:
    """STUB: Quick safety check for content."""
    result = moderate_post(content)
    return result["decision"] == "approved"
