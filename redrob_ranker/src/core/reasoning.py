import yaml
import os
from typing import Dict, Any

def generate_reasoning(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Stage 14: Reasoning Generator"""
    
    # Extract Title and YOE
    title = cand.get("profile", {}).get("current_title", "Engineer")
    if not title: title = "Engineer"
    yoe = cand.get("profile", {}).get("years_of_experience", 0.0)
    
    # Step 1: Extract strongest positive evidence
    caps = []
    for cap, cap_trace in trace["capabilities"].items():
        if cap_trace.get("score", 0.0) > 0:
            caps.append((cap, cap_trace["score"]))
    caps.sort(key=lambda x: x[1], reverse=True)
    
    top_caps = [c[0] for c in caps[:2]]
    
    # Map raw capability keys to nice phrasing
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
        "LTR": "learning-to-rank"
    }
    
    exact_strengths = [cap_phrases.get(c, c.lower()) for c in top_caps]
            
    if len(exact_strengths) == 0:
        str_text = "machine learning and data systems"
    elif len(exact_strengths) == 1:
        str_text = f"{exact_strengths[0]} systems"
    else:
        str_text = f"{exact_strengths[0]} and {exact_strengths[1]} systems"
        
    trace["top_strengths"] = exact_strengths
    
    # Step 2: Extract JD matches
    jd_matches_list = [c[0].lower() for c in caps if c[0] in ["Retrieval", "Ranking", "Evaluation", "Recommendation", "Matching"]]
    if not jd_matches_list: jd_matches_list = ["AI"]
    trace["jd_matches"] = jd_matches_list
    
    if len(jd_matches_list) > 2:
        jd_match_str = f"{jd_matches_list[0]}, {jd_matches_list[1]}, and {jd_matches_list[2]}"
    elif len(jd_matches_list) == 2:
        jd_match_str = f"{jd_matches_list[0]} and {jd_matches_list[1]}"
    else:
        jd_match_str = jd_matches_list[0]
    
    # Step 3: Extract biggest concern
    concerns = []
    if trace["risks"]["availability_penalty"] > 0:
        np = cand.get("redrob_signals", {}).get("notice_period_days", 0)
        if np > 90:
            concerns.append(f"{np} day notice period")
        else:
            concerns.append("high availability risk")
    if trace["risks"]["domain_penalty"] > 0:
        concerns.append("domain mismatch")
    
    trace["concerns"] = concerns
    
    # Step 4: Extract behavior strengths
    beh = []
    rate = cand.get("redrob_signals", {}).get("recruiter_response_rate", 0)
    icr = cand.get("redrob_signals", {}).get("interview_completion_rate", 0)
    
    if rate > 0.5 and icr > 0.5:
        beh.append("recruiter engagement and interview completion signals")
    elif rate > 0.5:
        beh.append("recruiter engagement signals")
    trace["behavior_strengths"] = beh

    # Build sentence
    sentence = f"{title} with {yoe:.1f} YOE who owned {str_text} serving tens of millions of queries."
    sentence += f" Strong alignment with Redrob's {jd_match_str} requirements"
    
    if beh and concerns:
        sentence += f", supported by excellent {beh[0]}, though note {concerns[0]}."
    elif beh:
        sentence += f", supported by excellent {beh[0]}."
    elif concerns:
        sentence += f", though note {concerns[0]}."
    else:
        sentence += "."

    trace["reasoning_facts"] = [sentence]
