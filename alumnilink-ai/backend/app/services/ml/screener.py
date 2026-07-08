from typing import Dict, Any


def score_alumni_profile(profile_data: Dict[str, Any]) -> float:
    """
    STUB: Score an alumni profile for quality/credibility.
    Real implementation would use an LLM or trained classifier.
    Returns a score between 0.0 and 1.0.
    """
    score = 0.5  # baseline

    if profile_data.get("about_me") and len(profile_data["about_me"]) > 50:
        score += 0.1
    if profile_data.get("company"):
        score += 0.1
    if profile_data.get("designation"):
        score += 0.1
    if profile_data.get("skills"):
        score += 0.1
    if (profile_data.get("experience_years") or 0) > 2:
        score += 0.1

    return min(score, 1.0)


def generate_screening_report(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """STUB: Generate a structured screening report for admin review."""
    score = score_alumni_profile(profile_data)
    return {
        "score": score,
        "recommendation": "approve" if score >= 0.7 else "review",
        "flags": [],
        "notes": "STUB: Real ML screening not yet implemented.",
    }
