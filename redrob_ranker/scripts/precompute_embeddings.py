#!/usr/bin/env python3
"""Pre-compute candidate embeddings offline (run once, ~15–45 min on CPU)."""

import json
import os

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ROOT, "models", "all-MiniLM-L6-v2")
DATA_PATH = os.path.join(ROOT, "data", "candidates.jsonl")
ARTIFACTS_DIR = os.path.join(ROOT, "artifacts")


def build_candidate_text(cand: dict) -> str:
    profile = cand.get("profile", {})
    skill_names = " ".join(s.get("name", "") for s in cand.get("skills", []))
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
        for entry in cand.get("career_history", [])
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


def main() -> None:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    model = SentenceTransformer(MODEL_DIR, device="cpu")

    candidates: list[str] = []
    ids: list[str] = []

    with open(DATA_PATH, encoding="utf-8") as f:
        for line in tqdm(f, desc="Loading"):
            cand = json.loads(line)
            candidates.append(build_candidate_text(cand))
            ids.append(cand["candidate_id"])

    print(f"Encoding {len(candidates):,} profiles... (15–45 min on CPU)")
    embeddings = model.encode(
        candidates,
        batch_size=128,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    np.save(os.path.join(ARTIFACTS_DIR, "candidate_embeddings.npy"), embeddings)
    with open(os.path.join(ARTIFACTS_DIR, "candidate_ids.json"), "w", encoding="utf-8") as f:
        json.dump(ids, f)

    print(f"Saved: {embeddings.shape}")


if __name__ == "__main__":
    main()
