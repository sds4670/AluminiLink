from typing import Dict, Any


def screen_message(message: str) -> dict:
    """
    Score an outreach message on 4 dimensions (intent, professional tone,
    personalisation, message quality), each weighted 0.25, for a 0.0-1.0
    composite. Pass threshold = 0.6.
    """
    scores = {}

    # Check 1 — Intent (weight 0.25)
    # Does the message have a clear mentorship ask?
    intent_keywords = [
        "mentorship", "guidance", "advice", "session",
        "career", "discuss", "learn", "experience",
        "opportunity", "connect", "schedule", "meeting"
    ]
    matched = sum(1 for k in intent_keywords if k in message.lower())
    scores["intent"] = min(matched / 3, 1.0) * 0.25

    # Check 2 — Professional Tone (weight 0.25)
    # No slang, casual openers, or demanding language
    unprofessional = [
        "hey", "hi there", "sup", "yo", "gimme",
        "asap", "urgent", "immediately", "job",
        "referral", "refer me", "get me"
    ]
    penalty = sum(1 for u in unprofessional if u in message.lower())
    scores["professional_tone"] = max(0.25 - (penalty * 0.05), 0.0)

    # Check 3 — Personalisation (weight 0.25)
    # Does message reference the alumni specifically?
    personal_signals = [
        "your experience", "your background",
        "your work", "your role", "your company",
        "your profile", "your journey", "your career",
        "you have", "you work", "your field",
        "your expertise", "your industry"
    ]
    matched_p = sum(1 for p in personal_signals if p in message.lower())
    scores["personalisation"] = min(matched_p / 2, 1.0) * 0.25

    # Check 4 — Message Quality (weight 0.25)
    # Word count minimum 30, penalise very short messages
    word_count = len(message.split())
    if word_count >= 50:
        quality = 0.25
    elif word_count >= 30:
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
            "Write at least 30 words. Give enough context "
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
