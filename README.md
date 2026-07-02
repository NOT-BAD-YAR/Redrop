# Redrop — Intelligent Candidate Discovery & Ranking
**INDIA RUNS · Track 01 · Data & AI Challenge**  
*Redrob AI × Hack2Skill*

| Attribute | Details |
| :--- | :--- |
| **Team** | `Quad_Core` |
| **Challenge** | Rank 100,000 candidates for the Senior AI Engineer JD → Top CSV with evidence reasoning |
| **Sandbox** | [Docker Hub — `notbad007/redrob-ranker`](https://hub.docker.com/r/notbad007/redrob-ranker) |
| **Metadata** | [`submission_metadata.yaml`](submission_metadata.yaml) *(portal fields + reproduce command)* |
| **Technical Manual** | 👉 **[`redrob_ranker/README.md`](redrob_ranker/README.md)** *(Detailed 14-Stage Architecture & Scoring Deep Dive)* |

---

## ⚡ Step-by-Step Execution Guide

This repository contains an offline AI engine capable of ranking 100,000+ candidates locally on CPU within minutes. Choose your execution workflow below:

---

### Method 1: Local Execution (Python 3.11)

#### Step 1: Clone Repository & Pull Git LFS Artifacts
Precomputed offline embeddings and bundled models are tracked via Git LFS (~146 MB total). Ensure Git LFS is installed (`git lfs install`), then clone:
```bash
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop
git lfs pull
```

#### Step 2: Create Virtual Environment & Install Dependencies
Requires **Python 3.11**.
```bash
cd redrob_ranker

# Create virtual environment
python -m venv .venv

# Activate on Windows PowerShell:
.\.venv\Scripts\activate
# Activate on Linux / macOS:
# source .venv/bin/activate

# Upgrade pip and install pinned requirements
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Run the Ranking Engine
You can execute the ranker in two distinct modes:

* **Option A: Explicit / Scripted Mode (Production Automation)**
  Runs immediately without user interaction by passing arguments directly:
  ```powershell
  python src/main.py --candidates ./data/candidates.jsonl --out ./output/submission.csv
  ```

* **Option B: Interactive Mode (Clean Prompts)**
  Run simply without arguments. It will prompt you for the input and output file locations:
  ```powershell
  python src/main.py
  ```
  ```text
  Enter input path (JSONL file or folder) [data\candidates.jsonl]: 
  Enter output CSV path [output\submission.csv]: 
  ```

#### Step 4: Validate Output Format
Verify that your generated CSV strictly adheres to the hackathon submission format:
```powershell
python validate_submission.py ./output/submission.csv
```
Expected output: `Submission is valid.`

---

### Method 2: Docker CLI (No Local Python Required)

Run directly using our pre-built public container on Docker Hub.

#### Step 1: Pull the Container Image
```bash
docker pull notbad007/redrob-ranker:latest
```

#### Step 2: Execute Container with Volume Mounts

> [!NOTE]
> **Understanding `${PWD}` and Path Locations:**  
> In the commands below, `${PWD}` (PowerShell) or `$(pwd)` (Linux/macOS) automatically expands to your **current terminal working directory**.
> * **If you are inside `redrob_ranker/`** where your `data/` folder is located, running the command below works automatically!
> * **If you are in a different terminal directory**, please replace `${PWD}/data` and `${PWD}/output` with the **absolute path** to your local `data` and `output` directories (for example: `-v "C:\Users\YourName\Redrop\redrob_ranker\data:/app/data"`).

```powershell
# Windows PowerShell (Navigate to redrob_ranker directory first, or use absolute paths):
docker run --rm -v "${PWD}/data:/app/data" -v "${PWD}/output:/app/output" notbad007/redrob-ranker:latest --candidates /app/data/candidates.jsonl --out /app/output/submission.csv
```

```bash
# Linux / macOS (Navigate to redrob_ranker directory first, or use absolute paths):
docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/output:/app/output" notbad007/redrob-ranker:latest --candidates /app/data/candidates.jsonl --out /app/output/submission.csv
```

Your ranked results will appear in `./output/submission.csv`.

---

### Method 3: Docker Desktop GUI

If you prefer using a graphical interface instead of terminal commands:

1. Open **Docker Desktop**.
2. In the top search bar, search for **`notbad007/redrob-ranker`** and click **Pull**.
3. Go to the **Images** tab, locate `notbad007/redrob-ranker:latest`, and click **Run**.
4. Click on **Optional Settings** before starting:
   * Under **Host path** for Volume 1: Select your local folder containing `candidates.jsonl` → **Container path:** `/app/data`
   * Under **Host path** for Volume 2: Select an empty folder for your output → **Container path:** `/app/output`
5. Click **Run**. The container will process the candidates and deposit `submission.csv` directly into your selected output directory!

---

## 📖 System Architecture & How It Works

To understand our **14-Stage Evaluation Pipeline**, orthogonal scoring matrices (45% Technical, 20% Behavioral, 20% BM25, 15% Dense Semantic), cross-encoder reranking mechanics, and deterministic explainability engine, read the full Technical Manual:
👉 **[`redrob_ranker/README.md`](redrob_ranker/README.md)**
