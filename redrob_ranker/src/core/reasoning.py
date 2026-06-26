import datetime
from typing import Dict, Any, List, Optional


def _days_since_active(sig: Dict[str, Any]) -> Optional[int]:
    """Prefer last_active_days_ago if present; otherwise derive from last_active_date."""
    if sig.get("last_active_days_ago") is not None:
        try:
            return int(sig["last_active_days_ago"])
        except (TypeError, ValueError):
            pass

    date_str = sig.get("last_active_date", "")
    if not date_str:
        return None

    try:
        last_active = datetime.datetime.strptime(str(date_str), "%Y-%m-%d")
        return (datetime.datetime.now() - last_active).days
    except (TypeError, ValueError):
        return None


def _response_rate_phrase(rate: float) -> str:
    if rate >= 0.5:
        return "high recruiter response rate"
    if rate >= 0.15:
        return "moderate recruiter response rate"
    return "low recruiter response rate"


def generate_reasoning(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Stage 14: Reasoning Generator"""

    profile = cand.get("profile", {})
    sig = cand.get("redrob_signals", {})

    title = profile.get("current_title") or "Engineer"
    yoe = profile.get("years_of_experience", 0.0) or 0.0

    caps: List[tuple] = []
    for cap, cap_trace in trace["capabilities"].items():
        if cap_trace.get("score", 0.0) > 0:
            caps.append((cap, cap_trace["score"]))
    caps.sort(key=lambda x: x[1], reverse=True)

    top_caps = [c[0] for c in caps[:2]]

    cap_phrases = {
        "Ranking": "learning-to-rank",
        "Retrieval": "hybrid retrieval",
        "Evaluation": "evaluation frameworks",
        "Vector Search": "vector search infrastructure",
        "Embeddings": "embedding",
        "Product ML": "production ML",
        "Matching": "candidate matching",
        "Recommendation": "recommendation",
        "Fine Tuning": "LLM fine-tuning",
    }

    exact_strengths: List[str] = []
    seen_phrases: set = set()
    for cap in top_caps:
        phrase = cap_phrases.get(cap, cap.lower())
        if phrase not in seen_phrases:
            seen_phrases.add(phrase)
            exact_strengths.append(phrase)

    if not exact_strengths:
        strength_text = "machine learning and data systems"
    elif len(exact_strengths) == 1:
        strength_text = exact_strengths[0]
    else:
        strength_text = f"{exact_strengths[0]} and {exact_strengths[1]}"

    trace["top_strengths"] = exact_strengths

    jd_matches_list = [
        c[0].lower()
        for c in caps
        if c[0] in ["Retrieval", "Ranking", "Evaluation", "Recommendation", "Matching"]
    ]
    if not jd_matches_list:
        jd_matches_list = ["AI"]
    trace["jd_matches"] = jd_matches_list

    concerns: List[str] = []
    if trace["risks"].get("availability_penalty", 0) > 0:
        notice_period = sig.get("notice_period_days", 0)
        if notice_period > 90:
            concerns.append(f"{notice_period} day notice period")
        else:
            concerns.append("high availability risk")
    if trace["risks"].get("domain_penalty", 0) > 0:
        concerns.append("domain mismatch")
    if trace.get("experience_penalty", 0) > 0:
        concerns.append("experience outside ideal 5-9 year band")

    trace["concerns"] = concerns

    rate = sig.get("recruiter_response_rate", 0.0) or 0.0

    parts: List[str] = [f"{title} with {yoe:.1f} YOE", f"strong in {strength_text}"]

    location = (profile.get("location") or "").strip()
    if location:
        parts.append(location)

    notice_period = sig.get("notice_period_days")
    if notice_period is not None:
        parts.append(f"{int(notice_period)}d notice")

    days_ago = _days_since_active(sig)
    if days_ago is not None:
        parts.append(f"active {days_ago}d ago")

    parts.append(_response_rate_phrase(rate))

    if concerns:
        parts.append(f"note {concerns[0]}")

    sentence = "; ".join(parts) + "."

    trace["reasoning_facts"] = [sentence]
