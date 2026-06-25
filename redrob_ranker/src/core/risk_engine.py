import yaml
import os
import datetime
from typing import Dict, Any

config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "weights.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
    DOMAIN_WEIGHTS = config["risk_engine"]["domain"]
    EXPECTED_SAL_MAX = config["risk_engine"]["expected_salary_penalty_max"]

def evaluate_risks(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Stages 9-10: Availability and Domain Risk Engine"""
    sig = cand.get("redrob_signals", {})
    
    # Availability Risk Engine
    avail_penalty = 0.0
    if sig.get("notice_period_days", 0) > 120:
        avail_penalty += 8
    if sig.get("recruiter_response_rate", 1.0) < 0.10:
        avail_penalty += 10
    
    try:
        last_active = datetime.datetime.strptime(sig.get("last_active_date", "2026-06-24"), "%Y-%m-%d").timestamp()
        if (datetime.datetime.now().timestamp() - last_active) > (180 * 24 * 3600):
            avail_penalty += 10
    except Exception:
        pass
        
    # Expected Salary Risk
    salary_range = sig.get("expected_salary_range_inr_lpa", {})
    max_sal = salary_range.get("max", 0)
    yoe = cand.get("profile", {}).get("years_of_experience", 1)
    if yoe > 0 and max_sal > 0:
        ratio = max_sal / float(yoe)
        if ratio > 15: # Expecting > 15 LPA per YOE
            avail_penalty += min(float(EXPECTED_SAL_MAX), (ratio - 15) * 0.1)
    
    trace["risks"]["availability_penalty"] = avail_penalty
    
    # Domain Risk Engine
    domain_penalties = []
    
    # Consulting Only
    history = cand.get("career_history", [])
    is_pure_consulting = len(history) > 0 and all(r.get("industry", "").lower() == "it services" for r in history)
    if is_pure_consulting:
        domain_penalties.append(DOMAIN_WEIGHTS.get("consulting_only", 15))
    
    # LangChain / Framework
    skills = [s.get("name", "").lower() for s in cand.get("skills", [])]
    has_langchain = any("langchain" in s for s in skills)
    t1_score = sum(trace["capabilities"][cap]["score"] for cap in trace["capabilities"] if cap in ["Retrieval", "Ranking", "Evaluation", "Recommendation", "Matching"])
    
    if has_langchain and t1_score < 5:
        domain_penalties.append(DOMAIN_WEIGHTS.get("langchain_only", 20))
        domain_penalties.append(DOMAIN_WEIGHTS.get("framework_centric", 20))
        
    # CV / Speech / Robotics Only
    titles = " ".join([r.get("title", "").lower() for r in history])
    if ("computer vision" in titles or "cv engineer" in titles) and t1_score < 5:
        domain_penalties.append(DOMAIN_WEIGHTS.get("cv_only", 20))
    if ("speech" in titles or "asr" in titles or "tts" in titles) and t1_score < 5:
        domain_penalties.append(DOMAIN_WEIGHTS.get("speech_only", 20))
    if ("robotics" in titles) and t1_score < 5:
        domain_penalties.append(DOMAIN_WEIGHTS.get("robotics_only", 20))
        
    domain_penalty = max(domain_penalties) if domain_penalties else 0.0
    trace["risks"]["domain_penalty"] = domain_penalty

    # Gates
    is_research_only = len(history) > 0 and all(r.get("industry", "").lower() in ["research", "academia"] for r in history)
    if is_research_only and sum(c["production"] for c in trace["capabilities"].values()) < 0.5:
        trace["gates"].append("Research Only + No Production")
