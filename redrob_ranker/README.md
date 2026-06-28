# Redrob Candidate Ranking System — Technical Documentation

This project is a structured, highly optimized multi-stage candidate ranking system built to identify the best **Senior AI Engineer** profiles from a dataset of 100,000+ candidates. It evaluates profiles through a 14-stage scoring pipeline designed to weed out keyword honeypots and elevate candidates with genuine, scalable production engineering experience.

---

## Repository Architecture

```text
redrob_ranker/
├── .env.example             # Template for environment configuration
├── Dockerfile               # Container build instructions
├── docker-compose.yml       # Multi-container orchestration & volume mounting
├── requirements.txt         # Project Python dependencies
├── validate_submission.py     # Competition CSV output validator
├── artifacts/               # Pre-computed embeddings & IDs (shipped via Git LFS)
│   ├── candidate_embeddings.npy
│   ├── candidate_ids.json
│   └── jd_embedding.npy
├── config/                  # Declarative scoring and extraction rules
│   ├── dictionaries.yaml    # RegEx taxonomy & capability extraction patterns
│   ├── templates.yaml       # Reasoning template strings
│   └── weights.yaml         # Multipliers, penalties, and score fusion weights
├── data/                    # Candidate datasets & job description files
├── models/                  # Bundled offline AI models (no internet needed at runtime)
│   ├── all-MiniLM-L6-v2/    # Vector embedding model (~87 MB)
│   └── cross-encoder-ms-marco-MiniLM-L6-v2/ # Stage 2 reranking model (~87 MB)
├── scripts/                 # Auxiliary helper scripts
│   ├── precompute_embeddings.py     # Re-calculates candidate vector embeddings
│   ├── precompute_jd_embedding.py   # Re-calculates job description vector embedding
│   └── download_cross_encoder.py    # Downloads/refreshes the offline cross-encoder model
└── src/                     # Core application pipeline logic
    ├── core/
    │   ├── behavior_engine.py       # Stage 8: Market intent & reachability multipliers
    │   ├── cross_encoder_rerank.py  # Stage 2: Precision reranking engine
    │   ├── extractor.py             # Stages 2-5: Taxonomy & evidence extraction
    │   ├── normalizer.py            # Stage 0: Schema & date standardization
    │   ├── ranker.py                # Stages 11-13: Pipeline orchestrator & sorting
    │   ├── reasoning.py             # Stage 14: Non-LLM human-readable reasoning generator
    │   ├── risk_engine.py           # Stages 9-10: Domain risk gates & penalties
    │   ├── scorer.py                # Stages 6-7: Technical fit capability aggregation
    │   ├── semantic_index.py        # Vector similarity & fusion calculation
    │   └── validator.py             # Stage 1: Timeline & credibility validation
    ├── models/
    │   ├── candidate.py             # Pydantic data models for candidate structures
    │   └── trace.py                 # Execution trace schema definitions
    └── main.py                      # CLI Application Entry Point
```

---

## Setup Instructions

### 1. Prerequisites & Git LFS
Candidate vector embeddings are shipped via Git LFS. Ensure LFS is initialized after cloning:
```bash
git lfs pull
```

### 2. Virtual Environment (Python 3.11 recommended)
Create and activate a clean Python environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate
```

Install required libraries:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration (.env)
Copy `.env.example` to `.env` to manage default execution parameters cleanly:
```bash
cp .env.example .env
```
Inside `.env`, you can customize:
- `CANDIDATES_PATH`: Location of input dataset (default: `./data/candidates.jsonl`)
- `OUTPUT_PATH`: Destination for ranked CSV (default: `./output/submission.csv`)
- `TOP_N`: Number of candidates to output (default: `100`)
- `USE_CROSS_ENCODER`: Set to `true` to enable Stage 2 reranking on the top 500 candidates.

---

## Working Functions & Execution Modes

### Mode A: Standard Ranking Pipeline (Stage 1)
Runs the full 14-stage scoring engine using precomputed semantic vectors, BM25 matching, and technical fit taxonomy. Scores all 100K candidates and exports the Top 100:
```bash
python src/main.py
```

### Mode B: High-Precision Reranking (Stage 2)
To maximize ranking precision, Stage 2 applies a deep cross-encoder (`ms-marco-MiniLM-L6-v2`) to rerank the top 500 candidates from Stage 1 before exporting the final Top 100.
Run by setting `USE_CROSS_ENCODER=true` in `.env` or passing the CLI flag:
```bash
python src/main.py --use-cross-encoder true
```
*(Note: Uses offline models committed under `models/`. Runs on CPU with batch size 16.)*

### Output Validation
Validate that your output CSV conforms exactly to competition header rules, row count limits (100 rows), and non-increasing score order:
```bash
python validate_submission.py ./output/submission.csv
```

---

## Auxiliary Helper Scripts

If you modify the underlying dataset or want to update models, the project includes standalone utility scripts under `scripts/`:

1. **Recompute Candidate Embeddings:**
   Generates new semantic vector embeddings for all profiles in `data/candidates.jsonl` (~20 min run time):
   ```bash
   python scripts/precompute_embeddings.py
   ```

2. **Recompute Job Description Embedding:**
   Updates the reference embedding vector if the job description text changes:
   ```bash
   python scripts/precompute_jd_embedding.py
   ```

3. **Download / Refresh Cross-Encoder Model:**
   Fetches and caches the MS-MARCO MiniLM cross-encoder model locally into `models/`:
   ```bash
   python scripts/download_cross_encoder.py
   ```

---

## Processing Stages Overview

- **Stage 0 (Schema Normalization):** Sanitizes dates and standardizes data structures (`normalizer.py`).
- **Stage 1 (Evidence Validation):** Flags timeline anomalies and calculates base Credibility scores (`validator.py`).
- **Stages 2–5 (Taxonomy Extraction):** Scans profile text against 3 tiers of AI taxonomy (Retrieval, Ranking, Evaluation, Matching, etc.), adjusting for Recency, Ownership ("built" vs "assisted"), and Production scale (`extractor.py`).
- **Stages 6–7 (Technical Fit Aggregation):** Applies point caps to prevent keyword spamming and applies product company bonuses (`scorer.py`).
- **Stage 8 (Behavioral Engine):** Evaluates candidate market intent, reachability, and demand (`behavior_engine.py`).
- **Stages 9–10 (Risk & Gate Engine):** Penalizes consulting-only or theoretical backgrounds and enforces hard filtering gates (`risk_engine.py`).
- **Stages 11–13 (Rank Orchestration):** Fuses Semantic (30%), Technical Fit (30%), BM25 (20%), and Behavioral (20%) scores (`ranker.py`, `semantic_index.py`).
- **Stage 2 Option (Cross-Encoder):** Blends Stage 1 scores with cross-encoder similarity for the top 500 candidates (`cross_encoder_rerank.py`).
- **Stage 14 (Reasoning Generation):** Generates concise, human-readable explanations explaining why each candidate was selected (`reasoning.py`).
