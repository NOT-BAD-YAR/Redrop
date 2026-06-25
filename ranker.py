import json
import re
import datetime
import math
from typing import Dict, List, Any
import multiprocessing as mp

# ==========================================
# CONSTANTS & REGEX COMPILED PATTERNS
# ==========================================

TIER_1_TAXONOMY = {
    "Retrieval": [r"\bretrieval\b", r"\bsemantic search\b", r"\binformation retrieval\b", r"\bdense retrieval\b", r"\bhybrid retrieval\b", r"\bcandidate retrieval\b", r"\bvector retrieval\b"],
    "Ranking": [r"\branking\b", r"\blearning-to-rank\b", r"\blearning to rank\b", r"\bre-ranking\b", r"\breranking\b", r"\brelevance\b", r"\branking models?\b"],
    "Evaluation": [r"\bndcg\b", r"\bmrr\b", r"\bmap\b", r"a/b testing", r"\boffline evaluation\b", r"\bonline evaluation\b", r"\bevaluation framework\b"],
    "Recommendation": [r"\brecommendation systems?\b", r"\bpersonalization\b", r"\brecommender systems?\b", r"\brecommender\b"],
    "Matching": [r"\bcandidate matching\b", r"\bjd matching\b", r"\bmarketplace matching\b"]
}

TIER_2_TAXONOMY = {
    "Embeddings": [r"\bbge\b", r"\be5\b", r"\bsentence[- ]transformers\b", r"\bembeddings?\b"],
    "Vector Search": [r"\bpinecone\b", r"\bmilvus\b", r"\bqdrant\b", r"\bfaiss\b", r"\bweaviate\b", r"\bopensearch\b", r"\belasticsearch\b", r"\bvector search\b", r"\bvector db\b"],
    "LTR": [r"\bxgboost\b", r"\blightgbm\b", r"\bltr\b"],
    "Fine Tuning": [r"\blora\b", r"\bqlora\b", r"\bpeft\b", r"\bfine[- ]tuning\b", r"\bfine[- ]tune\b"],
    "Product ML": [r"\bproduction\b", r"\blatency\b", r"\bscale\b", r"\breal users\b", r"\bqps\b", r"\bdeployment\b"]
}

TIER_3_TAXONOMY = {
    "Distributed Systems": [r"\bdistributed systems?\b", r"\bspark\b", r"\bkafka\b"],
    "HR Tech / Marketplace": [r"\bhr[- ]tech\b", r"\bmarketplace\b", r"\brecruiting\b", r"\btalent\b"],
    "Open Source": [r"\bopen[- ]source\b", r"\boss\b", r"\bcontributions?\b"]
}

OWNERSHIP_HIGH = [r"\bbuilt\b", r"\bowned\b", r"\bled\b", r"\barchitected\b", r"\bdesigned\b", r"\bimplemented\b", r"\bcreated\b", r"\bauthored\b"]
OWNERSHIP_MED = [r"\bcontributed\b", r"\bworked on\b", r"\bsupported\b", r"\bdeveloped\b", r"\bmaintained\b"]
OWNERSHIP_LOW = [r"\bassisted\b", r"\bhelped\b", r"\bparticipated\b"]
OWNERSHIP_EXP = [r"\blearning\b", r"\bexploring\b", r"\bfamiliar with\b", r"\bexperimented\b"]
OWNERSHIP_NEG = [r"\bnever\b", r"\bnot\b", r"\blimited exposure\b"]

PROD_MENTION = [r"\bdeployed\b", r"\blaunched\b", r"\bproduction\b", r"\brolled out\b"]
PROD_USERS = [r"\breal users\b", r"\bcustomers\b", r"\btraffic\b"]
PROD_SCALE = [r"\bscale\b", r"\bqps\b", r"\blatency\b", r"\bmillisecond\b", r"\bmillions\b", r"\bbillions\b", r"\btb\b", r"\bpb\b"]

def compile_regex(patterns): return re.compile("|".join(patterns), re.IGNORECASE)

TIER_1_REGEX = {k: compile_regex(v) for k, v in TIER_1_TAXONOMY.items()}
TIER_2_REGEX = {k: compile_regex(v) for k, v in TIER_2_TAXONOMY.items()}
TIER_3_REGEX = {k: compile_regex(v) for k, v in TIER_3_TAXONOMY.items()}
OWNERSHIP_REGEX = {"high": compile_regex(OWNERSHIP_HIGH), "medium": compile_regex(OWNERSHIP_MED), "low": compile_regex(OWNERSHIP_LOW), "exploration": compile_regex(OWNERSHIP_EXP), "negation": compile_regex(OWNERSHIP_NEG)}
PROD_REGEX = {"mention": compile_regex(PROD_MENTION), "users": compile_regex(PROD_USERS), "scale": compile_regex(PROD_SCALE)}

