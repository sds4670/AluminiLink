SPAM_KEYWORDS = [
    "click here", "buy now", "free money",
    "guaranteed", "winner", "congratulations you",
    "limited offer", "act now", "make money fast"
]


def moderate_post(content: str) -> dict:
    """
    4-layer moderation pipeline, evaluated in order:
      1. length check       -> hard reject
      2. spam keyword check -> hard reject
      3. toxicity check     -> hard reject if toxicity > 0.7
      4. admin review       -> flagged for manual review if 0.4 < toxicity <= 0.7
    """
    scores = {}

    # Layer 1 — length check
    word_count = len(content.split())
    if word_count < 5:
        return {
            "approved": False,
            "layer_failed": "length_check",
            "toxicity_score": 0.0,
            "reason": "Post too short — minimum 5 words"
        }

    # Layer 2 — spam keyword check
    content_lower = content.lower()
    spam_hits = sum(1 for k in SPAM_KEYWORDS if k in content_lower)
    if spam_hits >= 2:
        return {
            "approved": False,
            "layer_failed": "spam_check",
            "toxicity_score": 0.0,
            "reason": "Post flagged as spam"
        }

    # Layer 3 — toxicity detection (Detoxify)
    # Lazy import to avoid startup crash if the model/weights aren't available.
    try:
        from detoxify import Detoxify
        results = Detoxify("original").predict(content)
        toxicity = results["toxicity"]
    except Exception:
        toxicity = 0.0

    if toxicity > 0.7:
        return {
            "approved": False,
            "layer_failed": "toxicity_check",
            "toxicity_score": round(toxicity, 3),
            "reason": "Post contains toxic content"
        }

    # Layer 4 — admin review for borderline
    if toxicity > 0.4:
        return {
            "approved": False,
            "layer_failed": "admin_review",
            "toxicity_score": round(toxicity, 3),
            "reason": "Post flagged for admin review"
        }

    return {
        "approved": True,
        "layer_failed": None,
        "toxicity_score": round(toxicity, 3),
        "reason": None
    }
