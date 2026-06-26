import json
import multiprocessing as mp
from typing import Dict, Any, List
from dataclasses import asdict

from src.models.trace import Trace
from src.core.normalizer import normalize_candidate
from src.core.validator import validate_evidence
from src.core.extractor import extract_evidence
from src.core.scorer import score_technical_fit, apply_experience_penalty, WEIGHTS as CAPABILITIES
from src.core.behavior_engine import calculate_behavior
from src.core.risk_engine import evaluate_risks
from src.core.reasoning import generate_reasoning

def process_candidate(line: str) -> Any:
    if not line.strip(): return None
    try:
        cand = json.loads(line)
    except Exception:
        return None
        
    trace = asdict(Trace())
    for cap in CAPABILITIES.keys():
        trace["capabilities"][cap] = {
            "score": 0.0, "best_role_evidence": "", "ownership": 0.0, 
            "production": 0.0, "raw_evidence_hits": 0, "exact_matches": []
        }
            
    cand["trace"] = trace
    
    try:
        # Pipeline execution
        normalize_candidate(cand)
        validate_evidence(cand, trace)
        extract_evidence(cand, trace)
        score_technical_fit(cand, trace)
        apply_experience_penalty(cand, trace)
        calculate_behavior(cand, trace)
        evaluate_risks(cand, trace)
        
        # Stage 11: Final Score
        final = (
            trace["technical_fit"]
            * trace["behavior"]["final_multiplier"]
            * trace["credibility"]["final_multiplier"]
        )
        final *= trace["behavior"].get("active_days_multiplier", 1.0)
        final -= max(trace["risks"]["availability_penalty"], trace["risks"]["domain_penalty"])
        
        trace["final_score"] = final
        cand["final_score"] = final
        
        generate_reasoning(cand, trace)
        
        return cand
    except Exception as e:
        # Fallback for unexpected parsing errors
        return None

class CandidateRanker:
    def __init__(self, input_file: str, output_file: str, top_n: int = 100):
        self.input_file = input_file
        self.output_file = output_file
        self.top_n = top_n
        
    def run(self):
        print(f"Processing candidates from {self.input_file}...")
        valid_candidates = []
        
        with open(self.input_file, "r", encoding="utf-8") as f, mp.Pool() as pool:
            for cand in pool.imap_unordered(process_candidate, f, chunksize=1000):
                if cand is not None:
                    # Stage 12: Gate Filter
                    if not cand["trace"]["gates"]:
                        valid_candidates.append(cand)
                        
        print(f"Processed {len(valid_candidates)} valid candidates. Sorting...")

        # Stage 13: Sort by score descending; stable tie-break via candidate_id ascending.
        valid_candidates.sort(key=lambda x: x["candidate_id"])
        valid_candidates.sort(
            key=lambda x: (
                x["final_score"],
                x["trace"]["credibility"]["final_multiplier"],
                x["trace"]["behavior"]["final_multiplier"],
                x["trace"]["technical_fit"],
            ),
            reverse=True,
        )

        top_candidates = valid_candidates[: self.top_n]

        # Calculate top score for normalization
        max_score = max((c.get("final_score", 0.0) for c in valid_candidates), default=60.0)
        if max_score == 0:
            max_score = 60.0

        def _rounded_csv_score(cand: Dict[str, Any]) -> float:
            raw_score = cand.get("final_score", 0.0)
            normalized = min(1.0, max(0.0, raw_score / max_score))
            return round(normalized, 3)

        # Re-order top 100 so equal 3-decimal CSV scores tie-break by candidate_id ascending.
        top_candidates.sort(
            key=lambda x: (-_rounded_csv_score(x), x.get("candidate_id", ""))
        )

        # Write to CSV
        import csv
        with open(self.output_file, "w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for idx, cand in enumerate(top_candidates):
                rank = idx + 1
                cand_id = cand.get("candidate_id", "")
                score = f"{_rounded_csv_score(cand):.3f}"
                reasoning = " ".join(cand.get("trace", {}).get("reasoning_facts", []))
                writer.writerow([cand_id, rank, score, reasoning])
            
        print(f"Top {self.top_n} candidates written to {self.output_file}.")
