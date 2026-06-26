import os
from typing import Dict, Any

import yaml

config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "weights.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    _CONFIG = yaml.safe_load(f)

WEIGHTS = _CONFIG["technical_fit"]["capability_weights"]
EXPERIENCE_CONFIG = _CONFIG.get("experience_engine", {})


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
