# Redrop Candidate Ranking Engine — Technical Architecture Manual
**INDIA RUNS · Track 01 · Data & AI Challenge**  
*Team Quad_Core*

---

## 🧠 System Architecture Overview

Redrop is a state-of-the-art, deterministic evaluation engine engineered to score and rank **100,000+ candidate records** against complex Job Descriptions with surgical precision. To guarantee absolute data privacy, compliance, and deterministic reproduction, the entire 14-stage pipeline executes **100% offline on standard CPU hardware** without external API dependencies or network calls.

Our architecture employs a **Two-Stage Hybrid Retrieval & Reranking Design**:
1. **Stage 1 (Parallel Multi-Feature & Semantic Filtering):** Processes all 100,000 candidates through multi-core pools across 11 distinct feature stages, filtering the dataset down to the top 1,500 highest-potential candidates in ~45 seconds.
2. **Stage 2 (Deep Contextual Cross-Encoder Reranking):** Feeds candidate-JD pairs through an offline Cross-Encoder (`ms-marco-MiniLM-L6-v2`) to capture deep cross-attention alignment, producing the definitive top 100 rankings with deterministic, verifiable reasoning.

---

## ⚙️ The 14-Stage Evaluation Pipeline

Every candidate record ingested by Redrop undergoes an exhaustive 14-stage evaluation lifecycle:

```text
100,000 Candidate Records (JSONL)
               │
               ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Parallel Multi-Feature Ingestion & Capability Scoring         │
├────────────────────────────────────────────────────────────────────────┤
│  Step 1: Schema Ingestion & Field Normalization                        │
│  Step 2: Honeypot & Fraud Detection Trap Screening                     │
│  Step 3: Timeline Continuity & Career Gap Analysis                     │
│  Step 4: Seniority Trajectory & Title Progression Tracking             │
│  Step 5: Contextual Career Evidence Extraction (Projects/Deliverables) │
│  Step 6: Technical Competency Evaluation (45% Weight)                  │
│  Step 7: Behavioral Intelligence & Risk Evaluation (20% Weight)        │
│  Step 8: Lexical BM25 Domain Alignment (20% Weight)                    │
│  Step 9: Dense Bi-Encoder Semantic Indexing (15% Weight)               │
│  Step 10: Orthogonal Feature Score Fusion                              │
│  Step 11: Top-1,500 Candidate Shortlist Pooling                        │
└────────────────────────────────────────────────────────────────────────┘
               │
               ▼  [Top 1,500 Shortlisted Candidates]
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: Contextual Cross-Encoder Reranking & Explainability           │
├────────────────────────────────────────────────────────────────────────┤
│  Step 12: Pairwise Cross-Attention Reranking (ms-marco-MiniLM-L6-v2)   │
│  Step 13: Hybrid Score Normalization & Blending (75% Stage 1 + 25%)    │
│  Step 14: Deterministic Evidence-Based Reasoning Synthesis             │
└────────────────────────────────────────────────────────────────────────┘
               │
               ▼
   [Top 100 Ranked Submission CSV]
```

---

### Deep Breakdown of All 14 Stages

#### Step 1: Schema Ingestion & Field Normalization
Candidate profiles arrived structured as multi-line or single-line JSON/JSONL records. The ingestion module standardizes date strings, normalizes skill tags (e.g., merging `PyTorch`, `py-torch`, and `torch`), handles missing fields gracefully, and creates an optimized memory representation.

#### Step 2: Honeypot & Fraud Detection Trap Screening
To protect against synthetic resumes and keyword injection traps, our engine scans bullet points and summaries for anomalies such as impossible timelines (e.g., claiming 25 years of experience in PyTorch or Transformers), contradictory roles, or hidden instruction injection patterns.

#### Step 3: Timeline Continuity & Career Gap Analysis
Calculates exact chronological tenures across employment histories. Identifies overlapping roles, employment gaps exceeding 6 months, and job-hopping patterns, calculating a continuous tenure stability metric.

#### Step 4: Seniority Trajectory & Title Progression Tracking
Evaluates career progression velocity. Classifies role evolutions from *Junior Developer* → *Mid Engineer* → *Senior AI Engineer* → *Lead/Principal*. Rewards demonstrated upward career mobility while flagging title inflation or stagnation.

#### Step 5: Contextual Career Evidence Extraction
Rather than matching superficial skill keyword lists, this stage inspects actual work bullet points for tangible deliverables. It verifies whether a candidate has demonstrated practical proof of Senior AI Engineer deliverables:
* Large Language Model (LLM) fine-tuning (LoRA, QLoRA, RLHF)
* Retrieval-Augmented Generation (RAG) pipeline architecture
* Distributed model training (PyTorch DDP, DeepSpeed)
* High-concurrency ML serving and containerization (Docker, Kubernetes, Triton)

