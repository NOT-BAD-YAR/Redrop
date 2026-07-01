# Redrob Candidate Ranking System

This project is a structured, highly optimized multi-stage candidate ranking system built to identify the best Senior AI Engineer profiles from a dataset of 100,000+ candidates. It processes candidates against a 14-stage filtering and scoring pipeline designed to weed out keyword honeypots and elevate candidates with genuine, scalable production experience.

## Architecture

The project is structured into multiple core modules handling specific stages of the scoring pipeline:

```text
redrob_ranker/
├── artifacts/               # Pre-computed embeddings (offline ranking)
│   ├── candidate_embeddings.npy
│   ├── candidate_ids.json
│   └── jd_embedding.npy
├── data/                    # Symlink candidates.jsonl + Job Description.md
├── models/
│   ├── all-MiniLM-L6-v2/    # Bundled offline embedding model (~87 MB, no internet at runtime)
│   └── cross-encoder-ms-marco-MiniLM-L6-v2/  # Bundled Stage 2 rerank model (~87 MB, offline)
├── scripts/
│   ├── precompute_embeddings.py
│   ├── precompute_jd_embedding.py
│   └── download_cross_encoder.py
├── config/                  
│   ├── dictionaries.yaml    # Stores all RegEx keyword patterns for extraction
│   ├── templates.yaml       # Reasoning generator templates
│   └── weights.yaml         # Mathematical limits, caps, and risk penalties
├── src/
│   ├── core/
│   │   ├── behavior_engine.py  # Stage 8: Multiplicative behavior scoring using Redrob signals
│   │   ├── extractor.py        # Stages 2-5: Evidence Extraction, Ownership, Recency & Production Scoring
│   │   ├── normalizer.py       # Stage 0: Schema validation & date normalization
│   │   ├── ranker.py           # Stages 11-13: Pipeline Orchestrator & Multiprocessing map
│   │   ├── reasoning.py        # Stage 14: Non-LLM Template-driven Reasoning Generator
│   │   ├── risk_engine.py      # Stages 9-10: Availability and Domain Risk Engines (Gates & Penalties)
│   │   ├── scorer.py           # Stages 6-7: Aggregates capability scores into final Technical Fit
│   │   ├── semantic_index.py   # Loads pre-computed embeddings + fusion scoring
│   │   ├── cross_encoder_rerank.py  # Stage 2: cross-encoder rerank on top 1500
│   │   └── validator.py        # Stage 1: Evidence Validation (Consistency & Credibility)
│   ├── models/
│   │   ├── candidate.py        # Type hints for candidate JSON objects
│   │   └── trace.py            # Pydantic models mapping the formal Trace Schema
│   └── main.py                 # CLI Execution Point
├── output/                     # Export directory for ranked JSON output
└── requirements.txt            # Project dependencies (pydantic, pyyaml)
```

## Setup & Execution

### Mac setup (Python 3.11 required)

Do **not** use system Python 3.14 — `pydantic` will fail to install. Use Homebrew Python 3.11:

```bash
cd Redrop/redrob_ranker
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Data is symlinked under `data/` (465 MB `candidates.jsonl` is not copied):

```bash
# Already set up if you followed Phase 1; recreate with:
mkdir -p data
ln -sf "../../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl" data/candidates.jsonl
ln -sf "../../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/Job Description.md" "data/Job Description.md"
```

Activate the venv in every new terminal: `source .venv/bin/activate`

### Offline embedding model (judges: no internet)

The MiniLM model is **committed under `models/all-MiniLM-L6-v2/`** (~87 MB). Do not download from Hugging Face at runtime.

---

## Setup

Judges clone the repo and run — **no pre-computation needed**. Candidate embeddings are shipped via Git LFS.

### Step 1 — Install dependencies

```bash
cd Redrop/redrob_ranker
source .venv/bin/activate   # create venv first — see Mac setup above
pip install -r requirements.txt
```

After clone, pull LFS files:

```bash
git lfs pull
```

### Step 2 — Run ranker (embeddings pre-computed, no wait)

```bash
source .venv/bin/activate

