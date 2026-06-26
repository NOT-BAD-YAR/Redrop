import datetime
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

MAX_REASONING_CHARS = 300

CAPABILITY_JD_THEME: Dict[str, str] = {
    "Ranking": "search and ranking",
    "Retrieval": "retrieval and embeddings",
    "Evaluation": "ranking evaluation",
    "Vector Search": "vector search",
    "Embeddings": "retrieval and embeddings",
    "Product ML": "production ML",
    "Matching": "search and ranking",
    "Recommendation": "recommendation systems",
    "Fine Tuning": "LLM and retrieval workflows",
}

# Maps raw regex hits to natural phrasing (same meaning, cleaner English).
TERM_CANONICAL: Dict[str, str] = {
    "embedding": "embeddings",
    "embeddings": "embeddings",
    "sentence transformers": "sentence-transformer work",
    "sentence-transformers": "sentence-transformer work",
    "recommendation system": "recommendation systems",
    "recommendation systems": "recommendation systems",
    "learning to rank": "learning-to-rank",
    "learning-to-rank": "learning-to-rank",
    "re-ranking": "re-ranking",
    "ranking": "ranking",
    "information retrieval": "information retrieval",
    "retrieval": "retrieval",
    "semantic search": "semantic search",
    "vector search": "vector search",
    "hybrid retrieval": "hybrid retrieval",
    "production": "production deployment",
    "scale": "production scale",
    "offline evaluation": "offline evaluation",
    "a/b testing": "A/B testing",
    "ndcg": "NDCG evaluation",
    "fine-tuning": "fine-tuning",
    "fine tuning": "fine-tuning",
    "lora": "LoRA fine-tuning",
    "qlora": "QLoRA fine-tuning",
    "peft": "PEFT fine-tuning",
    "pinecone": "Pinecone",
    "opensearch": "OpenSearch",
    "faiss": "FAISS",
    "milvus": "Milvus",
    "qdrant": "Qdrant",
}

CONCERN_POOLS: Dict[str, List[str]] = {
    "experience_below": [
        "experience sits below the role's preferred band",
        "tenure is lighter than the JD's target range",
        "years of experience fall short of the ideal window",
    ],
    "experience_above": [
        "seniority is slightly outside the target range",
        "the profile exceeds the JD's ideal experience window",
        "experience level is above the role's preferred band",
    ],
    "production_depth": [
        "career text gives less production-scale detail than the top-ranked profiles",
        "production depth is less explicit than in the strongest matches",
        "hands-on production evidence is thinner than among the leading candidates",
        "prior roles do not document production scale as clearly as top picks",
        "deployment-at-scale evidence is less visible than in leading profiles",
        "production context in career history is lighter than among top matches",
    ],
    "activity": [
        "recent platform activity is weaker than among the top picks",
        "recency signals are softer than for the leading candidates",
        "recent engagement is not as strong as the top-ranked group",
        "the candidate has been less active recently than stronger shortlist peers",
        "platform recency trails the most engaged profiles in the pool",
        "last-activity timing is less favorable than for higher-ranked candidates",
    ],
    "engagement": [
        "recruiter response signals are weaker than for stronger candidates",
        "engagement metrics trail the leading shortlist",
        "hiring signals are softer than among higher-ranked profiles",
        "response-rate signals are not as strong as for top contenders",
        "outreach responsiveness appears weaker than for leading matches",
        "recruiter engagement history is less compelling than for top picks",
    ],
    "technical_overlap": [
        "technical overlap is narrower than for the strongest matches",
        "fit is more partial than complete",
        "the profile covers only part of the JD's core stack",
        "core JD requirements are only partly reflected in the profile",
        "depth across the JD's main technical themes is uneven",
        "the technical case is less complete than top profiles",
        "stack alignment is real but not as broad as the strongest candidates",
        "coverage of the JD's main technical areas is incomplete",
    ],
    "thin_evidence": [
        "career-history support is sparse for this JD",
        "prior roles provide limited depth on core requirements",
        "supporting evidence across roles is thin",
    ],
    "domain": [
        "background alignment with the JD domain is weaker",
        "domain fit is not as direct as for higher-ranked candidates",
        "career domain is a less natural match for this role",
    ],
    "notice": [
        "notice period is a hiring consideration",
        "longer notice slightly reduces immediate shortlist appeal",
        "availability timing is less favorable than for top picks",
    ],
    "default_upper": [
        "the case is credible but not as compelling as the very top profiles",
        "overall fit is solid without being standout",
        "strength is real but not at the leading edge of the pool",
    ],
    "default_mid": [
        "relevance is reasonable but not standout",
        "fit is moderate rather than strong",
        "the profile sits in the middle of the shortlist on overall fit",
    ],
    "default_lower": [
        "overall fit trails the stronger candidates on this shortlist",
        "the profile is viable but not competitive with the top tier",
        "ranking reflects weaker alignment than higher-placed candidates",
    ],
}

