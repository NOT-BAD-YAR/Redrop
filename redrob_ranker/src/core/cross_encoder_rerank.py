import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_MODEL_DIR = os.path.join(ROOT, "models", "cross-encoder-ms-marco-MiniLM-L6-v2")
HUB_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"
JD_PATH = os.path.join(ROOT, "data", "Job Description.md")

STAGE1_WEIGHT = 0.75
CROSS_WEIGHT = 0.25


def build_candidate_text(cand: Dict[str, Any]) -> str:
    """Schema-aware candidate text builder (same fields as embedding precompute)."""
    profile = cand.get("profile", {}) or {}
    skill_names = " ".join(s.get("name", "") for s in cand.get("skills", []) or [])
    career_text = " ".join(
        " ".join(
            filter(
                None,
                [
                    entry.get("title", ""),
                    entry.get("company", ""),
                    entry.get("description", ""),
                ],
            )
        )
        for entry in cand.get("career_history", []) or []
    )
    return " ".join(
        filter(
            None,
            [
                profile.get("current_title", ""),
                profile.get("headline", ""),
                profile.get("summary", ""),
                skill_names,
                career_text,
            ],
        )
    )


def load_jd_text(jd_path: Optional[str] = None) -> str:
    path = jd_path or JD_PATH
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_cross_encoder(model_path_or_name: Optional[str] = None) -> Optional[Any]:
    """Load CrossEncoder from local bundle or hub. Returns None if unavailable."""
    from sentence_transformers import CrossEncoder

    candidates = []
    if model_path_or_name:
        candidates.append(model_path_or_name)
    if os.path.isdir(LOCAL_MODEL_DIR):
        candidates.append(LOCAL_MODEL_DIR)
    candidates.append(HUB_MODEL_NAME)

    seen = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        try:
            if path == LOCAL_MODEL_DIR and not os.path.isdir(path):
                continue
            model = CrossEncoder(path, device="cpu")
            logger.info("Loaded cross-encoder from %s", path)
            return model
        except Exception as exc:
            logger.warning("Failed to load cross-encoder from %s: %s", path, exc)

    return None


def rerank_top_k(
    jd_text: str,
    top_candidates: List[Dict[str, Any]],
    model: Any,
    batch_size: int = 16,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Rerank Stage-1 top pool with cross-encoder scores fused into final_score."""
    if model is None or not top_candidates:
        return top_candidates, False

    pairs = [(jd_text, build_candidate_text(cand)) for cand in top_candidates]
    scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=False)
    scores = np.asarray(scores, dtype=np.float64)

    min_score = float(scores.min())
    max_score = float(scores.max())

    for cand, raw_score in zip(top_candidates, scores):
        cross_norm = (float(raw_score) - min_score) / (max_score - min_score + 1e-8)
        stage1_score = float(cand.get("final_score", cand.get("trace", {}).get("final_score", 0.0)))

        trace = cand.setdefault("trace", {})
        trace["stage1_score"] = stage1_score
        trace["cross_score"] = float(raw_score)
        trace["cross_norm"] = cross_norm
        rerank_score = STAGE1_WEIGHT * stage1_score + CROSS_WEIGHT * cross_norm
        trace["rerank_score"] = rerank_score
        trace["final_score"] = rerank_score
        cand["final_score"] = rerank_score

    top_candidates.sort(
        key=lambda x: (
            -x.get("final_score", 0.0),
            -x.get("trace", {}).get("cross_score", 0.0),
            x.get("candidate_id", ""),
        )
    )
    return top_candidates, True
