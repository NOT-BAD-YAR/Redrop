# Redrop — Intelligent Candidate Discovery & Ranking
**INDIA RUNS · Track 01 · Data & AI Challenge**  
*Redrob AI × Hack2Skill*

| Attribute | Details |
| :--- | :--- |
| **Team** | `Quad_Core` |
| **Challenge** | Rank 100,000 candidates for the Senior AI Engineer JD → Top CSV with evidence reasoning |
| **Branch** | `hari` |
| **Sandbox** | [Docker Hub — `notbad007/redrob-ranker`](https://hub.docker.com/r/notbad007/redrob-ranker) |
| **Metadata** | [`submission_metadata.yaml`](submission_metadata.yaml) *(portal fields + reproduce command)* |
| **Full Architecture Guide** | 👉 **[`redrob_ranker/README.md`](redrob_ranker/README.md)** *(System design, scoring weights, pipeline deep dive)* |

---

## ⚡ Quick Execution Guide (For Judges & Evaluators)

This engine evaluates 100,000+ candidates offline on CPU. Choose your preferred execution method below:

---

### Method 1: The Python Way (Local Execution)

#### Step 1: Clone Repository & Pull LFS Artifacts
```bash
git clone https://github.com/NOT-BAD-YAR/Redrop.git
cd Redrop
git checkout hari
git lfs pull
```

#### Step 2: Setup Python 3.11 Environment
```bash
cd redrob_ranker
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Run the Pipeline

* **Option A: Automated / Scripted Mode (No user prompts)**
  ```powershell
  python src/main.py --candidates ./data/candidates.jsonl --out ./output/submission.csv
  ```

* **Option B: Interactive Mode (Clean CLI prompts)**
  ```powershell
  python src/main.py
  ```
  ```text
  Enter input path (JSONL file or folder) [data\candidates.jsonl]: 
  Enter output CSV path [output\submission.csv]: 
  ```

#### Step 4: Validate Format
```powershell
python validate_submission.py ./output/submission.csv
```

---

### Method 2: The Docker Way (Terminal CLI)

No local Python setup required. Run directly via our public container:

```bash
docker pull notbad007/redrob-ranker:latest
```

Place your `candidates.jsonl` in a local `data/` directory, create an `output/` directory, and run:

```powershell
# Windows PowerShell:
docker run --rm -v "${PWD}/data:/app/data" -v "${PWD}/output:/app/output" notbad007/redrob-ranker:latest --candidates /app/data/candidates.jsonl --out /app/output/submission.csv
```

```bash
# Linux / macOS:
docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/output:/app/output" notbad007/redrob-ranker:latest --candidates /app/data/candidates.jsonl --out /app/output/submission.csv
```

---

### Method 3: The Docker Way (Docker Desktop GUI)

For visual evaluators who prefer UI execution over terminal commands:

1. Open **Docker Desktop**.
2. In the top search bar, search for **`notbad007/redrob-ranker`** and click **Pull**.
3. Go to the **Images** tab, find `notbad007/redrob-ranker:latest`, and click **Run**.
4. Expand **Optional Settings**:
   * **Volume 1 (Host path):** Select your local folder containing `candidates.jsonl` → **Container path:** `/app/data`
   * **Volume 2 (Host path):** Select an empty output folder → **Container path:** `/app/output`
5. Click **Run**. The ranked results will be deposited into your output folder as `submission.csv`!

---

## 📖 Deep Technical Architecture & Internals

For full details on how our two-stage pipeline works, feature extraction formulas, cross-encoder reranking, and explainability reasoning generation, see the Technical Manual:
👉 **[`redrob_ranker/README.md`](redrob_ranker/README.md)**