FIT_LABELS: Dict[str, Dict[str, List[str]]] = {
    "top": {
        "lead": ["a strong match for", "a leading fit for", "well aligned with", "a top-tier fit for"],
        "noun": ["strong match", "leading fit", "top-tier fit"],
    },
    "upper": {
        "lead": ["a good match for", "a solid fit for", "a credible match for"],
        "noun": ["good match", "solid fit", "credible match"],
    },
    "mid": {
        "lead": ["a moderate match for", "some overlap with", "reasonable fit for"],
        "noun": ["moderate match", "some overlap", "reasonable fit"],
    },
    "lower": {
        "lead": ["limited fit for", "partial fit for", "some relevance to"],
        "noun": ["limited fit", "partial fit", "some relevance"],
    },
}


def _seed(rank: int, candidate_id: str, salt: str = "") -> int:
    return int(hashlib.md5(f"{candidate_id}:{rank}:{salt}".encode()).hexdigest(), 16)


def _pick(pool: List[str], rank: int, candidate_id: str, salt: str = "") -> str:
    if not pool:
        return ""
    return pool[_seed(rank, candidate_id, salt) % len(pool)]


def _days_since_active(sig: Dict[str, Any]) -> Optional[int]:
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


def _rank_band(rank: int) -> str:
    if rank <= 10:
        return "top"
    if rank <= 40:
        return "upper"
    if rank <= 75:
        return "mid"
    return "lower"


def _top_capabilities(trace: Dict[str, Any], limit: int = 3) -> List[Tuple[str, Dict[str, Any]]]:
    scored = [
        (cap, ct)
        for cap, ct in trace.get("capabilities", {}).items()
        if ct.get("score", 0.0) > 0
    ]
    scored.sort(key=lambda x: x[1].get("score", 0.0), reverse=True)
    return scored[:limit]


def _find_career_role(cand: Dict[str, Any], role_title: str) -> Optional[Dict[str, Any]]:
    for role in cand.get("career_history", []) or []:
        if role.get("title") == role_title:
            return role
    return None


def _jd_theme(top_caps: List[Tuple[str, Dict[str, Any]]]) -> str:
    for cap, _ in top_caps:
        if cap in CAPABILITY_JD_THEME:
            return CAPABILITY_JD_THEME[cap]
    return "search and ranking"


def _canonical_term(raw: str) -> str:
    key = raw.strip().lower()
    return TERM_CANONICAL.get(key, raw.strip().lower())


def _normalize_evidence_terms(matches: List[str], max_terms: int = 2) -> str:
    """Deduplicate and naturalize raw keyword hits."""
    if not matches:
        return ""

    canonical: List[str] = []
    seen_roots: set = set()

    priority = [
        "learning-to-rank",
        "re-ranking",
        "recommendation systems",
        "information retrieval",
        "semantic search",
        "hybrid retrieval",
        "vector search",
        "embeddings",
        "sentence-transformer work",
        "production deployment",
        "production scale",
        "offline evaluation",
        "A/B testing",
        "NDCG evaluation",
        "fine-tuning",
        "LoRA fine-tuning",
        "QLoRA fine-tuning",
        "PEFT fine-tuning",
        "ranking",
        "retrieval",
        "production",
        "scale",
    ]

    normalized = [_canonical_term(m) for m in matches if m and m.strip()]

    # Prefer richer phrases first.
    for pref in priority:
        for term in normalized:
            if term == pref or pref in term:
                root = pref.split()[0]
                if root not in seen_roots:
                    seen_roots.add(root)
                    if term not in canonical:
                        canonical.append(term)
                break

    for term in normalized:
        root = term.split("-")[0].split()[0]
        if root in seen_roots:
            continue
        # Skip near-duplicates (embedding/embeddings already handled).
        if any(term in c or c in term for c in canonical):
            continue
        seen_roots.add(root)
        canonical.append(term)

    # Collapse fine-tuning family to one term.
    ft_terms = [t for t in canonical if "fine-tuning" in t.lower() or "lora" in t.lower() or "peft" in t.lower()]
    if len(ft_terms) > 1:
        preferred = next(
            (t for t in ft_terms if "QLoRA" in t or "LoRA" in t or "PEFT" in t),
            ft_terms[0],
        )
        canonical = [t for t in canonical if t not in ft_terms or t == preferred]

    # Collapse production redundancy.
    if "production deployment" in canonical and "production scale" in canonical:
        canonical = [t for t in canonical if t != "production scale"]
    if "production deployment" in canonical and "production" in canonical:
        canonical = [t for t in canonical if t != "production"]

    picked = canonical[:max_terms]
    if not picked:
        return ""
    if len(picked) == 1:
        return picked[0]
    return f"{picked[0]} and {picked[1]}"


