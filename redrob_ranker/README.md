# Redrop — Intelligent Candidate Discovery & Ranking
**INDIA RUNS · Track 01 · Data & AI Challenge**  
*Redrob AI × Hack2Skill*

| Attribute | Details |
| :--- | :--- |
| **Team** | `Quad_Core` |
| **Challenge** | Rank 100,000 candidates for the Senior AI Engineer JD → Top CSV with evidence reasoning |
| **Branch** | `hari` |
| **Sandbox** | [Docker Hub — `notbad007/redrob-ranker`](https://hub.docker.com/r/notbad007/redrob-ranker) |
| **Metadata** | [`submission_metadata.yaml`](../submission_metadata.yaml) *(portal fields + reproduce command)* |

---

## ✨ System Overview

Redrop is a state-of-the-art, two-stage AI candidate evaluation engine designed to rank large-scale talent pools (**100,000+ candidates**) against complex Job Descriptions with surgical accuracy—**entirely offline on CPU**.

* **Stage 1 (Deep Feature Extraction & Dense Indexing):** Evaluates timeline continuity, seniority traps, technical skill overlap, behavioral intelligence, and pre-computed dense semantic embeddings (`all-MiniLM-L6-v2`) to shortlist top contenders.
* **Stage 2 (Cross-Encoder Reranking):** Leverages a dedicated cross-encoder (`ms-marco-MiniLM-L6-v2`) to perform deep contextual interaction scoring between the Job Description and candidate histories.
* **Explainability Engine:** Dynamically generates concise, human-verifiable justifications for every ranked candidate.

---

## 🚀 Method 1: The Python Way (Local Execution)

### Step 1: Clone Repository & Pull LFS Artifacts
Precomputed embeddings and models are stored via Git LFS. Ensure Git LFS is installed (`git lfs install`), then clone:
```bash
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop
git checkout hari
git lfs pull
```

### Step 2: Prepare Virtual Environment & Dependencies
Requires **Python 3.11**.
```bash
# Navigate into ranker package
cd redrob_ranker

# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run the Ranking Pipeline
You can run the ranker in two distinct ways depending on your workflow:

#### Option A: Production / Automated Scripted Mode
Pass paths explicitly via CLI flags. Executed immediately without interactive prompts:
```powershell
python src/main.py --candidates ./data/candidates.jsonl --out ./output/submission.csv
```

#### Option B: Interactive User Mode
Run simply without flags. If no path is supplied, it prompts cleanly for input and output locations:
```powershell
python src/main.py
```
```text
Enter input path (JSONL file or folder) [data\candidates.jsonl]: 
Enter output CSV path [output\submission.csv]: 
```

### Step 4: Validate Output
Check format compliance against challenge rules:
```powershell
python validate_submission.py ./output/submission.csv
```

---

## 🐳 Method 2: The Docker Way (Terminal CLI)

No Python installation required. Run directly via our published public Docker container.

### Step 1: Pull the Latest Image
```bash
docker pull notbad007/redrob-ranker:latest
```

### Step 2: Run with Volume Mounts
Place your `candidates.jsonl` into a local `data/` folder, create an `output/` folder, and execute:

```powershell
# Windows PowerShell:
docker run --rm -v "${PWD}/data:/app/data" -v "${PWD}/output:/app/output" notbad007/redrob-ranker:latest --candidates /app/data/candidates.jsonl --out /app/output/submission.csv
```

```bash
# Linux / macOS:
docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/output:/app/output" notbad007/redrob-ranker:latest --candidates /app/data/candidates.jsonl --out /app/output/submission.csv
```

Your ranked results will appear in `./output/submission.csv`.

---

## 🖥️ Method 3: The Docker Way (Docker Desktop GUI)

For evaluators who prefer a visual interface without terminal commands:

1. Open **Docker Desktop**.
2. In the top search bar, search for **`notbad007/redrob-ranker`** (under the *Images / Hub* tab) and click **Pull**.
3. Once downloaded, go to **Images**, find `notbad007/redrob-ranker:latest`, and click **Run**.
4. Click on **Optional Settings** before launching:
   * Under **Host path** for Volume 1: Browse and select your local folder containing `candidates.jsonl`.
   * Under **Container path** for Volume 1: Type `/app/data`
   * Under **Host path** for Volume 2: Browse and select your local empty folder for output.
   * Under **Container path** for Volume 2: Type `/app/output`
5. Click **Run**.
6. The container logs will show the ranking progress, and `submission.csv` will be deposited directly into your selected output folder!

---

## 📊 Performance & Runtime Benchmarks

Tested on standard CPU hardware (8 cores, 16 GB RAM):

| Mode | Processing Stage | Execution Time |
| :--- | :--- | :--- |
| **Stage 1 Retrieval Only** | 100,000 candidates | ~30 – 45 seconds |
| **Full Two-Stage Pipeline** | Stage 1 + Top-1500 Cross-Encoder Reranking | **~90 – 120 seconds** |

---

## 📂 Repository Structure

```text
redrob_ranker/
├── Dockerfile              # Production container specification
├── requirements.txt        # Pinned Python dependencies
├── validate_submission.py  # Output format validation utility
├── config/                 # Weights, dictionaries, and scoring rules
├── models/                 # Bundled offline Transformers models
├── artifacts/              # Precomputed semantic candidate embeddings (Git LFS)
└── src/
    ├── main.py             # CLI Entrypoint (Interactive + Scripted modes)
    └── core/               # Feature extractors, cross-encoder, and ranking logic
```
