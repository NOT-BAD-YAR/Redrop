# Redrop Candidate Ranking Engine — Technical Architecture Manual
**Track 01: Intelligent Candidate Discovery & Ranking**  
*Team Quad_Core (Branch: `hari`)*

---

## 🧠 System Architecture Overview

Redrop implements a high-performance, **Two-Stage Hybrid Ranking Engine** specifically designed to evaluate massive talent datasets (**100,000+ candidate histories**) against complex technical Job Descriptions. To guarantee data privacy, compliance, and deterministic reproducibility, the entire pipeline executes **100% offline on standard CPU hardware** without any network dependency or external LLM API calls during inference.

```text
100,000 Candidate Records (JSONL)
               │
               ▼
┌────────────────────────────────────────────────────────┐
│ STAGE 1: Parallel Multi-Feature & Semantic Filtering   │
├────────────────────────────────────────────────────────┤
│  • Timeline Validation & Honeypot Detection            │
│  • Seniority & Career Progression Analysis             │
│  • Evidence Extraction (Projects, Roles, Achievements) │
│  • Dense Semantic Similarity (all-MiniLM-L6-v2)        │
│  • Hybrid Scoring Fusion (Tech 45%, Behav 20%, BM25 20%)│
└────────────────────────────────────────────────────────┘
               │
               ▼  [Top 1,500 Candidate Shortlist]
┌────────────────────────────────────────────────────────┐
│ STAGE 2: Contextual Cross-Encoder Reranking            │
├────────────────────────────────────────────────────────┤
│  • Pairwise Interaction Scoring (ms-marco-MiniLM-L6-v2)│
│  • High-Precision Contextual Job Fit Alignment         │
│  • Blended Score Normalization (75% Stage 1 + 25% Stage 2)│
└────────────────────────────────────────────────────────┘
               │
               ▼  [Top 100 Ranked Candidates]
┌────────────────────────────────────────────────────────┐
│ EXPLAINABILITY & REASONING ENGINE                      │
├────────────────────────────────────────────────────────┤
│  • Dynamic Justification Generation (Evidence-Based)   │
│  • CSV Output Formatting & Schema Validation           │
└────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Component Deep-Dive

### 1. Stage 1: Fast Hybrid Retrieval & Capability Scoring
Evaluating 100,000 candidates sequentially would bottleneck CPU performance. Stage 1 utilizes multi-process parallelism to score candidates across five critical orthogonal dimensions:

* **Technical Competency & Evidence (45% Weight):** Parses candidate experience descriptions rather than relying solely on skill keyword lists. Identifies real-world implementation evidence for Senior AI Engineer concepts (LLM fine-tuning, RAG pipelines, distributed PyTorch, containerization).
* **Behavioral & Risk Intelligence (20% Weight):** Evaluates employment stability, notice periods, availability constraints, and leadership signals.
* **Lexical BM25 Alignment (20% Weight):** Calculates exact domain terminology matches against the Senior AI Engineer taxonomy.
* **Dense Semantic Indexing (15% Weight):** Uses precomputed bi-encoder vector representations (`all-MiniLM-L6-v2`) via localized memory mapping to measure broad semantic affinity with the Job Description vector.
* **Honeypot & Timeline Integrity:** Automatically identifies inflated experience anomalies, overlapping incompatible employment histories, or synthetic resumes.

### 2. Stage 2: Deep Contextual Cross-Encoder Reranking
Bi-encoder vectors compress full resumes into fixed embeddings, which can blur subtle distinctions between top candidates. Stage 2 takes the top **1,500 candidates** from Stage 1 and feeds candidate-JD pairs into a bundled offline **Cross-Encoder model (`ms-marco-MiniLM-L6-v2`)**.

* Unlike bi-encoders, the cross-encoder processes the candidate history and Job Description simultaneously via cross-attention layers.
* This identifies subtle semantic nuances (e.g., distinguishing between *building LLM architectures from scratch* versus *using an API wrap*).
* The final score fuses Stage 1 global capabilities with Stage 2 contextual alignment.

### 3. Dynamic Explainability Engine
Rather than using generative LLMs that hallucinate or require network connectivity, Redrop includes a deterministic, evidence-grounded explainability module. For each selected candidate in the top 100, it synthesizes:
* Key technical domain overlaps verified in work histories.
* Demonstrated leadership and tenure stability.
* Specific justification for their assigned rank and score.

---

## 🛠️ Offline Model & Artifact Bundling

All required ML models and index structures are bundled directly within the repository via Git LFS:
* `models/all-MiniLM-L6-v2/` — Offline bi-encoder weights (~87 MB)
* `models/cross-encoder-ms-marco-MiniLM-L6-v2/` — Offline cross-encoder weights (~87 MB)
* `artifacts/candidate_embeddings.npy` — Precomputed 100K semantic matrix
* `config/weights.yaml` & `config/dictionaries.yaml` — Configurable scoring matrices

---

## ⚙️ CLI Reference & Configuration

When executing `src/main.py`, the following parameters are supported:

| CLI Argument | Default Value | Description |
| :--- | :--- | :--- |
| `--candidates` | *(Interactive prompt or `data/candidates.jsonl`)* | Path to candidate dataset (`.jsonl`, `.json`, or directory) |
| `--out` | *(Interactive prompt or `output/submission.csv`)* | Path where the final ranked CSV will be saved |
| `--top_n` | `100` | Number of ranked candidates to output |
| `--use-cross-encoder` | `true` (via CLI/config) | Whether to activate Stage 2 cross-encoder reranking |
| `--rerank-pool-size` | `1500` | Number of top Stage 1 candidates to send to Stage 2 |

---

## 🏃 Execution Instructions Summary

To run the pipeline locally from the project root:

```powershell
# 1. Activate Python 3.11 virtual environment
.\redrob_ranker\.venv\Scripts\activate

# 2. Run the ranker
python redrob_ranker/src/main.py --candidates ./redrob_ranker/data/candidates.jsonl --out ./redrob_ranker/output/submission.csv

# 3. Validate output format
python redrob_ranker/validate_submission.py ./redrob_ranker/output/submission.csv
```

*(For quick setup or Docker instructions, see the root [`../README.md`](../README.md)).*
