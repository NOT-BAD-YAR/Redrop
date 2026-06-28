# Redrob Candidate Ranking System — Track 01 Submission

An advanced, multi-stage AI candidate evaluation engine designed to rank 100,000+ applicants for the **Senior AI Engineer** role. The system processes profile data against a 14-stage filtering and scoring pipeline, identifying high-impact engineering talent while filtering out keyword honeypots and risk factors.

---

## Key Features & Working Functions

* **14-Stage Evaluation Pipeline:** Integrates schema validation, credibility checking, taxonomy-based capability extraction (Retrieval, Ranking, Evaluation, Matching), ownership weighting ("built" vs "assisted"), and recency scoring.
* **Hybrid Score Fusion:** Combines offline semantic vector embeddings (`all-MiniLM-L6-v2`), BM25 lexical search, technical fit scores, and behavioral signals (market intent, reachability).
* **Stage 2 Cross-Encoder Reranking:** Optional precision reranking of the top 500 candidates using an offline cross-encoder (`ms-marco-MiniLM-L6-v2`).
* **Environment Configuration (`.env`):** Clean, zero-code configuration via `.env` files for customized input/output paths and runtime flags.
* **Docker & Compose Support:** Fully containerized pipeline with automatic host volume mounting for seamless execution across different OS environments.
* **Automated Output Validation:** Built-in validation script ensuring strict adherence to competition submission schemas and sorting criteria.

---

## Quick Start (Simple & Clear)

All project source code and configuration files reside in the `redrob_ranker` directory.

### 1. Environment Setup

```bash
cd redrob_ranker

# Pull precomputed offline embeddings via Git LFS
git lfs pull

# Create and activate virtual environment (Python 3.11 recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Settings (.env)

Copy the example configuration file to set up default file paths and options:

```bash
# Windows (PowerShell)
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

You can open `.env` to tweak parameters like `TOP_N`, `CANDIDATES_PATH`, or enable `USE_CROSS_ENCODER=true`.

### 3. Run the Ranking Pipeline

Run the ranker directly. It will automatically load variables from `.env`:

```bash
python src/main.py
```

*To override `.env` settings via command line arguments:*
```bash
python src/main.py --candidates ./data/candidates.jsonl --out ./output/submission.csv --top_n 100 --use-cross-encoder true
```

### 4. Validate the Submission

Verify that your generated CSV strictly meets competition formatting, sorting, and header rules:

```bash
python validate_submission.py ./output/submission.csv
```

---

## Running via Docker (Alternative)

If you prefer a containerized setup without installing local Python dependencies:

```bash
cd redrob_ranker

# Build and execute the ranker using Docker Compose
docker compose up --build
```

The container automatically maps `./data` and `./output` to your local host directory, outputting the results to `redrob_ranker/output/submission.csv`.

---

## Detailed Documentation

For an in-depth breakdown of scoring weights, taxonomy dictionaries, risk penalty calculations, and helper scripts (like embedding pre-computation), refer to the comprehensive guide:
👉 **[redrob_ranker/README.md](redrob_ranker/README.md)**