def _extract_evidence(
    cand: Dict[str, Any], top_caps: List[Tuple[str, Dict[str, Any]]]
) -> Tuple[str, Optional[str], bool, bool]:
    """Return (evidence_phrase, company, has_career, has_production_depth)."""
    if not top_caps:
        return "limited overlap with core JD requirements", None, False, False

    _, best_trace = top_caps[0]
    matches = list(best_trace.get("exact_matches") or [])
    terms = _normalize_evidence_terms(matches)
    role_title = (best_trace.get("best_role_evidence") or "").strip()
    role = _find_career_role(cand, role_title)
    has_production = float(best_trace.get("production", 0.0) or 0.0) >= 0.55

    if role and terms:
        company = (role.get("company") or "").strip() or None
        return terms, company, True, has_production

    if terms:
        return terms, None, False, has_production

    cap = top_caps[0][0]
    theme = CAPABILITY_JD_THEME.get(cap, "search and ranking")
    return f"limited explicit evidence beyond some {theme} keywords", None, False, False


def _typed_concerns(
    trace: Dict[str, Any],
    sig: Dict[str, Any],
    top_caps: List[Tuple[str, Dict[str, Any]]],
    yoe: float,
) -> List[str]:
    types: List[str] = []

    if trace.get("experience_penalty", 0) > 0:
        types.append("experience_below" if yoe < 5 else "experience_above")

    if trace.get("risks", {}).get("domain_penalty", 0) > 0:
        types.append("domain")

    notice = sig.get("notice_period_days")
    if trace.get("risks", {}).get("availability_penalty", 0) > 0:
        if notice and int(notice) > 90:
            types.append("notice")

    days = _days_since_active(sig)
    if days is not None and days >= 90:
        types.append("activity")

    rate = sig.get("recruiter_response_rate", 0.0) or 0.0
    if rate < 0.15:
        types.append("engagement")

    if top_caps:
        _, bt = top_caps[0]
        if bt.get("production", 0.0) < 0.55:
            types.append("production_depth")
        if bt.get("raw_evidence_hits", 0) <= 1:
            types.append("thin_evidence")

    if (trace.get("technical_fit", 0.0) or 0.0) < 35 and "thin_evidence" not in types:
        types.append("technical_overlap")

    return types


def _select_caveat(
    concern_types: List[str],
    band: str,
    rank: int,
    candidate_id: str,
) -> str:
    filtered = list(concern_types)
    if band == "top":
        filtered = [t for t in filtered if t not in ("technical_overlap", "production_depth", "thin_evidence")] or filtered
    elif band == "upper":
        filtered = [t for t in filtered if t != "technical_overlap"] or filtered

    if filtered:
        idx = (_seed(rank, candidate_id, "ctype") + rank * 11) % len(filtered)
        ctype = filtered[idx]
        salt = f"caveat-{ctype}-{rank // 10}"
        return _pick(CONCERN_POOLS[ctype], rank, candidate_id, salt)

    fallback_key = {"top": "default_upper", "upper": "default_upper", "mid": "default_mid", "lower": "default_lower"}[band]
    return _pick(CONCERN_POOLS[fallback_key], rank, candidate_id, f"caveat-default-{rank}")


def _signal_sentence(sig: Dict[str, Any], rank: int, candidate_id: str, band: str) -> str:
    notice = sig.get("notice_period_days")
    days = _days_since_active(sig)
    rate = sig.get("recruiter_response_rate", 0.0) or 0.0
    n_notice = int(notice) if notice is not None else None

    forms: List[str] = []

    if n_notice is not None and days is not None and rate >= 0.5:
        forms.extend([
            f"{n_notice}-day notice and activity {days} days ago strengthen shortlist readiness",
            f"Active {days} days ago with a manageable {n_notice}-day notice period",
            f"Recent activity and a {n_notice}-day notice support near-term availability",
        ])
    elif n_notice is not None and days is not None:
        forms.extend([
            f"Active {days} days ago on a {n_notice}-day notice timeline",
            f"{n_notice}-day notice and last activity {days} days ago are worth weighing",
        ])
    elif n_notice is not None and n_notice > 90:
        forms.append(f"{n_notice}-day notice is a hiring consideration despite otherwise relevant fit")
    elif n_notice is not None:
        forms.append(f"{n_notice}-day notice period noted")

    if rate >= 0.5 and not forms:
        forms.append("high recruiter response rate supports outreach")
    elif 0 < rate < 0.15:
        forms.append("low recruiter response rate is a concern")

    if not forms:
        if band in ("mid", "lower"):
            return ""
        return "profile signals are otherwise workable"

    return _pick(forms, rank, candidate_id, "signal")


