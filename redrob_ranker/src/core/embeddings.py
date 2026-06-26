import os
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models", "all-MiniLM-L6-v2")
)


@lru_cache(maxsize=1)
def get_embedding_model() -> "SentenceTransformer":
    """Load bundled MiniLM from disk only — no Hugging Face Hub access at runtime."""
    if not os.path.isfile(os.path.join(MODEL_DIR, "model.safetensors")):
        raise FileNotFoundError(
            f"Offline embedding model not found at {MODEL_DIR}. "
            "Bundle redrob_ranker/models/all-MiniLM-L6-v2 in the repo."
        )

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_DIR, device="cpu")
