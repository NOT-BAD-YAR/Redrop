# Redrob Candidate Ranking System

This project is a structured, highly optimized multi-stage candidate ranking system built to identify the best Senior AI Engineer profiles from a dataset of 100,000+ candidates. It processes candidates against a 14-stage filtering and scoring pipeline designed to weed out keyword honeypots and elevate candidates with genuine, scalable production experience.

## Architecture

The project is structured into multiple core modules handling specific stages of the scoring pipeline:

```text
redrob_ranker/
├── data/                    # Expected directory for candidates.jsonl input
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
│   │   └── validator.py        # Stage 1: Evidence Validation (Consistency & Credibility)
│   ├── models/
│   │   ├── candidate.py        # Type hints for candidate JSON objects
│   │   └── trace.py            # Pydantic models mapping the formal Trace Schema
│   └── main.py                 # CLI Execution Point
├── output/                     # Export directory for ranked JSON output
└── requirements.txt            # Project dependencies (pydantic, pyyaml)
```

## Setup & Execution

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run the Pipeline
The `main.py` script utilizes Python's `multiprocessing` to stream and process candidates in parallel without blowing up the memory footprint.

```powershell
python src/main.py --candidates ..\candidates.jsonl --out output\submission.csv
```

## Processing Stages

- **Stage 0 (Schema):** Ensures robust dates via timestamp conversion (`normalizer.py`).
- **Stage 1 (Evidence Validation):** Flags invalid timelines and generates base Credibility (`validator.py`).
- **Stages 2-5 (Evidence & Modifiers):** Scans profile text against 3 Tiers of Technical taxonomy, applying modifiers for Recency, Ownership ("built" vs "assisted"), and Production scale (`extractor.py`).
- **Stages 6-7 (Technical Fit):** Caps taxonomy points to prevent over-indexing on keywords. Adds Product Company bonuses (`scorer.py`).
- **Stage 8 (Behavior):** Evaluates Intent, Reachability, and Demand using a multiplicative modifier (`behavior_engine.py`).
- **Stages 9-10 (Risks & Gates):** Adds heavy point penalties for low response rates or consulting-only backgrounds. Applies hard removal Gates (`risk_engine.py`).
- **Stages 11-13 (Rank Orchestration):** Calculates Final Score (`Tech Fit * Behavior * Credibility - Risks`) and sorts Top 100 (`ranker.py`).
- **Stage 14 (Reasoning):** Outputs human-readable logic templates appended to the trace (`reasoning.py`).
