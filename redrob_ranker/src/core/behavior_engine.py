import yaml
import os
from typing import Dict, Any

config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "weights.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    WEIGHTS = yaml.safe_load(f)["behavior_engine"]

def calculate_behavior(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Stage 8: Behavior Engine"""
    sig = cand.get("redrob_signals", {})
    
    # 1. Market Intent
    otw = 1.0 if sig.get("open_to_work_flag") else 0.5
    apps = min(1.0, sig.get("applications_submitted_30d", 0) / 10.0)
    intent_score = (otw * 0.7) + (apps * 0.3)
    
    # 2. Reachability
    resp_rate = sig.get("recruiter_response_rate", 0.5)
    resp_time = sig.get("avg_response_time_hours", 48)
    time_score = 1.0 if resp_time < 24 else max(0.2, 1.0 - (resp_time / 168.0))
    reachability_score = (resp_rate * 0.8) + (time_score * 0.2)
    
    # 3. Recruiter Demand
    views = min(1.0, sig.get("profile_views_received_30d", 0) / 100.0)
    saves = min(1.0, sig.get("saved_by_recruiters_30d", 0) / 10.0)
    search = min(1.0, sig.get("search_appearance_30d", 0) / 200.0)
    demand_score = (views + saves + search) / 3.0
    
    # 4. Reliability
    int_comp = sig.get("interview_completion_rate", 0.8)
    offer_acc = sig.get("offer_acceptance_rate", 0.8)
    if offer_acc == -1: offer_acc = 0.8
    reliability_score = (int_comp * 0.7) + (offer_acc * 0.3)
    
    # 5. Logistics
    np = sig.get("notice_period_days", 60)
    np_score = max(0.0, 1.0 - (np / 90.0)) # 0 days = 1.0, 90+ days = 0.0
    relocate = 1.0 if sig.get("willing_to_relocate") else 0.5
    mode = sig.get("preferred_work_mode", "hybrid")
    mode_score = 1.0 if mode in ["onsite", "hybrid", "flexible"] else 0.5
    logistics_score = (np_score * 0.5) + (relocate * 0.25) + (mode_score * 0.25)
    
    # 6. Trust
    v_email = 1.0 if sig.get("verified_email") else 0.0
    v_phone = 1.0 if sig.get("verified_phone") else 0.0
    li = 1.0 if sig.get("linkedin_connected") else 0.0
    profile_comp = sig.get("profile_completeness_score", 50) / 100.0
    gh = sig.get("github_activity_score", 0)
    gh_score = max(0.0, min(1.0, gh / 100.0))
    trust_score = (v_email * 0.2) + (v_phone * 0.2) + (li * 0.2) + (profile_comp * 0.2) + (gh_score * 0.2)
    
    # Store scores
    trace["behavior"]["intent_score"] = intent_score
    trace["behavior"]["reachability_score"] = reachability_score
    trace["behavior"]["demand_score"] = demand_score
    trace["behavior"]["reliability_score"] = reliability_score
    trace["behavior"]["logistics_score"] = logistics_score
    trace["behavior"]["trust_score"] = trust_score
    
    # Combine using weights
    g = WEIGHTS.get("groups", {})
    total_score = (
        intent_score * g.get("market_intent", 0.25) +
        reachability_score * g.get("reachability", 0.25) +
        demand_score * g.get("recruiter_demand", 0.15) +
        reliability_score * g.get("reliability", 0.15) +
        logistics_score * g.get("logistics", 0.10) +
        trust_score * g.get("trust", 0.10)
    )
    
    # Map [0, 1] to [min_mult, max_mult]
    min_mult = WEIGHTS.get("min_multiplier", 0.70)
    max_mult = WEIGHTS.get("max_multiplier", 1.15)
    
    beh_mult = min_mult + ((max_mult - min_mult) * total_score)
    trace["behavior"]["final_multiplier"] = max(min_mult, min(max_mult, beh_mult))