def init_trace() -> Dict[str, Any]:
    trace = {
        "capabilities": {},
        "behavior": {"intent_score": 1.0, "reachability_score": 1.0, "demand_score": 1.0, "reliability_score": 1.0, "trust_score": 1.0, "logistics_score": 1.0, "final_multiplier": 1.0},
        "credibility": {"consistency_score": 100, "credibility_score": 100, "final_multiplier": 1.0, "flags": []},
        "risks": {"availability_penalty": 0.0, "domain_penalty": 0.0, "flags": []},
        "gates": [],
        "technical_fit": 0.0,
        "final_score": 0.0,
        "reasoning_facts": []
    }
    for cap in list(TIER_1_TAXONOMY.keys()) + list(TIER_2_TAXONOMY.keys()) + list(TIER_3_TAXONOMY.keys()):
        trace["capabilities"][cap] = {"score": 0.0, "best_role_evidence": "", "ownership": 0.0, "production": 0.0}
    return trace

def parse_date(date_str):
    if not date_str: return None
    try: return datetime.datetime.strptime(date_str, "%Y-%m-%d").timestamp()
    except: return None

def get_ownership_modifier(text):
    if not text: return 0.5
    if OWNERSHIP_REGEX["negation"].search(text): return 0.0
    if OWNERSHIP_REGEX["high"].search(text): return 1.0
    if OWNERSHIP_REGEX["medium"].search(text): return 0.6
    if OWNERSHIP_REGEX["low"].search(text): return 0.3
    if OWNERSHIP_REGEX["exploration"].search(text): return 0.1
    return 0.5  # default if not explicit

def get_production_modifier(text):
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

