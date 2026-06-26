import re
import yaml
import datetime
import os
from typing import Dict, Any, Tuple

# Load dictionaries
config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "dictionaries.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    DICTS = yaml.safe_load(f)

def _compile_group(group: Dict[str, list]) -> Dict[str, re.Pattern]:
    return {k: re.compile("|".join(v), re.IGNORECASE) for k, v in group.items()}

TIER_1_REGEX = _compile_group(DICTS["taxonomy"]["tier_1"])
TIER_2_REGEX = _compile_group(DICTS["taxonomy"]["tier_2"])
TIER_3_REGEX = _compile_group(DICTS["taxonomy"]["tier_3"])
OWNERSHIP_REGEX = _compile_group(DICTS["ownership"])
PROD_REGEX = _compile_group(DICTS["production"])

def get_ownership_modifier(text: str) -> float:
    if not text: return 0.5
    if OWNERSHIP_REGEX["negation"].search(text): return 0.0
    if OWNERSHIP_REGEX["high"].search(text): return 1.0
    if OWNERSHIP_REGEX["medium"].search(text): return 0.6
    if OWNERSHIP_REGEX["low"].search(text): return 0.3
    if OWNERSHIP_REGEX["exploration"].search(text): return 0.1
    return 0.5

def get_production_modifier(text: str) -> float:
    if not text: return 0.5
    score = 0.0
    has_mention = PROD_REGEX["mention"].search(text)
    has_users = PROD_REGEX["users"].search(text)
    has_scale = PROD_REGEX["scale"].search(text)
    
    if has_mention and has_users and has_scale: score = 1.0
    elif has_scale: score = 0.8
    elif has_users: score = 0.5
    elif has_mention: score = 0.3
    return 0.5 + 0.5 * score

def extract_evidence(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Stages 2-5: Evidence Extraction, Ownership, Recency, Production"""
    for cap_tier, cap_dict in [("T1", TIER_1_REGEX), ("T2", TIER_2_REGEX), ("T3", TIER_3_REGEX)]:
        for cap, regex in cap_dict.items():
            if cap not in trace["capabilities"]:
                continue
            best_score = 0.0
            evidence_count = 0
            recency_sum = 0.0
            exact_matches = set()
            
            for role in cand.get("career_history", []):
                text = role.get("description", "")
                m = regex.search(text)
                if m:
                    evidence_count += 1
                    exact_matches.add(m.group(0).lower())
                    own_mod = get_ownership_modifier(text)
                    prod_mod = get_production_modifier(text)
                    
                    age_years = (datetime.datetime.now().timestamp() - role.get("start_ts", 0)) / (3600*24*365)
                    if role.get("is_current"): rec_weight = 1.0
                    elif age_years < 2: rec_weight = 0.85
                    elif age_years < 5: rec_weight = 0.65
                    else: rec_weight = 0.50
                    rec_mod = 0.5 + 0.5 * rec_weight
                    
                    score = 1.0 * own_mod * rec_mod * prod_mod
                    recency_sum += rec_mod
                    if score > best_score:
                        best_score = score
                        trace["capabilities"][cap]["best_role_evidence"] = role.get("title", "")
                        trace["capabilities"][cap]["ownership"] = own_mod
                        trace["capabilities"][cap]["production"] = prod_mod
            
            for source_key, trust in [("summary", 0.7), ("headline", 0.6)]:
                text = cand.get("profile", {}).get(source_key, "")
                m = regex.search(text)
                if m:
                    evidence_count += 1
                    exact_matches.add(m.group(0).lower())
                    score = trust * 0.5 * 0.5 * 0.5
                    if score > best_score: best_score = score
            
            for skill in cand.get("skills", []):
                m = regex.search(skill.get("name", ""))
                if m:
                    evidence_count += 1
                    exact_matches.add(m.group(0).lower())
                    score = 0.2 * 0.5 * 0.5 * 0.5
                    if score > best_score: best_score = score
            
            if evidence_count > 0:
                rec_avg = recency_sum / max(1, sum(1 for r in cand.get("career_history", []) if regex.search(r.get("description", ""))))
                role_breadth = min(1.0, evidence_count / 3.0)
                final_cap_score = (0.50 * best_score) + (0.35 * rec_avg) + (0.15 * role_breadth)
            else:
                final_cap_score = best_score
                
            trace["capabilities"][cap]["score"] = final_cap_score
            trace["capabilities"][cap]["raw_evidence_hits"] = evidence_count
            trace["capabilities"][cap]["exact_matches"] = list(exact_matches)
