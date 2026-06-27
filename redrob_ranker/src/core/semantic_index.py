import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

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
            data = yaml.safe_load(f)
            if data and "fusion_weights" in data:
                return data["fusion_weights"]
    except Exception as e:
        logger.warning("Failed to load weights.yaml (%s) — using defaults", e)
    return dict(DEFAULT_FUSION_WEIGHTS)


def load_semantic_artifacts() -> Tuple[Dict[str, np.ndarray], Optional[np.ndarray], bool]:
    """Load pre-computed embeddings from disk. Returns (embed_map, jd_vec, ready)."""
    emb_path = os.path.join(ARTIFACTS_DIR, "candidate_embeddings.npy")
    ids_path = os.path.join(ARTIFACTS_DIR, "candidate_ids.json")
    jd_path = os.path.join(ARTIFACTS_DIR, "jd_embedding.npy")

    embed_map = {}
    if os.path.isfile(emb_path) and os.path.isfile(ids_path):
        try:
            embeddings = np.load(emb_path, allow_pickle=True)
            with open(ids_path, "r", encoding="utf-8") as f:
                candidate_ids = json.load(f)
            if len(candidate_ids) == embeddings.shape[0]:
                embed_map = dict(zip(candidate_ids, embeddings))
            else:
                logger.warning(
                    "candidate_ids length (%d) != embeddings rows (%d)",
                    len(candidate_ids),
                    embeddings.shape[0],
                )
        except Exception as e:
            logger.warning("Failed loading candidate embeddings: %s", e)

    if not os.path.isfile(jd_path):
        logger.warning("artifacts/jd_embedding.npy not found — semantic_score will be 0.0")
        return embed_map, None, False

    try:
        jd_embedding = np.load(jd_path, allow_pickle=True)[0]
    except Exception as e:
        logger.warning("Failed loading jd_embedding.npy: %s", e)
        return embed_map, None, False

    logger.info(
        "Loaded semantic index: %d precomputed candidates, JD vector dim %d",
        len(embed_map),
        jd_embedding.shape[0],
    )
    return embed_map, jd_embedding, True


def semantic_similarity(
    cand_id: str,
    embed_map: Dict[str, np.ndarray],
    jd_vec: Optional[np.ndarray],
    semantic_ready: bool,
    cand: Optional[Dict[str, Any]] = None,
) -> float:
    if not semantic_ready or jd_vec is None:
        return 0.0
    vec = embed_map.get(cand_id)
    if vec is None and cand is not None:
        try:
            from src.core.embeddings import get_embedding_model
            from src.core.cross_encoder_rerank import build_candidate_text
            model = get_embedding_model()
            text = build_candidate_text(cand)
            vec = model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
            embed_map[cand_id] = vec
        except Exception as e:
            logger.warning("Dynamic fallback embedding failed for %s: %s", cand_id, e)
            return 0.0
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