def _through_phrase(ctx: Dict[str, Any], rank: int, candidate_id: str) -> str:
    evidence = ctx["evidence"]
    company = ctx["company"]
    if not ctx["has_career_evidence"]:
        return evidence
    if company and _seed(rank, candidate_id, "co") % 3 != 0:
        return f"work at {company} on {evidence}"
    return evidence


def _evidence_with_company(evidence: str, company: Optional[str], rank: int, candidate_id: str) -> str:
    if company and _seed(rank, candidate_id, "co") % 3 != 0:
        return f"career history at {company} shows {evidence}"
    return f"career history shows {evidence}"


def _select_family(band: str, rank: int, candidate_id: str, has_career: bool) -> str:
    if band == "top":
        pool = ["strong_profile", "strong_evidence", "balanced", "signal_led", "strong_profile", "strong_evidence"]
    elif band == "upper":
        pool = ["strong_profile", "strong_evidence", "balanced", "signal_led", "balanced", "strong_evidence"]
    elif band == "mid":
        pool = ["balanced", "cautious", "signal_led", "strong_evidence", "balanced", "cautious"]
    else:
        pool = ["cautious", "caveat_led", "balanced", "signal_led", "caveat_led", "cautious"]

    if not has_career:
        pool = [p for p in pool if p != "strong_evidence"] or pool

    return pool[_seed(rank, candidate_id, "family") % len(pool)]


def _fit_label(band: str, rank: int, candidate_id: str, kind: str = "lead") -> str:
    return _pick(FIT_LABELS[band][kind], rank, candidate_id, f"fit-{kind}")


