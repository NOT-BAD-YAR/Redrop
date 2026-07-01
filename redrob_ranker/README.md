# Redrob Candidate Ranking System — Technical Documentation & Architecture

This repository contains the core codebase for the **Redrob Candidate Ranking System** (Track 01). Built to identify elite **Senior AI Engineer** talent from an unstructured pool of 100,000+ applicants, our system implements a highly optimized, deterministic 14-stage evaluation pipeline. It combines offline semantic similarity, multi-tiered AI capability taxonomy extraction, behavioral reachability signals, and rigorous risk gating—executing in under a minute on standard CPU hardware.

---

## Technology Stack

Our system is engineered for speed, reproducibility, and zero-external-dependency execution:

* **Core Runtime:** Python 3.11 (optimized for speed and clean typing).
* **Vector Embeddings & Semantic Search:** `sentence-transformers` & `numpy`. Uses precomputed vector representations (`all-MiniLM-L6-v2`, 384-dim) stored locally via Git LFS to perform high-speed cosine similarity without API calls.
* **Precision Reranking:** Offline Cross-Encoder (`ms-marco-MiniLM-L6-v2`) for deep sequence-pair classification on the top candidates.
* **Concurrency Engine:** Python `multiprocessing.Pool` utilizing shared worker memory initialization (`_init_worker`) to eliminate IPC overhead and achieve maximum multi-core throughput.
* **Declarative Configuration:** `PyYAML` & `python-dotenv` for clean, zero-code management of taxonomy regex patterns, scoring weights, and environment variables.
* **Data Modeling & Validation:** `Pydantic` for strict candidate schema enforcement and trace logging.

---

## System Architecture & Flow

```text
Input Candidates (JSON/JSONL) 
       │
       ▼
[Stage 0] Schema Normalization & Date Standardization
       │
       ▼
[Stage 1] Timeline & Credibility Validation (Anomalies & Gaps)
       │
       ▼
[Stages 2–5] Capability Taxonomy & Evidence Extraction (Retrieval, Ranking, Evaluation, Matching)
       │
       ▼
[Stages 6–7] Technical Fit Aggregation & Anti-Spam Point Capping
       │
       ▼
[Stage 8] Behavioral Engine (Market Intent & Reachability)
       │
       ▼
[Stages 9–10] Risk Engine & Gate Filtering (Honeypot & Consulting Penalties)
       │
       ▼
[Stages 11–13] Hybrid Score Fusion (Semantic 30% + Tech Fit 30% + BM25 20% + Behavioral 20%)
       │
       ▼
[Optional Stage 2] Cross-Encoder Precision Reranking (Top 1500 Pool)
       │
       ▼
[Stage 14] Deterministic Human-Readable Reasoning Generation ➔ Output Top 100 CSV
```

---

## The 14-Stage Working Process Explained

### 1. Pre-Processing & Data Integrity
* **Stage 0 (Schema Normalization):** Sanitizes heterogeneous candidate inputs, converts salary currencies to INR LPA, and standardizes date timestamps across work history entries.
* **Stage 1 (Credibility Validation):** Scans career timelines for overlapping full-time employment, suspicious gaps (>6 months), and academic timeline discrepancies to compute a base credibility score.

### 2. Deep Capability & Taxonomy Extraction
* **Stages 2–5 (Evidence Extraction):** Evaluates profile summaries, headlines, and career descriptions against a 3-tier AI engineering taxonomy defined in `config/dictionaries.yaml`:
  * *Retrieval & Indexing:* Vector databases (Qdrant, Milvus, Pinecone), BM25, hybrid search.
  * *Ranking & Recommendation:* Cross-encoders, ColBERT, learning-to-rank (LTR).
  * *Evaluation & Alignment:* RAGAS, TruLens, RLHF, DPO, prompt engineering.
  * *Matching & Architecture:* Graph neural networks, entity resolution, LLM orchestration.
  * Adjusts weights based on **Ownership** (*"built/architected"* vs *"assisted/maintained"*), **Recency** (current vs legacy roles), and **Production Scale**.

### 3. Scoring & Spam Prevention
* **Stages 6–7 (Technical Fit Aggregation):** Aggregates weighted capability hits into a unified 0–100 Technical Fit score. Enforces strict category point caps to prevent candidates from gaming the system via keyword spamming. Applies bonuses for verified product company backgrounds.

### 4. Behavioral & Risk Gating
* **Stage 8 (Behavioral Engine):** Assesses candidate availability, profile freshness, and salary expectations (`expected_salary_range_inr_lpa`). Candidates exceeding budget thresholds or displaying low intent receive reachability multipliers.
* **Stages 9–10 (Risk & Gate Engine):** Enforces hard filtering gates (e.g., salary honeypot triggers where min > max). Applies progressive penalties to candidates with purely theoretical backgrounds or consulting-only experience lacking product ownership.

