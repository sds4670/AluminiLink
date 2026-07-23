SPAM_KEYWORDS = [
    "click here", "buy now", "free money",
    "guaranteed", "winner", "congratulations you",
    "limited offer", "act now", "make money fast"
]

# Lazy-loaded singleton so requests never pay reload cost; stays None (and
# every call falls back to toxicity=0.0) if the model can't load in this
# environment. detoxify==0.5.1 was tried first and is a dead end (see
# PROGRESS.md Day 4 — hard-pins transformers==4.22.1, which conflicts with
# the transformers==4.30.2 this project needs for SBERT matching); toxic-bert
# is loaded directly via the already-installed `transformers` lib instead.
_toxicity_pipeline = None
_toxicity_load_failed = False


def _get_toxicity_pipeline():
    global _toxicity_pipeline, _toxicity_load_failed
    if _toxicity_pipeline is None and not _toxicity_load_failed:
        try:
            from transformers import pipeline
            _toxicity_pipeline = pipeline(
                "text-classification", model="unitary/toxic-bert", top_k=None
            )
        except Exception:
            _toxicity_load_failed = True
    return _toxicity_pipeline


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

    # Layer 3 — toxicity detection (unitary/toxic-bert)
    try:
        pipeline = _get_toxicity_pipeline()
        if pipeline is None:
            toxicity = 0.0
        else:
            label_scores = pipeline(content)[0]
            toxicity = next(s["score"] for s in label_scores if s["label"] == "toxic")
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