def process_candidate(line: str):
    if not line.strip(): return None
    try: cand = json.loads(line)
    except: return None
    
    trace = init_trace()
    cand["trace"] = trace
    
    # --- STAGE 0: Schema Validation ---
    for role in cand.get("career_history", []):
        role["start_ts"] = parse_date(role.get("start_date"))
        role["end_ts"] = parse_date(role.get("end_date")) or datetime.datetime.now().timestamp()
    
    # --- STAGE 1: Evidence Validation (Consistency & Credibility) ---
    consistency = 100
    credibility = 100
    career_months = sum(r.get("duration_months", 0) for r in cand.get("career_history", []))
    
    for skill in cand.get("skills", []):
        if skill.get("duration_months", 0) > career_months + 60:
            consistency -= 5
            trace["credibility"]["flags"].append(f"Skill {skill['name']} duration > career + 60m")
    
    # Basic domain checks
    is_pure_consulting = all(r.get("industry", "").lower() == "it services" for r in cand.get("career_history", []))
    is_research_only = all(r.get("industry", "").lower() in ["research", "academia"] for r in cand.get("career_history", []))
    
    trace["credibility"]["consistency_score"] = consistency
    trace["credibility"]["credibility_score"] = credibility
    trace["credibility"]["final_multiplier"] = max(0.8, min(1.0, (consistency + credibility) / 200.0))
    
    if consistency < 50: trace["gates"].append("Severe Credibility Failure")

    # --- STAGES 2-6: Evidence, Ownership, Recency, Production, Capability ---
    sources = [
        ("description", 1.0),
        ("summary", 0.70),
        ("headline", 0.60),
        ("skills", 0.20)
    ]
    
    for cap_tier, cap_dict in [("T1", TIER_1_REGEX), ("T2", TIER_2_REGEX), ("T3", TIER_3_REGEX)]:
        for cap, regex in cap_dict.items():
            best_score = 0.0
            evidence_count = 0
            recency_sum = 0.0
            
            # Check career history
            for role in cand.get("career_history", []):
                text = role.get("description", "")
                if regex.search(text):
                    evidence_count += 1
                    own_mod = get_ownership_modifier(text)
                    prod_mod = get_production_modifier(text)
                    
                    # Recency
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
            
            # Check other sources
            for source_key, trust in [("summary", 0.7), ("headline", 0.6)]:
                text = cand.get("profile", {}).get(source_key, "")
                if regex.search(text):
                    score = trust * 0.5 * 0.5 * 0.5 # default modifiers
                    if score > best_score: best_score = score
            
            # Check skills
            for skill in cand.get("skills", []):
                if regex.search(skill.get("name", "")):
                    score = 0.2 * 0.5 * 0.5 * 0.5
                    if score > best_score: best_score = score
            
            if evidence_count > 0:
                rec_avg = recency_sum / evidence_count
                role_breadth = min(1.0, evidence_count / 3.0)
                final_cap_score = (0.50 * best_score) + (0.35 * rec_avg) + (0.15 * role_breadth)
            else:
                final_cap_score = best_score
                
            trace["capabilities"][cap]["score"] = final_cap_score

    # --- STAGE 7: Technical Fit ---
    t1_score = sum(trace["capabilities"][cap]["score"] * 12 for cap in TIER_1_TAXONOMY)
    t2_score = sum(trace["capabilities"][cap]["score"] * 5 for cap in TIER_2_TAXONOMY)
    t3_score = sum(trace["capabilities"][cap]["score"] * 5 for cap in TIER_3_TAXONOMY)
    
    t1_score = min(60, t1_score)
    t2_score = min(25, t2_score)
    t3_score = min(15, t3_score)
    
    bonus = 0
    if cand.get("profile", {}).get("current_company", "").lower() in ["amazon", "flipkart", "swiggy", "zomato", "yellow.ai"]:
        bonus += 5
    
    ed_tier = next((e.get("tier") for e in cand.get("education", []) if e.get("tier")), "unknown")
    if ed_tier == "tier_1": bonus += 0.5
    elif ed_tier == "tier_2": bonus += 0.25
        
    tech_fit = t1_score + t2_score + t3_score + bonus
    trace["technical_fit"] = min(100.0, tech_fit)

    # --- STAGE 8: Behavior Engine ---
    sig = cand.get("redrob_signals", {})
    
    intent = 1.0 if sig.get("open_to_work_flag") else 0.8
    reach = max(0.05, sig.get("recruiter_response_rate", 0.5)) # Heavy penalty if low
    demand = min(1.2, 0.8 + (sig.get("saved_by_recruiters_30d", 0) / 10.0))
    reliab = max(0.2, sig.get("interview_completion_rate", 0.8))
    
    beh_raw = intent * reach * demand * reliab
    # Normalize beh_raw (which ranges roughly 0.01 to ~1.4) to 0.70 - 1.15
    beh_mult = 0.70 + (0.45 * min(1.0, beh_raw / 0.8))
    trace["behavior"]["final_multiplier"] = max(0.70, min(1.15, beh_mult))

    # --- STAGE 9: Availability Risk Engine ---
    avail_penalty = 0.0
    if sig.get("notice_period_days", 0) > 120: avail_penalty += 8
    if sig.get("recruiter_response_rate", 1.0) < 0.10: avail_penalty += 10
    
    try:
        last_active = datetime.datetime.strptime(sig.get("last_active_date", "2026-06-24"), "%Y-%m-%d").timestamp()
        if (datetime.datetime.now().timestamp() - last_active) > (180 * 24 * 3600):
            avail_penalty += 10
    except: pass
    
    trace["risks"]["availability_penalty"] = avail_penalty

    # --- STAGE 10: Domain Risk Engine ---
    domain_penalties = []
    if is_pure_consulting: domain_penalties.append(15)
    
    # Simple check for LangChain only:
    has_langchain = any("langchain" in s.get("name", "").lower() for s in cand.get("skills", []))
    has_t1 = t1_score > 5
    if has_langchain and not has_t1: domain_penalties.append(20)
    
    domain_penalty = max(domain_penalties) if domain_penalties else 0.0
    trace["risks"]["domain_penalty"] = domain_penalty

    if is_research_only and tech_fit > 0 and sum(c["production"] for c in trace["capabilities"].values()) < 0.5:
        trace["gates"].append("Research Only + No Production")

    # --- STAGE 11: Final Score ---
    final = (trace["technical_fit"] * trace["behavior"]["final_multiplier"] * trace["credibility"]["final_multiplier"]) - max(avail_penalty, domain_penalty)
    trace["final_score"] = final
    cand["final_score"] = final
    
    # --- STAGE 14: Reasoning Generator ---
    facts = []
    if t1_score > 30: facts.append("Strong Tier 1 capabilities (Retrieval/Ranking).")
    if bonus >= 5: facts.append("Product company background.")
    if beh_mult < 0.9: facts.append(f"Behavioral flags (Response rate: {sig.get('recruiter_response_rate')}).")
    if avail_penalty > 0: facts.append("High availability risk.")
    trace["reasoning_facts"] = facts

    return cand

def rank_candidates(input_file: str, output_file: str, top_n: int = 100):
    print(f"Processing candidates from {input_file}...")
    valid_candidates = []
    
    with open(input_file, "r", encoding="utf-8") as f, mp.Pool() as pool:
        # We read line by line and use imap_unordered for fast streaming
        for cand in pool.imap_unordered(process_candidate, f, chunksize=1000):
            if cand is not None:
                # Stage 12: Gate Filter
                if not cand["trace"]["gates"]:
                    valid_candidates.append(cand)
    
    print(f"Processed {len(valid_candidates)} valid candidates.")
    
    # Stage 13: Sorting
    valid_candidates.sort(
        key=lambda x: (
            x["final_score"],
            x["trace"]["credibility"]["final_multiplier"],
            x["trace"]["behavior"]["final_multiplier"],
            x["trace"]["technical_fit"],
            x["candidate_id"]
        ),
        reverse=True
    )
    
    top_candidates = valid_candidates[:top_n]
    
    # Output
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(top_candidates, out, indent=2)
    print(f"Top {top_n} candidates written to {output_file}.")

if __name__ == "__main__":
    import time
    start_time = time.time()
    rank_candidates("candidates.jsonl", "ranked_top_100.json", top_n=100)
    print(f"Completed in {time.time() - start_time:.2f} seconds.")
