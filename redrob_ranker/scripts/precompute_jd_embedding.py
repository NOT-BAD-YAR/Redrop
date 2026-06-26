#!/usr/bin/env python3
"""Encode the job description once and save jd_embedding.npy for offline ranking."""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.core.embeddings import get_embedding_model  # noqa: E402

JD_PATH = os.path.join(ROOT, "data", "Job Description.md")
OUT_PATH = os.path.join(ROOT, "artifacts", "jd_embedding.npy")


def main() -> None:
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(JD_PATH, "r", encoding="utf-8") as f:
        jd_text = f.read()

    model = get_embedding_model()
    embedding = model.encode(
        [jd_text],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    np.save(OUT_PATH, embedding)
    print(f"Saved {OUT_PATH} with shape {embedding.shape}")


if __name__ == "__main__":
    main()
