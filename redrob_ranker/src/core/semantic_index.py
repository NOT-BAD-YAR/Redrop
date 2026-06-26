import json
import logging
import os
from typing import Dict, Optional, Tuple

import numpy as np
import yaml

logger = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARTIFACTS_DIR = os.path.join(ROOT, "artifacts")
CONFIG_PATH = os.path.join(ROOT, "config", "weights.yaml")

DEFAULT_FUSION_WEIGHTS = {
    "semantic": 0.30,
    "technical_fit": 0.30,
    "bm25": 0.20,
    "behavioral": 0.20,
}


def load_fusion_weights() -> Dict[str, float]:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        weights = cfg.get("fusion_weights", {})
        return {k: float(weights.get(k, DEFAULT_FUSION_WEIGHTS[k])) for k in DEFAULT_FUSION_WEIGHTS}
    except (OSError, TypeError, ValueError):
        return dict(DEFAULT_FUSION_WEIGHTS)


def load_semantic_artifacts() -> Tuple[Dict[str, np.ndarray], Optional[np.ndarray], bool]:
    """Load pre-computed embeddings from disk. Returns (embed_map, jd_vec, ready)."""
    emb_path = os.path.join(ARTIFACTS_DIR, "candidate_embeddings.npy")
    ids_path = os.path.join(ARTIFACTS_DIR, "candidate_ids.json")
    jd_path = os.path.join(ARTIFACTS_DIR, "jd_embedding.npy")

    if not os.path.isfile(emb_path):
        logger.warning(
            "artifacts/candidate_embeddings.npy not found — semantic_score will be 0.0"
        )
        return {}, None, False

    embeddings = np.load(emb_path)
    with open(ids_path, "r", encoding="utf-8") as f:
        candidate_ids = json.load(f)

    if len(candidate_ids) != embeddings.shape[0]:
        logger.warning(
            "candidate_ids.json length (%d) != embeddings rows (%d) — semantic disabled",
            len(candidate_ids),
            embeddings.shape[0],
        )
        return {}, None, False

    embed_map = dict(zip(candidate_ids, embeddings))

    if not os.path.isfile(jd_path):
        logger.warning(
            "artifacts/jd_embedding.npy not found — semantic_score will be 0.0"
        )
        return embed_map, None, False

    jd_embedding = np.load(jd_path)[0]

    logger.info(
        "Loaded semantic index: %d candidates, JD vector dim %d",
        len(embed_map),
        jd_embedding.shape[0],
    )
    return embed_map, jd_embedding, True


def semantic_similarity(
    cand_id: str,
    embed_map: Dict[str, np.ndarray],
    jd_vec: Optional[np.ndarray],
    semantic_ready: bool,
) -> float:
    if not semantic_ready or jd_vec is None:
        return 0.0
    vec = embed_map.get(cand_id)
    if vec is None:
        return 0.0
    return float(np.dot(vec, jd_vec))


def fuse_final_score(
    semantic_score: float,
    technical_fit: float,
    bm25_score: float,
    behavioral_multiplier: float,
    fusion_weights: Optional[Dict[str, float]] = None,
) -> float:
    w = fusion_weights or load_fusion_weights()
    return (
        w["semantic"] * semantic_score
        + w["technical_fit"] * (technical_fit / 100.0)
        + w["bm25"] * bm25_score
        + w["behavioral"] * behavioral_multiplier
    )
