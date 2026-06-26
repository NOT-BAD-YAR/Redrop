import json
import logging
import multiprocessing as mp
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from src.core.behavior_engine import calculate_behavior
from src.core.extractor import extract_evidence
from src.core.normalizer import normalize_candidate
from src.core.reasoning import generate_reasoning
from src.core.risk_engine import evaluate_risks
from src.core.scorer import (
    apply_experience_penalty,
    apply_seniority_penalty,
    apply_title_trap_penalties,
    score_technical_fit,
    WEIGHTS as CAPABILITIES,
)
from src.core.semantic_index import (
    fuse_final_score,
    load_fusion_weights,
    load_semantic_artifacts,
    semantic_similarity,
)
from src.core.validator import validate_evidence
from src.models.trace import Trace

logger = logging.getLogger(__name__)

# Worker globals populated once per process via Pool initializer.
_EMBED_MAP: Dict[str, Any] = {}
_JD_VEC: Optional[Any] = None
_FUSION_WEIGHTS: Dict[str, float] = {}
_SEMANTIC_READY: bool = False


def _init_worker(
    embed_map: Dict[str, Any],
    jd_vec: Optional[Any],
    fusion_weights: Dict[str, float],
    semantic_ready: bool,
) -> None:
    global _EMBED_MAP, _JD_VEC, _FUSION_WEIGHTS, _SEMANTIC_READY
    _EMBED_MAP = embed_map
    _JD_VEC = jd_vec
    _FUSION_WEIGHTS = fusion_weights
    _SEMANTIC_READY = semantic_ready


def process_candidate(line: str) -> Any:
    if not line.strip():
        return None
    try:
        cand = json.loads(line)
    except Exception:
        return None

    trace = asdict(Trace())
    for cap in CAPABILITIES.keys():
        trace["capabilities"][cap] = {
            "score": 0.0,
            "best_role_evidence": "",
            "ownership": 0.0,
            "production": 0.0,
            "raw_evidence_hits": 0,
            "exact_matches": [],
        }

    cand["trace"] = trace

    sig = cand.get("redrob_signals", {})
    sal = sig.get("expected_salary_range_inr_lpa", {})
    sal_min = sal.get("min", 0) or 0
    sal_max = sal.get("max", 9999) or 9999
    if sal_min > sal_max:
        trace["gates"].append("Honeypot: salary_min > salary_max")
        return cand

    try:
        normalize_candidate(cand)
        validate_evidence(cand, trace)
        extract_evidence(cand, trace)
        score_technical_fit(cand, trace)
        apply_experience_penalty(cand, trace)
        apply_seniority_penalty(cand, trace)
        apply_title_trap_penalties(cand, trace)
        calculate_behavior(cand, trace)
        evaluate_risks(cand, trace)

        cand_id = cand.get("candidate_id", "")
        trace["semantic_score"] = semantic_similarity(
            cand_id, _EMBED_MAP, _JD_VEC, _SEMANTIC_READY
        )
        trace["bm25_score"] = 0.0

        final = fuse_final_score(
            semantic_score=trace["semantic_score"],
            technical_fit=trace["technical_fit"],
            bm25_score=trace["bm25_score"],
            behavioral_multiplier=trace["behavior"]["final_multiplier"],
            fusion_weights=_FUSION_WEIGHTS,
        )
        risk_penalty = max(
            trace["risks"]["availability_penalty"],
            trace["risks"]["domain_penalty"],
        )
        final = max(0.0, final - (risk_penalty / 100.0))
        final *= trace["behavior"].get("active_days_multiplier", 1.0)
        final = max(0.0, final - trace.get("seniority_penalty", 0.0))
        final *= trace.get("title_trap_multiplier", 1.0)

        trace["final_score"] = final
        cand["final_score"] = final

        generate_reasoning(cand, trace)

        return cand
    except Exception:
        return None


class CandidateRanker:
    def __init__(self, input_file: str, output_file: str, top_n: int = 100):
        self.input_file = input_file
        self.output_file = output_file
        self.top_n = top_n
        self.embed_map: Dict[str, Any] = {}
        self.jd_vec: Optional[Any] = None
        self.semantic_ready: bool = False
        self.fusion_weights: Dict[str, float] = load_fusion_weights()

    def _load_semantic_artifacts(self) -> None:
        print("Loading semantic artifacts from disk...")
        self.embed_map, self.jd_vec, self.semantic_ready = load_semantic_artifacts()
        if self.semantic_ready:
            print(f"Semantic index ready: {len(self.embed_map):,} candidate vectors")
        else:
            print("Semantic index unavailable — semantic_score will be 0.0")

    def run(self):
        self._load_semantic_artifacts()

        print(f"Processing candidates from {self.input_file}...")
        valid_candidates: List[Dict[str, Any]] = []

        with open(self.input_file, "r", encoding="utf-8") as f, mp.Pool(
            initializer=_init_worker,
            initargs=(
                self.embed_map,
                self.jd_vec,
                self.fusion_weights,
                self.semantic_ready,
            ),
        ) as pool:
            for cand in pool.imap_unordered(process_candidate, f, chunksize=1000):
                if cand is not None:
                    if not cand["trace"]["gates"]:
                        valid_candidates.append(cand)

        print(f"Processed {len(valid_candidates)} valid candidates. Sorting...")

        valid_candidates.sort(key=lambda x: x["candidate_id"])
        valid_candidates.sort(
            key=lambda x: (
                x["final_score"],
                x["trace"].get("semantic_score", 0.0),
                x["trace"]["technical_fit"],
                x["trace"]["behavior"]["final_multiplier"],
            ),
            reverse=True,
        )

        top_candidates = valid_candidates[: self.top_n]

        max_score = max((c.get("final_score", 0.0) for c in valid_candidates), default=1.0)
        if max_score == 0:
            max_score = 1.0

        def _rounded_csv_score(cand: Dict[str, Any]) -> float:
            raw_score = cand.get("final_score", 0.0)
            normalized = min(1.0, max(0.0, raw_score / max_score))
            return round(normalized, 3)

        top_candidates.sort(
            key=lambda x: (-_rounded_csv_score(x), x.get("candidate_id", ""))
        )

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
