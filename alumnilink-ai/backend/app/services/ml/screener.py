import re
from typing import Dict, Any


def _contains(text: str, phrase: str) -> bool:
    """
    Word-boundary match, not a raw substring check. Plain `phrase in text`
    false-positives badly here: "yo" (meant to catch the greeting "yo") is a
    substring of "your"/"you", so it silently penalised the tone of almost
    every personalised message ("your journey", "you work"); "sup" is a
    substring of "support"/"suppose" the same way.
    """
    return re.search(r"\b" + re.escape(phrase) + r"\b", text) is not None


def screen_message(message: str) -> dict:
    """
    Score an outreach message on 4 dimensions (intent, professional tone,
    personalisation, message quality), each weighted 0.25, for a 0.0-1.0
    composite. Pass threshold = 0.6.

    Calibrated for how students actually write a first message, not a
    templated form letter: one genuine intent word and one genuine
    personalisation phrase now earn full credit on those dimensions (was 3
    and 2 matches respectively), and a sincere ~20-word message no longer
    scores zero on quality (was a 30-word floor). "job" was removed from the
    unprofessional-tone penalty — wanting career/job guidance is the entire
    point of this platform, penalising the word was never correct.
    """
    scores = {}
    message_lower = message.lower()

    # Check 1 — Intent (weight 0.25)
    # Does the message have a clear mentorship ask? One genuine signal is
    # enough — real messages rarely repeat the same kind of word 3 times.
    intent_keywords = [
        "mentorship", "guidance", "advice", "session", "career", "discuss",
        "learn", "experience", "opportunity", "connect", "schedule", "meeting",
        "chat", "talk", "call", "insight", "insights", "tips", "path", "journey",
        "transition", "break into", "breaking into", "pick your brain",
        "guide", "mentor", "understand", "curious about",
    ]
    matched = sum(1 for k in intent_keywords if _contains(message_lower, k))
    scores["intent"] = 0.25 if matched >= 1 else 0.0

    # Check 2 — Professional Tone (weight 0.25)
    # Only genuinely demanding/pushy language is penalised now. Casual
    # openers ("hey") and the word "job" are normal, legitimate language for
    # this platform, not a tone problem.
    unprofessional = [
        "sup", "yo", "gimme", "asap", "urgent", "immediately",
        "refer me", "get me",
    ]
    penalty = sum(1 for u in unprofessional if _contains(message_lower, u))
    scores["professional_tone"] = max(0.25 - (penalty * 0.05), 0.0)

    # Check 3 — Personalisation (weight 0.25)
    # Does the message reference the alumni specifically? One real signal is
    # enough — expecting two separate "your X" phrases in one short message
    # was the strictest, least natural part of the old scoring.
    personal_signals = [
        "your experience", "your background", "your work", "your role",
        "your company", "your profile", "your journey", "your career",
        "you have", "you work", "your field", "your expertise",
        "your industry", "your team", "you're", "you are", "saw that you",
        "saw you", "noticed you", "given your", "based on your", "since you",
    ]
    matched_p = sum(1 for p in personal_signals if _contains(message_lower, p))
    scores["personalisation"] = 0.25 if matched_p >= 1 else 0.0

    # Check 4 — Message Quality (weight 0.25)
    # A short but sincere message (15-29 words) now earns partial credit
    # instead of zero; 30+ words (was 50) earns full credit.
    word_count = len(message.split())
    if word_count >= 30:
        quality = 0.25
    elif word_count >= 15:
        quality = 0.15
    else:
        quality = 0.0
    scores["message_quality"] = quality

    total_score = sum(scores.values())
    passed = total_score >= 0.6

    suggestions = []
    if scores["intent"] < 0.15:
        suggestions.append(
            "Add a specific mentorship ask — what do you "
            "want to discuss or learn from this alumnus?"
        )
    if scores["professional_tone"] < 0.20:
        suggestions.append(
            "Use a professional greeting and avoid "
            "casual language or demanding phrases."
        )
    if scores["personalisation"] < 0.15:
        suggestions.append(
            "Reference something specific about the "
            "alumnus — their company, role, or experience."
        )
    if scores["message_quality"] < 0.15:
        suggestions.append(
            "Write at least 15 words. Give enough context "
            "about yourself and your goals."
        )

    return {
        "score": round(total_score, 2),
        "passed": passed,
        "breakdown": {
            "intent": round(scores["intent"], 2),
            "professional_tone": round(scores["professional_tone"], 2),
            "personalisation": round(scores["personalisation"], 2),
            "message_quality": round(scores["message_quality"], 2),
        },
        "suggestions": suggestions
    }


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
