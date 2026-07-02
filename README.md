# Redrop — Track 01: Intelligent Candidate Discovery

Hack2Skill × Redrob AI | Rank 100K candidates → Top 100 CSV with reasoning.

**Team:** Quad_Core  
**GitHub:** https://github.com/NOT-BAD-YAR/Redrop (branch: `kavin`)

---

## Quick Start (Judges)

```bash
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop && git checkout kavin && git lfs pull
cd redrob_ranker

# Place hackathon candidates.jsonl into data/
mkdir -p data output
cp /path/to/candidates.jsonl data/candidates.jsonl

# Setup Python 3.11 venv
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Run + validate
python src/main.py \
  --candidates ./data/candidates.jsonl \
  --out ./output/submission.csv \
  --use-cross-encoder true \
  --rerank-pool-size 1500

python validate_submission.py ./output/submission.csv
```

**Docker alternative:** see [redrob_ranker/README.md](redrob_ranker/README.md#option-a--docker-no-local-python-needed)

---

## Full Documentation

👉 **[redrob_ranker/README.md](redrob_ranker/README.md)** — setup, CLI flags, architecture, troubleshooting

👉 **`submission_metadata.yaml`** — team info, sandbox link, reproduce command
