# Redrop Candidate Ranker — Track 01

Rank **100,000 candidates** against the Senior AI Engineer job description and output a **top-100 CSV with reasoning**.  
Runs **offline on CPU** (no GPU, no internet, no LLM API calls during ranking).

**Team:** Quad_Core | **Repo:** https://github.com/NOT-BAD-YAR/Redrop (branch: `kavin`)

---

## For Judges — Reproduce in 5 Steps

### Step 0 — Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | **3.11** (do not use 3.14 — `pydantic` will fail) |
| RAM | 8–16 GB |
| Git LFS | Required for embedding artifacts (~146 MB) |
| Input data | `candidates.jsonl` from the hackathon bundle (**not included in repo**) |

Install Git LFS once:

```bash
# macOS
brew install git-lfs && git lfs install

# Ubuntu/Debian
sudo apt install git-lfs && git lfs install

# Windows
winget install -e --id GitHub.GitLFS && git lfs install
```

### Step 1 — Clone and pull LFS files

```bash
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop
git checkout kavin
git lfs pull
cd redrob_ranker
```

### Step 2 — Place candidate data

Copy or symlink the hackathon `candidates.jsonl` into `data/`:

```bash
mkdir -p data output

# Example (adjust path to your bundle location):
cp "/path/to/hackathon/candidates.jsonl" data/candidates.jsonl
```

The job description is already in the repo at `data/Job Description.md`.

### Step 3 — Install Python dependencies

```bash
# Use Python 3.11 explicitly
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> **Important:** Always activate `.venv` before running commands.  
> If you see `ModuleNotFoundError: No module named 'yaml'`, you are not using the venv.

### Step 4 — Run the ranker (single command)

**Recommended submission command** (Stage 1 + cross-encoder rerank):

```bash
source .venv/bin/activate

python src/main.py \
  --candidates ./data/candidates.jsonl \
  --out ./output/submission.csv \
  --use-cross-encoder true \
  --rerank-pool-size 1500
```

**Stage 1 only** (faster, ~30 seconds):

```bash
python src/main.py \
  --candidates ./data/candidates.jsonl \
  --out ./output/submission.csv
```

### Step 5 — Validate output

```bash
python validate_submission.py ./output/submission.csv
```

Expected: `Submission is valid.`

---

## Expected Runtime (CPU, 100K candidates)

| Mode | Stage 1 | Stage 2 | Total |
|------|---------|---------|-------|
| Stage 1 only | ~30s | — | ~30s |
| + Cross-encoder (pool 1500) | ~30s | ~50s | **~80s** |
| + Cross-encoder (pool 7000) | ~30s | ~210s | **~4 min** |

All modes stay within the **5-minute** hackathon limit when pool ≤ 7000.

---

## Option A — Docker (no local Python needed)

Pre-built image: **`notbad007/redrob-ranker:latest`**

```bash
cd redrob_ranker
mkdir -p data output

# Place candidates.jsonl in ./data/ first, then:
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/output:/app/output" \
  notbad007/redrob-ranker:latest \
  --candidates /app/data/candidates.jsonl \
  --out /app/output/submission.csv \
  --use-cross-encoder true \
  --rerank-pool-size 1500
```

**Docker Compose** (from cloned repo):

```bash
docker compose run --rm ranker \
  --use-cross-encoder true \
  --rerank-pool-size 1500
```

---

## CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--candidates` | `./data/candidates.jsonl` | Path to `.jsonl`, `.json`, or folder of files |
| `--out` | `./output/submission.csv` | Output CSV path |
| `--top_n` | `100` | Number of candidates to output |
| `--use-cross-encoder` | `false` | Enable Stage 2 reranking (`true`/`false`) |
| `--rerank-pool-size` | `1500` | How many Stage-1 candidates to rerank |

Environment variables (optional, via `.env`):

```bash
cp .env.example .env
# Edit: CANDIDATES_PATH, OUTPUT_PATH, USE_CROSS_ENCODER, RERANK_POOL_SIZE
```

---

## Output Format

CSV columns (exact order): `candidate_id,rank,score,reasoning`

- Exactly **100 data rows** + 1 header
- Ranks 1–100, each used once
- Scores non-increasing by rank
- Reasoning: evidence-based, no LLM generation

---

## What's Bundled in the Repo (no download at runtime)

| Asset | Location | Notes |
|-------|----------|-------|
| Candidate embeddings | `artifacts/candidate_embeddings.npy` | Git LFS, 100K vectors |
| JD embedding | `artifacts/jd_embedding.npy` | Precomputed |
| Embedding model | `models/all-MiniLM-L6-v2/` | ~87 MB |
| Cross-encoder model | `models/cross-encoder-ms-marco-MiniLM-L6-v2/` | ~87 MB |
| Scoring config | `config/weights.yaml`, `config/dictionaries.yaml` | |

Pre-computation is **not required** after clone — embeddings are shipped ready to use.

---

## How It Works (brief)

```text
100,000 candidates
       ↓
Stage 1 — 14-stage pipeline (parallel, all candidates)
  • Validate timelines & honeypots
  • Extract evidence from career text (not just skills list)
  • Score technical fit + behavioral signals + semantic similarity
  • Fuse: 45% technical + 20% behavioral + 20% BM25 + 15% semantic
       ↓
Stage 2 — Cross-encoder rerank (optional, top N pool only)
  • Pairwise JD ↔ candidate scoring with ms-marco-MiniLM-L6-v2
  • Final = 75% Stage 1 + 25% cross-encoder (normalized)
       ↓
Top 100 CSV + reasoning
```

---

## Repository Layout

```text
redrob_ranker/
├── src/main.py              ← Entry point (run this)
├── src/core/                ← Pipeline modules
├── config/                  ← Weights & regex taxonomy
├── artifacts/               ← Precomputed embeddings (Git LFS)
├── models/                  ← Bundled offline models
├── data/                    ← Place candidates.jsonl here
├── output/                  ← submission.csv written here
├── validate_submission.py   ← Format checker
├── Dockerfile               ← Container build
└── requirements.txt
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named 'yaml'` | Run `source .venv/bin/activate` then `python -m pip install -r requirements.txt` |
| `command not found: pip` | Use `python -m pip` instead of `pip` |
| `candidates.jsonl not found` | Copy hackathon bundle file into `data/candidates.jsonl` |
| LFS files missing / tiny `.npy` | Run `git lfs pull` from repo root |
| `pydantic` install fails | You are on Python 3.14 — use **Python 3.11** |
| Cross-encoder slow | Normal on CPU; pool 1500 ≈ 50s, pool 7000 ≈ 3.5 min |

---

## Optional — Regenerate Embeddings

Only needed if you change the embedding model or text builder (~20 min, offline):

```bash
source .venv/bin/activate
python scripts/precompute_embeddings.py
python scripts/precompute_jd_embedding.py
```

---

## Submission Metadata

See `../submission_metadata.yaml` at repo root for team info, reproduce command, and compute environment details.