def prepare_reasoning_context(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    profile = cand.get("profile", {}) or {}
    sig = cand.get("redrob_signals", {}) or {}

    title = (profile.get("current_title") or "Engineer").strip()
    yoe = float(profile.get("years_of_experience", 0.0) or 0.0)
    top_caps = _top_capabilities(trace)

    evidence, company, has_career, has_production = _extract_evidence(cand, top_caps)
    jd_theme = _jd_theme(top_caps)
    concern_types = _typed_concerns(trace, sig, top_caps, yoe)

    trace["top_strengths"] = [jd_theme]
    trace["jd_matches"] = [jd_theme]
    trace["concerns"] = concern_types

    trace["reasoning_context"] = {
        "title": title,
        "yoe": yoe,
        "jd_theme": jd_theme,
        "evidence": evidence,
        "company": company,
        "has_career_evidence": has_career,
        "has_production_depth": has_production,
        "concern_types": concern_types,
        "sig": sig,
    }


def _truncate(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= MAX_REASONING_CHARS:
        return text
    cut = text[: MAX_REASONING_CHARS - 3].rsplit(" ", 1)[0]
    return cut + "..."


def _render_strong_profile(ctx: Dict[str, Any], band: str, rank: int, cid: str) -> str:
    title, yoe, jd = ctx["title"], ctx["yoe"], ctx["jd_theme"]
    evidence = ctx["evidence"]
    company = ctx["company"]
    caveat = _select_caveat(ctx["concern_types"], band, rank, cid)
    signal = _signal_sentence(ctx["sig"], rank, cid, band)
    fit = _fit_label(band, rank, cid)

    if ctx["has_career_evidence"]:
        ev = _evidence_with_company(evidence, company, rank, cid)
    else:
        ev = f"the profile points to {evidence}"

    if band == "top":
        variants = [
            f"{title} ({yoe:.1f} YOE) is {fit} {jd}; {ev}. {signal.capitalize()}.",
            f"{title} with {yoe:.1f} YOE is {fit} {jd} — {ev}. {signal.capitalize()}.",
        ]
    elif band == "upper":
        variants = [
            f"{title} ({yoe:.1f} YOE) is {fit} {jd}; {ev}, though {caveat}.",
            f"{title} with {yoe:.1f} YOE brings {jd} overlap through {ev}, though {caveat}.",
        ]
    else:
        variants = [
            f"{title} with {yoe:.1f} YOE brings {jd} overlap through {ev}, though {caveat}.",
        ]
    return _pick(variants, rank, cid, "tpl-sp")


def _render_strong_evidence(ctx: Dict[str, Any], band: str, rank: int, cid: str) -> str:
    title, yoe, jd = ctx["title"], ctx["yoe"], ctx["jd_theme"]
    evidence = ctx["evidence"]
    company = ctx["company"]
    caveat = _select_caveat(ctx["concern_types"], band, rank, cid)
    signal = _signal_sentence(ctx["sig"], rank, cid, band)
    fit = _fit_label(band, rank, cid, "noun")

    if company:
        opener = f"Career history at {company} shows {evidence}"
    else:
        opener = f"Career history shows {evidence}"

    if band == "top":
        return f"{opener}; {title} with {yoe:.1f} YOE aligns well with the JD's {jd}. {signal.capitalize()}."
    if band == "upper":
        return f"{opener}; {title} with {yoe:.1f} YOE is a {fit}, though {caveat}. {signal.capitalize()}."
    if band == "mid":
        return f"{opener}; {title} with {yoe:.1f} YOE has some {jd} relevance, but {caveat}."
    return f"{opener}; {title} with {yoe:.1f} YOE shows only partial {jd} relevance — {caveat}."


def _render_balanced(ctx: Dict[str, Any], band: str, rank: int, cid: str) -> str:
    title, yoe, jd = ctx["title"], ctx["yoe"], ctx["jd_theme"]
    caveat = _select_caveat(ctx["concern_types"], band, rank, cid)
    signal = _signal_sentence(ctx["sig"], rank, cid, band)
    bridge = _through_phrase(ctx, rank, cid)

    suffix = f" {signal.capitalize()}." if signal else ""
    if band in ("top", "upper"):
        return f"{title} with {yoe:.1f} YOE brings {jd} overlap through {bridge}, though {caveat}.{suffix}"
    return f"{title} with {yoe:.1f} YOE shows some relevance to {jd} through {bridge}, but {caveat}.{suffix}"


def _render_cautious(ctx: Dict[str, Any], band: str, rank: int, cid: str) -> str:
    title, yoe, jd = ctx["title"], ctx["yoe"], ctx["jd_theme"]
    evidence = ctx["evidence"]
    caveat = _select_caveat(ctx["concern_types"], band, rank, cid)
    signal = _signal_sentence(ctx["sig"], rank, cid, band)
    suffix = f" {signal.capitalize()}." if signal and band == "lower" else ""

    return (
        f"{title} with {yoe:.1f} YOE shows some relevance to {jd}, but {caveat}."
        f"{suffix}"
    )


def _render_signal_led(ctx: Dict[str, Any], band: str, rank: int, cid: str) -> str:
    title, yoe, jd = ctx["title"], ctx["yoe"], ctx["jd_theme"]
    evidence = ctx["evidence"]
    signal = _signal_sentence(ctx["sig"], rank, cid, band)
    caveat = _select_caveat(ctx["concern_types"], band, rank, cid)

    if not signal:
        signal = _fit_label(band, rank, cid, "noun").capitalize()

    if band in ("top", "upper"):
        return f"{signal.capitalize()}; {title} with {yoe:.1f} YOE also shows {evidence}, supporting {jd} fit."
    return f"{signal.capitalize()}; {title} with {yoe:.1f} YOE shows {evidence}, though {caveat}."


def _render_caveat_led(ctx: Dict[str, Any], band: str, rank: int, cid: str) -> str:
    title, yoe, jd = ctx["title"], ctx["yoe"], ctx["jd_theme"]
    caveat = _select_caveat(ctx["concern_types"], band, rank, cid)
    bridge = _through_phrase(ctx, rank, cid)

    return f"{caveat.capitalize()}. Even so, {title} with {yoe:.1f} YOE shows some {jd} overlap through {bridge}."


RENDERERS = {
    "strong_profile": _render_strong_profile,
    "strong_evidence": _render_strong_evidence,
    "balanced": _render_balanced,
    "cautious": _render_cautious,
    "signal_led": _render_signal_led,
    "caveat_led": _render_caveat_led,
}


def render_reasoning(cand: Dict[str, Any], trace: Dict[str, Any], rank: int) -> str:
    ctx = trace.get("reasoning_context")
    if not ctx:
        prepare_reasoning_context(cand, trace)
        ctx = trace["reasoning_context"]

    cid = cand.get("candidate_id", "")
    band = _rank_band(rank)
    family = _select_family(band, rank, cid, ctx["has_career_evidence"])
    text = RENDERERS[family](ctx, band, rank, cid)
    return _truncate(text)


def generate_reasoning(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    prepare_reasoning_context(cand, trace)
    trace["reasoning_facts"] = []
