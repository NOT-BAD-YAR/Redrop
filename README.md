# Redrob Candidate Ranking System — Track 01 Submission

An advanced, multi-stage AI candidate evaluation engine designed to rank 100,000+ applicants for the **Senior AI Engineer** role. The system processes profile data against a 14-stage filtering and scoring pipeline, identifying high-impact engineering talent while filtering out keyword honeypots and risk factors.

👉 **For comprehensive technical architecture, detailed scoring formulas, and stage-by-stage breakdowns, please see the [Detailed Technical Documentation (redrob_ranker/README.md)](redrob_ranker/README.md).**

---

## Important Note on Cloning & Git LFS

This repository includes bundled offline embedding models and precomputed semantic vectors (~170 MB total). Because we use large files, **Git Large File Storage (Git LFS)** is required.

### 1. Install Git LFS for Your Operating System
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

### 2. Initialize and Clone the Repository
Once installed, initialize Git LFS and clone the project:
```bash
# 1. Initialize Git LFS on your system
git lfs install

# 2. Clone the repository
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop

# 3. Pull LFS files (if not automatically pulled during clone)
git lfs pull
```

---

## Quick Start: Running via Docker (Recommended)

You can run the entire evaluation system immediately using our pre-built Docker image: **`notbad007/redrob-ranker`**. You do not need to install Python or local dependencies. 

When running via Docker, you **must explicitly map volume paths** from your local machine to the container so it can read your candidate data and save the final CSV submission. The container expects data at `/app/data` and writes output to `/app/output`.

### Method 1: Terminal Way (`docker run`)

Open your terminal and run the container by mapping your local folders (`-v`):

```bash
docker run --rm \
  -v /path/to/your/local/data:/app/data \
  -v /path/to/your/local/output:/app/output \
  notbad007/redrob-ranker:latest
```
*(Replace `/path/to/your/local/data` with the folder containing `candidates.jsonl` on your computer, and `/path/to/your/local/output` with where you want `submission.csv` saved.)*

**Optional Custom Arguments & Environment Variables:**
You can pass custom flags or environment variables (`-e`):
```bash
docker run --rm \
  -e USE_CROSS_ENCODER=true \
  -e TOP_N=100 \
  -v /path/to/your/local/data:/app/data \
  -v /path/to/your/local/output:/app/output \
  notbad007/redrob-ranker:latest --candidates /app/data/candidates.jsonl --out /app/output/submission.csv
```

---

### Method 2: GUI Way (Docker Desktop)

If you prefer using Docker Desktop's graphical interface instead of the terminal:

1. Open **Docker Desktop** and navigate to the search bar or the **Images** tab.
2. Search for or pull the image: **`notbad007/redrob-ranker:latest`**.
3. Click the **Run** button next to the image.
4. Before starting, expand the **Optional settings** (or **Advanced settings**) section.
5. Under **Volumes / Host path mapping**, add two mappings:
   * **Host Path 1:** Select your local folder containing `candidates.jsonl` ➔ **Container Path:** `/app/data`
   * **Host Path 2:** Select your destination folder for results ➔ **Container Path:** `/app/output`
6. *(Optional)* Under **Environment variables**, add any desired overrides (e.g., Variable: `USE_CROSS_ENCODER`, Value: `true`).
7. Click **Run**. The container will process the profiles and place `submission.csv` directly into your local destination folder!

---

## Quick Start: Running via Local Python Setup

If you prefer running directly on your machine without Docker:

```bash
cd redrob_ranker

# 1. Create and activate virtual environment (Python 3.11 recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Setup environment configuration
cp .env.example .env

# 4. Execute the ranking pipeline
python src/main.py

# 5. Validate your generated submission file
python validate_submission.py ./output/submission.csv
```

---

## Detailed System Documentation

To explore the underlying architecture, technology stack, and full working process of the 14-stage scoring pipeline, please read our complete technical guide:
👉 **[Click here to view the Technical Architecture & Process Guide (redrob_ranker/README.md)](redrob_ranker/README.md)**
