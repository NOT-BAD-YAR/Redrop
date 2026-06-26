import os
import re
from typing import Dict, Any

import yaml

config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "weights.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    _CONFIG = yaml.safe_load(f)

WEIGHTS = _CONFIG["technical_fit"]["capability_weights"]
EXPERIENCE_CONFIG = _CONFIG.get("experience_engine", {})
SENIORITY_PENALTY = float(_CONFIG.get("risk_engine", {}).get("junior_title_penalty", 0.25))
JUNIOR_TITLE_PATTERN = re.compile(r"\b(junior|jr\.?)\b", re.IGNORECASE)

NON_AI_TITLES = [
    "business analyst",
    "hr manager",
    "human resources",
    "marketing manager",
    "product manager",
    "data entry",
    "sales executive",
    "sales manager",
    "recruiter",
    "account manager",
    "project manager",
    "operations manager",
    "content writer",
    "graphic designer",
    "ux designer",
]

INTERN_TRAINEE_TITLES = ["intern", "trainee"]

TITLE_TRAP_MULTIPLIER = float(_CONFIG.get("risk_engine", {}).get("title_trap_multiplier", 0.60))
INTERN_TRAINEE_MULTIPLIER = float(_CONFIG.get("risk_engine", {}).get("intern_trainee_multiplier", 0.70))
TITLE_TRAP_MIN_AI_CAPS = int(_CONFIG.get("risk_engine", {}).get("title_trap_min_ai_caps", 2))
TITLE_TRAP_MIN_TECHNICAL_FIT = float(
    _CONFIG.get("risk_engine", {}).get("title_trap_min_technical_fit", 20)
)


def _title_contains_phrase(title_lower: str, phrases: list[str]) -> bool:
    return any(phrase in title_lower for phrase in phrases)


def _has_ai_keyword_signal(trace: Dict[str, Any]) -> bool:
    cap_hits = sum(1 for c in trace["capabilities"].values() if c.get("score", 0) > 0)
    return cap_hits >= TITLE_TRAP_MIN_AI_CAPS or trace.get("technical_fit", 0) >= TITLE_TRAP_MIN_TECHNICAL_FIT


def score_technical_fit(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Stages 6-7: Capability Aggregation and Technical Fit"""
    score = 0.0
    for cap, cap_trace in trace["capabilities"].items():
        w = WEIGHTS.get(cap, 0)
        score += cap_trace["score"] * w

    trace["technical_fit"] = min(100.0, score)


def apply_experience_penalty(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Apply YOE band soft penalty to technical_fit before final score is computed."""
    cfg = EXPERIENCE_CONFIG
    if not cfg:
        trace["experience_penalty"] = 0.0
        return

    profile = cand.get("profile", {})
    yoe = float(profile.get("years_of_experience", 0.0) or 0.0)

    ideal_min = float(cfg.get("ideal_min", 5))
    ideal_max = float(cfg.get("ideal_max", 9))
    penalty_under = float(cfg.get("soft_penalty_per_year_under", 0.08))
    penalty_over = float(cfg.get("soft_penalty_per_year_over", 0.05))
    hard_floor = float(cfg.get("hard_floor_yoe", 1.5))

    if yoe < hard_floor:
        trace["gates"].append(f"Experience below hard floor ({yoe:.1f} < {hard_floor})")
        trace["experience_penalty"] = 1.0
        trace["technical_fit"] = 0.0
        return

    penalty_ratio = 0.0
    if yoe < ideal_min:
        penalty_ratio += (ideal_min - yoe) * penalty_under
    elif yoe > ideal_max:
        penalty_ratio += (yoe - ideal_max) * penalty_over

    penalty_ratio = min(0.5, max(0.0, penalty_ratio))
    trace["experience_penalty"] = penalty_ratio

    if penalty_ratio > 0:
        trace["technical_fit"] = max(0.0, trace["technical_fit"] * (1.0 - penalty_ratio))


def apply_seniority_penalty(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Penalize Junior/Jr. titles for a Senior-level JD."""
    title = (cand.get("profile", {}) or {}).get("current_title", "") or ""
    if JUNIOR_TITLE_PATTERN.search(title):
        trace["seniority_penalty"] = SENIORITY_PENALTY
    else:
        trace["seniority_penalty"] = 0.0


def apply_title_trap_penalties(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Detect keyword stuffers and wrong-level intern/trainee titles."""
    title = (cand.get("profile", {}) or {}).get("current_title", "") or ""
    title_lower = title.lower()
    trace["title_trap_multiplier"] = 1.0

    if _title_contains_phrase(title_lower, INTERN_TRAINEE_TITLES):
        trace["title_trap_multiplier"] = INTERN_TRAINEE_MULTIPLIER
        return

    if _title_contains_phrase(title_lower, NON_AI_TITLES) and _has_ai_keyword_signal(trace):
        trace["title_trap_multiplier"] = TITLE_TRAP_MULTIPLIER
        trace["gates"].append("Title trap: non-AI role with AI skills")
