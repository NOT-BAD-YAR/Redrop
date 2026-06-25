import yaml
import os
from typing import Dict, Any

config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "weights.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    WEIGHTS = yaml.safe_load(f)["credibility_engine"]

def validate_evidence(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Stage 1: Evidence Validation Engine (Consistency & Credibility)"""
    credibility = 1.0
    career_months = sum(r.get("duration_months", 0) for r in cand.get("career_history", []))
    
    # Skill Duration Validation
    for skill in cand.get("skills", []):
        diff = skill.get("duration_months", 0) - career_months
        if diff > 120:
            credibility = min(credibility, WEIGHTS.get("major_penalty", 0.60))
            trace["credibility"]["flags"].append(f"Major: Skill {skill['name']} > career + 10y")
        elif diff > 60:
            credibility = min(credibility, WEIGHTS.get("medium_penalty", 0.85))
            trace["credibility"]["flags"].append(f"Medium: Skill {skill['name']} > career + 5y")
        elif diff > 20:
            credibility = min(credibility, WEIGHTS.get("minor_penalty", 0.95))
            trace["credibility"]["flags"].append(f"Minor: Skill {skill['name']} > career + 1.6y")
            
    # Education Chronology Weirdness
    ed_years = []
    for e in cand.get("education", []):
        deg = e.get("degree_name", "").lower()
        end = str(e.get("end_date", ""))
        try:
            y = int(end[-4:]) if len(end) >= 4 else 0
            if y > 0: ed_years.append((deg, y))
        except ValueError:
            pass
            
    for d1, y1 in ed_years:
        for d2, y2 in ed_years:
            m1 = any(x in d1 for x in ["master", "msc", "mtech", "ms"])
            b2 = any(x in d2 for x in ["bachelor", "bsc", "btech", "bs"])
            if m1 and b2 and y1 < y2:
                credibility = min(credibility, WEIGHTS.get("major_penalty", 0.60))
                trace["credibility"]["flags"].append("Education chronology weirdness")
                    
    # Skill Assessment Check
    assessments = cand.get("redrob_signals", {}).get("skill_assessment_scores", {})
    for skill, score in assessments.items():
        if score < 30:
            credibility = min(credibility, WEIGHTS.get("assessment_penalty", 0.85))
            trace["credibility"]["flags"].append(f"Low assessment ({score}) for {skill}")

    trace["credibility"]["final_multiplier"] = credibility