python src/main.py \
  --candidates ./data/candidates.jsonl \
  --out ./output/submission.csv

python validate_submission.py ./output/submission.csv
```

### Optional — Stage 2 cross-encoder rerank

Stage 1 (default) scores all valid candidates and outputs the top 100. Stage 2 reranks only the **top 1500** Stage-1 candidates with a cross-encoder (`cross-encoder/ms-marco-MiniLM-L6-v2`), then outputs the final top 100.

The cross-encoder model is **committed under `models/cross-encoder-ms-marco-MiniLM-L6-v2/`** (~87 MB). No download needed after clone.

To re-download or refresh the model:

```bash
source .venv/bin/activate
python scripts/download_cross_encoder.py
```

This saves the model to `models/cross-encoder-ms-marco-MiniLM-L6-v2/`.

**Run with Stage 2 enabled:**

```bash
source .venv/bin/activate

python src/main.py \
  --candidates ./data/candidates.jsonl \
  --out ./output/submission.csv \
  --use-cross-encoder true
```

If the cross-encoder model is missing, the ranker logs a warning and falls back to Stage 1 ordering. Stage 2 uses CPU only, batch size 16, and fuses scores as `0.75 * stage1_score + 0.25 * cross_norm`.

> **Note:** `artifacts/candidate_embeddings.npy` (146 MB) is stored via **Git LFS**.
> It downloads automatically on `git clone` (or `git lfs pull`). No 20-minute pre-computation needed.

Also bundled in the repo (small files, regular git):
- `artifacts/candidate_ids.json` — 100K aligned candidate IDs
- `artifacts/jd_embedding.npy` — JD vector for semantic scoring
- `models/all-MiniLM-L6-v2/` — offline embedding model (~87 MB)

### Optional — Re-generate embeddings from scratch (~20 min)

Only needed if you change the embedding model or candidate text builder.

```bash
source .venv/bin/activate
python scripts/precompute_embeddings.py
python scripts/precompute_jd_embedding.py
```

**Fusion weights** (`config/weights.yaml`):

```yaml
fusion_weights:
  semantic: 0.30
  technical_fit: 0.30
  bm25: 0.20
  behavioral: 0.20
```

If `artifacts/candidate_embeddings.npy` is missing, the ranker logs a warning and continues with `semantic_score = 0.0`.

---

## Processing Stages

- **Stage 0 (Schema):** Ensures robust dates via timestamp conversion (`normalizer.py`).
- **Stage 1 (Evidence Validation):** Flags invalid timelines and generates base Credibility (`validator.py`).
- **Stages 2-5 (Evidence & Modifiers):** Scans profile text against 3 Tiers of Technical taxonomy, applying modifiers for Recency, Ownership ("built" vs "assisted"), and Production scale (`extractor.py`).
- **Stages 6-7 (Technical Fit):** Caps taxonomy points to prevent over-indexing on keywords. Adds Product Company bonuses (`scorer.py`).
- **Stage 8 (Behavior):** Evaluates Intent, Reachability, and Demand using a multiplicative modifier (`behavior_engine.py`).
- **Stages 9-10 (Risks & Gates):** Adds heavy point penalties for low response rates or consulting-only backgrounds. Applies hard removal Gates (`risk_engine.py`).
- **Stages 11-13 (Rank Orchestration):** Fuses semantic + technical fit + BM25 + behavioral scores; sorts Top 100 (`ranker.py` + `semantic_index.py`).
- **Stage 2 (optional cross-encoder):** Reranks top 1500 Stage-1 candidates with JD–profile cross-encoder scores (`cross_encoder_rerank.py`).
- **Stage 14 (Reasoning):** Outputs human-readable logic templates appended to the trace (`reasoning.py`).
