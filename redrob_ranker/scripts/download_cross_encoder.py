#!/usr/bin/env python3
"""Download cross-encoder model for offline Stage 2 reranking."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT_DIR = os.path.join(ROOT, "models", "cross-encoder-ms-marco-MiniLM-L6-v2")
HUB_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"


def main() -> None:
    os.makedirs(os.path.dirname(OUT_DIR), exist_ok=True)
    print(f"Downloading {HUB_MODEL_NAME} to {OUT_DIR} ...")

    from sentence_transformers import CrossEncoder

    model = CrossEncoder(HUB_MODEL_NAME, device="cpu")
    model.save(OUT_DIR)
    print(f"Saved cross-encoder model to {OUT_DIR}")


if __name__ == "__main__":
    main()
