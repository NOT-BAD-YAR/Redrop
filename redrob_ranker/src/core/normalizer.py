import datetime
from typing import Dict, Any

def parse_date(date_str: str) -> float:
    if not date_str:
        return 0.0
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").timestamp()
    except Exception:
        return 0.0

def normalize_candidate(cand: Dict[str, Any]) -> None:
    """Stage 0: Schema Validation and Normalization"""
    for role in cand.get("career_history", []):
        role["start_ts"] = parse_date(role.get("start_date"))
        if role.get("end_date"):
            role["end_ts"] = parse_date(role.get("end_date"))
        else:
            role["end_ts"] = datetime.datetime.now().timestamp()
