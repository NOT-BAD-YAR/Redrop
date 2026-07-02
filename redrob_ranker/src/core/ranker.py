import json
import logging
import multiprocessing as mp
import os
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from src.core.behavior_engine import calculate_behavior
from src.core.cross_encoder_rerank import load_cross_encoder, load_jd_text, rerank_top_k
from src.core.extractor import extract_evidence
from src.core.normalizer import normalize_candidate
from src.core.reasoning import generate_reasoning, render_reasoning
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


def _iter_candidate_items(input_path: str):
    if os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                if file.endswith(".jsonl"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                yield line
                elif file.endswith(".json"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if not content:
                        continue
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            for obj in data:
                                yield obj
                        elif isinstance(data, dict):
                            yield data
                    except Exception:
                        for line in content.splitlines():
                            if line.strip():
                                yield line
    else:
        if input_path.endswith(".json") and not input_path.endswith(".jsonl"):
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    for obj in data:
                        yield obj
                elif isinstance(data, dict):
                    yield data
                return
            except Exception:
                pass
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield line


def process_candidate(item: Any) -> Any:
    if isinstance(item, str):
        if not item.strip():
            return None
        try:
            cand = json.loads(item)
        except Exception:
            return None
    elif isinstance(item, dict):
        cand = item
    else:
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

    sig = cand.get("redrob_signals") or {}
    sal = sig.get("expected_salary_range_inr_lpa") or {}
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
            cand_id, _EMBED_MAP, _JD_VEC, _SEMANTIC_READY, cand=cand
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
    def __init__(
        self,
        input_file: str,
        output_file: str,
        top_n: int = 100,
        use_cross_encoder: bool = False,
        rerank_pool_size: int = 1500,
        cross_encoder_batch_size: int = 16,
    ):
        self.input_file = input_file
        self.output_file = output_file
        self.top_n = top_n
        self.use_cross_encoder = use_cross_encoder
        self.rerank_pool_size = rerank_pool_size
        self.cross_encoder_batch_size = cross_encoder_batch_size
        self.embed_map: Dict[str, Any] = {}
        self.jd_vec: Optional[Any] = None
        self.semantic_ready: bool = False
        self.fusion_weights: Dict[str, float] = load_fusion_weights()
        self.stage1_seconds: float = 0.0
        self.stage2_seconds: float = 0.0

    def _load_semantic_artifacts(self) -> None:
        print("Loading semantic artifacts from disk...")
        self.embed_map, self.jd_vec, self.semantic_ready = load_semantic_artifacts()
        if self.semantic_ready:
            print(f"Semantic index ready: {len(self.embed_map):,} candidate vectors")
        else:
            print("Semantic index unavailable — semantic_score will be 0.0")

    def run(self) -> Tuple[float, float]:
        stage1_start = time.time()
        self._load_semantic_artifacts()

        print(f"Processing candidates from {self.input_file}...")
        valid_candidates: List[Dict[str, Any]] = []

        with mp.Pool(
            initializer=_init_worker,
            initargs=(
                self.embed_map,
                self.jd_vec,
                self.fusion_weights,
                self.semantic_ready,
            ),
        ) as pool:
            for cand in pool.imap_unordered(process_candidate, _iter_candidate_items(self.input_file), chunksize=1000):
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

        self.stage1_seconds = time.time() - stage1_start
        print(f"Stage 1 completed in {self.stage1_seconds:.2f} seconds.")

        stage2_start = time.time()
        if self.use_cross_encoder:
            rerank_pool = valid_candidates[: self.rerank_pool_size]
            model = load_cross_encoder()
            if model is None:
                print("Cross-encoder model unavailable — skipping Stage 2 rerank.")
                top_candidates = valid_candidates[: self.top_n]
            else:
                jd_text = load_jd_text()
                reranked_pool, ok = rerank_top_k(
                    jd_text,
                    rerank_pool,
                    model,
                    batch_size=self.cross_encoder_batch_size,
                )
                if ok:
                    top_candidates = reranked_pool[: self.top_n]
                    self.stage2_seconds = time.time() - stage2_start
                    print(
                        f"Stage 2 cross-encoder rerank completed in "
                        f"{self.stage2_seconds:.2f} seconds "
                        f"({len(rerank_pool)} candidates)."
                    )
                else:
                    top_candidates = valid_candidates[: self.top_n]
        else:
            top_candidates = valid_candidates[: self.top_n]

        score_source = top_candidates if self.use_cross_encoder else valid_candidates
        max_score = max((float(c.get("final_score", 0.0) or 0.0) for c in score_source), default=1.0)
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
                reasoning = render_reasoning(cand, cand.get("trace", {}), rank)
                writer.writerow([cand_id, rank, score, reasoning])

        print(f"Top {self.top_n} candidates written to {self.output_file}.")
        return self.stage1_seconds, self.stage2_seconds
