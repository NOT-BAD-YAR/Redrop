# Redrop — Intelligent Candidate Discovery & Ranking

**INDIA RUNS · Track 01 · Data & AI Challenge**  
**Redrob AI × Hack2Skill**

| | |
|---|---|
| **Team** | Quad_Core |
| **Challenge** | Rank 100,000 candidates for the **Senior AI Engineer** JD → top-100 CSV with reasoning |
| **Branch** | `kavin` |
| **Sandbox** | [Docker Hub — `notbad007/redrob-ranker`](https://hub.docker.com/r/notbad007/redrob-ranker) |
| **Metadata** | [`submission_metadata.yaml`](submission_metadata.yaml) (portal fields + reproduce command) |

---

## What this repo does

Given `candidates.jsonl` (100K profiles) and the released job description, our system:

1. Scores every candidate through a **14-stage CPU pipeline** (evidence validation, technical fit, behavioral signals, honeypot gates, semantic similarity).
2. Optionally **reranks the top 1,500** Stage-1 candidates with an offline cross-encoder.
3. Writes **`submission.csv`** — exactly 100 rows: `candidate_id,rank,score,reasoning`.

**Design goal:** find engineers who actually built retrieval/ranking systems in production — not keyword stuffers, honeypots, or inactive profiles.

---

## Reproduce the submission (single command)

> Per `submission_spec.md` §10.3 — this is the command judges should run at **Stage 3**.

### Option A — Docker (recommended, no Python setup)

```bash
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop && git lfs pull
cd redrob_ranker

mkdir -p data output
cp /path/to/hackathon/candidates.jsonl data/candidates.jsonl

docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/output:/app/output" \
  notbad007/redrob-ranker:latest \
  --candidates /app/data/candidates.jsonl \
  --out /app/output/submission.csv \
  --use-cross-encoder true \
  --rerank-pool-size 1500
```

### Option B — Local Python 3.11

```bash
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop && git checkout kavin && git lfs pull
cd redrob_ranker

mkdir -p data output
cp /path/to/hackathon/candidates.jsonl data/candidates.jsonl

python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt

python src/main.py \
  --candidates ./data/candidates.jsonl \
  --out ./output/submission.csv \
  --use-cross-encoder true \
  --rerank-pool-size 1500
```

### Validate before uploading

```bash
cd redrob_ranker
python validate_submission.py ./output/submission.csv
```

Expected output: **`Submission is valid.`**

---

## Compute constraints (submission_spec.md §3)

| Constraint | Limit | This system |
|------------|-------|-------------|
| Runtime | ≤ 5 min | **~80 s** (Stage 1 ~30 s + cross-encoder on 1,500) |
| Memory | ≤ 16 GB | ~2–4 GB peak |
| Compute | CPU only | ✅ No GPU used |
| Network | Off during ranking | ✅ No API calls; bundled offline models |
| Disk | ≤ 5 GB intermediate | ✅ Precomputed embeddings in repo (Git LFS) |

**Pre-computation:** Candidate embeddings (`artifacts/candidate_embeddings.npy`, ~146 MB) and model weights are **committed to the repo**. Judges do **not** need to run embedding pre-computation — only the ranking command above.

---

## Methodology (summary)

| Stage | What happens |
|-------|----------------|
| **Stage 1** | Parallel 14-step pipeline on all ~70K valid candidates: credibility checks, regex evidence from **career text** (not skills list alone), technical fit, 23 Redrob behavioral signals, risk/honeypot penalties, semantic cosine similarity vs JD |
| **Score fusion** | 45% technical fit + 20% behavioral + 20% BM25 + 15% semantic |
| **Stage 2** (optional) | Cross-encoder (`ms-marco-MiniLM-L6-v2`) reranks top 1,500 → final = 75% Stage 1 + 25% cross-encoder |
| **Reasoning** | Template-based from extracted evidence — no LLM, no hallucination |

**Anti-gaming:** salary honeypots gated, title-trap penalties (BA/HR/Marketing + AI keywords), consulting-only and LangChain-only penalties, inactive/low-response down-weighting.

👉 Full architecture, CLI flags, and troubleshooting: **[`redrob_ranker/README.md`](redrob_ranker/README.md)**

---

## Repository layout

```text
Redrop/
├── README.md                    ← You are here (judge quick-start)
├── submission_metadata.yaml     ← Portal metadata mirror (required)
├── reference_docs/              ← Hackathon spec copies & schemas
└── redrob_ranker/               ← All ranking code
    ├── src/main.py              ← Entry point
    ├── src/core/                ← Pipeline modules
    ├── config/                  ← weights.yaml, dictionaries.yaml
    ├── artifacts/               ← Precomputed embeddings (Git LFS)
    ├── models/                  ← MiniLM + cross-encoder (offline)
    ├── data/                    ← Place candidates.jsonl here
    ├── output/                  ← submission.csv written here
    ├── validate_submission.py   ← Format validator
    ├── requirements.txt
    ├── Dockerfile
    └── docker-compose.yml
```

**Not in repo:** `candidates.jsonl` (465 MB) — provided separately in the hackathon bundle.  
**In repo:** `data/Job Description.md`

---

## Submission checklist (portal)

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | **Ranked CSV** (100 rows, UTF-8) | Upload as `team_<id>.csv` to portal |
| 2 | **GitHub repo** | https://github.com/NOT-BAD-YAR/Redrop (branch `kavin`) |
| 3 | **Sandbox link** | https://hub.docker.com/r/notbad007/redrob-ranker |
| 4 | **submission_metadata.yaml** | Repo root (mirrors portal form) |
| 5 | **README** | This file + `redrob_ranker/README.md` |

CSV format: `candidate_id,rank,score,reasoning` — ranks 1–100 unique, scores non-increasing.

---

## Prerequisites

1. **Git LFS** — required for `artifacts/candidate_embeddings.npy`
   ```bash
   brew install git-lfs && git lfs install   # macOS
   git lfs pull                            # after clone
   ```
2. **Python 3.11** — do not use 3.14 (`pydantic` build fails)
3. **Hackathon data** — copy `candidates.jsonl` into `redrob_ranker/data/`

---

## Team

| Name | Role |
|------|------|
| Kavin C | ML & Semantic Ranking Engineer |
| Gokula Kannan S | Pipeline & Scoring Engineer |
| Ganga Rukmani A | Behavioral Intelligence & Risk Engineer |
| Hariharan A | Explainability & DevOps Engineer |

**Primary contact:** Kavin C · 727724eucy042@skcet.ac.in · +91-8610866523

---

## AI tools declaration

AI assistants (ChatGPT, Antigravity) were used for autocomplete and debugging only. Core architecture, ranking logic, and pipeline design are human-engineered. **No candidate data was sent to external LLM APIs.** See `submission_metadata.yaml` for full declaration.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `No module named 'yaml'` | Activate venv: `source redrob_ranker/.venv/bin/activate` |
| `command not found: pip` | Use `python -m pip install -r requirements.txt` |
| Tiny/missing `.npy` files | Run `git lfs pull` from repo root |
| `candidates.jsonl not found` | Copy hackathon bundle file to `redrob_ranker/data/` |
| `pydantic` install fails | Use **Python 3.11**, not 3.14 |

---

## References

- Official spec: hackathon bundle `Submission Spec.md` (also in `reference_docs/`)
- Deep technical docs: [`redrob_ranker/README.md`](redrob_ranker/README.md)
- Event: [India Runs — Hack2Skill](https://hack2skill.com/event/india_runs)