### 5. Hybrid Score Fusion & Reranking
* **Stages 11–13 (Orchestration & Fusion):** Fuses four core orthogonal signals into a preliminary ranking score:
  $$\text{Final Score} = 0.30 \times \text{Semantic} + 0.30 \times \text{TechnicalFit} + 0.20 \times \text{BM25} + 0.20 \times \text{Behavioral}$$
* **Optional Stage 2 (Cross-Encoder Reranking):** If enabled (`USE_CROSS_ENCODER=true`), the top 1500 candidates undergo deep pairwise evaluation against the exact job description text using `ms-marco-MiniLM-L6-v2`, blending cross-encoder logits with Stage 1 scores for ultimate ranking precision.

### 6. Explainability & Output
* **Stage 14 (Reasoning Generation):** Generates concise, audit-ready markdown justifications for each selected candidate highlighting their specific production evidence, top competencies, and overall fit. Exports the top 100 ranked profiles to `submission.csv`.

---

## Repository Structure

```text
redrob_ranker/
├── .env.example             # Template for environment variables
├── Dockerfile               # Container build instructions
├── docker-compose.yml       # Multi-container orchestration & local volume mounts
├── requirements.txt         # Python project dependencies
├── validate_submission.py   # Competition submission CSV validator
├── artifacts/               # Precomputed offline embeddings & IDs (Git LFS)
├── config/                  # Declarative taxonomy rules & fusion weights (.yaml)
├── data/                    # Candidate datasets & job description files
├── models/                  # Bundled offline AI models (no internet required at runtime)
├── scripts/                 # Auxiliary helper scripts (embedding pre-computation)
└── src/                     # Core application source code
```

---

## Execution Modes & Setup Instructions

### Prerequisites: Git Large File Storage (Git LFS)
Because offline vector embeddings are stored in this repository, you must install Git LFS before cloning:

#### 1. Install Git LFS for Your Operating System
Open your terminal or command prompt and run the relevant command for your system:

**🌐 Windows**
The most direct method is using the built-in Windows Package Manager:
```bash
winget install -e --id GitHub.GitLFS
```
Alternatively, you can download the installer directly from the [Official Git LFS Website](https://git-lfs.com) and run the executable.

**🍎 macOS**
If you use Homebrew, run:
```bash
brew install git-lfs
```
If you use MacPorts, run:
```bash
port install git-lfs
```

**🐧 Linux (Ubuntu/Debian)**
```bash
sudo apt update && sudo apt install git-lfs
```

#### 2. Initialize and Clone the Repository
```bash
git lfs install
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop/redrob_ranker
git lfs pull
```

---

### Mode A: Docker Container Execution (Pull & Run via CLI)
You can execute the ranker directly using our pre-built image without installing Python locally. You **must mount local volume directories (`-v`)** to supply input data and collect the output CSV.

```bash
docker run --rm \
  -v /path/to/local/data:/app/data \
  -v /path/to/local/output:/app/output \
  notbad007/redrob-ranker:latest
```
*(Note: By default, the container reads `/app/data/candidates.jsonl` and writes `/app/output/submission.csv`.)*

**Passing Custom Flags in Docker (including cross-encoder on top 1500):**
```bash
docker run --rm \
  -v /path/to/local/data:/app/data \
  -v /path/to/local/output:/app/output \
  notbad007/redrob-ranker:latest --candidates /app/data/candidates.jsonl --out /app/output/submission.csv --use-cross-encoder true --rerank-pool-size 1500
```

---

### Mode B: Docker Desktop GUI Execution
If you prefer using Docker Desktop GUI instead of terminal commands:
1. Search for image **`notbad007/redrob-ranker:latest`** in Docker Desktop.
2. Click **Run**.
3. Expand **Optional settings** (or **Advanced settings**).
4. Under **Volumes / Host path mapping**, add:
   * **Host Path 1:** Your folder containing `candidates.jsonl` ➔ **Container Path:** `/app/data`
   * **Host Path 2:** Your output folder ➔ **Container Path:** `/app/output`
5. *(Optional)* Add environment variable overrides under **Environment variables** (e.g., `USE_CROSS_ENCODER` = `true`).
6. Click **Run**.

---

### Mode C: Docker Compose Execution (Local Repo)
If working inside the cloned repository directory, run:
```bash
docker compose run --rm ranker
```
To enable cross-encoder reranking via Compose:
```bash
docker compose run --rm ranker --use-cross-encoder true
```

---

### Mode D: Local Python Virtual Environment Setup
```bash
# 1. Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate

# 2. Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Run pipeline
python src/main.py
```

---

## Submission Validation

To verify that your generated CSV strictly adheres to Track 01 guidelines (exact headers, 100 rows, descending score order):
```bash
python validate_submission.py ./output/submission.csv
```

---

## Auxiliary Utilities

If you update the dataset or job description, recompute offline artifacts using the scripts in `scripts/`:
* Recompute Candidate Vectors: `python scripts/precompute_embeddings.py`
* Recompute Job Description Vector: `python scripts/precompute_jd_embedding.py`
* Refresh Cross-Encoder Bundle: `python scripts/download_cross_encoder.py`