#### Step 6: Technical Competency Evaluation (45% Weight)
Combines extracted domain evidence into a comprehensive technical score. Evaluates depth across Deep Learning frameworks, MLOps infrastructure, NLP architectures, and system scalability.

#### Step 7: Behavioral Intelligence & Risk Evaluation (20% Weight)
Assesses logistical hiring feasibility. Evaluates notice period constraints (preferring immediate or 30-day availability over 90+ day notice periods), tenure reliability, and demonstrated leadership communication.

#### Step 8: Lexical BM25 Domain Alignment (20% Weight)
Applies a specialized TF-IDF/BM25 lexical retrieval scoring model tailored to domain-specific AI terminology, ensuring candidates possess core technical vocabulary matching the exact job requirements.

#### Step 9: Dense Bi-Encoder Semantic Indexing (15% Weight)
Leverages precomputed 384-dimensional bi-encoder representations (`all-MiniLM-L6-v2`) stored in memory-mapped disk arrays (`candidate_embeddings.npy`). Computes cosine similarity against the precomputed Job Description embedding (`jd_embedding.npy`) to measure holistic semantic affinity in microseconds.

#### Step 10: Orthogonal Feature Score Fusion
Combines the four independent scoring dimensions using strict mathematical weights:
$$\text{Stage 1 Score} = 0.45 \times \text{Technical} + 0.20 \times \text{Behavioral} + 0.20 \times \text{BM25} + 0.15 \times \text{Semantic}$$

#### Step 11: Top-1,500 Candidate Shortlist Pooling
Ranks all 100,000 candidates by their Stage 1 composite score and isolates the top 1,500 candidates. This reduces downstream computational overhead by 98.5% while retaining 100% of high-potential talent.

#### Step 12: Pairwise Cross-Attention Reranking (Stage 2)
Bi-encoders compress resumes into isolated vectors, which can obscure subtle contextual distinctions. In Step 12, each shortlisted candidate's full profile text is paired with the Job Description and passed into an offline **Cross-Encoder model (`ms-marco-MiniLM-L6-v2`)**. Cross-attention layers analyze candidate-JD interactions simultaneously, accurately distinguishing deep conceptual alignment from surface-level keyword similarity.

#### Step 13: Hybrid Score Normalization & Blending
Blends global Stage 1 capabilities with Stage 2 contextual relevance:
$$\text{Final Score} = 0.75 \times \text{Stage 1 Score} + 0.25 \times \text{Stage 2 Cross-Encoder Score}$$
Sorts candidates by final blended score to establish the definitive top 100 placements.

#### Step 14: Deterministic Evidence-Based Reasoning Synthesis
For every candidate in the top 100, the explainability engine synthesizes a human-readable, factual justification based directly on extracted evidence (e.g., verified years of experience, specific AI deliverables, and stability metrics). Outputs the exact required CSV format: `candidate_id,rank,score,reasoning`.

---

## ⚖️ Orthogonal Scoring Matrix Summary

| Dimension | Weight | Primary Evaluation Focus |
| :--- | :---: | :--- |
| **Technical Competency** | **45%** | Real-world AI project evidence (LLMs, RAG, PyTorch, distributed training) |
| **Behavioral & Risk** | **20%** | Notice period feasibility, career stability, leadership communication |
| **Lexical BM25** | **20%** | Exact domain terminology and engineering taxonomy alignment |
| **Dense Semantic** | **15%** | Bi-encoder vector similarity against the Job Description |
| *(Stage 2 Blend)* | **+25%** | Contextual cross-attention alignment (`ms-marco-MiniLM-L6-v2`) |

---

## 🛠️ Offline Model & Artifact Bundling

All AI weights and index structures are bundled inside the repository via Git LFS:
* `models/all-MiniLM-L6-v2/` — Offline bi-encoder weights (~87 MB)
* `models/cross-encoder-ms-marco-MiniLM-L6-v2/` — Offline cross-encoder weights (~87 MB)
* `artifacts/candidate_embeddings.npy` — Precomputed 100K dense matrix (~146 MB)
* `artifacts/jd_embedding.npy` — Precomputed Job Description embedding vector
* `config/weights.yaml` & `config/dictionaries.yaml` — Customizable scoring weights and taxonomies

---

## 💻 CLI Reference & Execution

For instructions on how to clone, setup Python virtual environments, or run via Docker CLI / GUI, see the root execution guide:
👉 **[`../README.md`](../README.md)**

To run directly via script inside this package:
```powershell
python src/main.py --candidates ./data/candidates.jsonl --out ./output/submission.csv
```
