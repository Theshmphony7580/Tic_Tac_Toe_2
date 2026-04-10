# TalentIntel Enterprise — Product Requirements Document (PRD)

## Multi-Agent AI System for Intelligent Resume Parsing, Skill-Set Matching, and API-Ready Talent Intelligence

---

## 1. Problem Statement

Recruitment and talent acquisition teams process thousands of resumes daily across diverse formats (PDF, DOCX, LinkedIn exports, plain text). Each resume contains inconsistent layouts, terminology, and skill representations. A candidate might list "React.js" while a job description requires "ReactJS" or "React"; one resume uses "ML Engineering" while the skill database categorizes it as "Machine Learning Engineering."

Current ATS (Applicant Tracking Systems) rely on rigid keyword matching that:
- **Misses qualified candidates** due to synonym mismatches
- **Surfaces irrelevant candidates** due to superficial keyword overlap
- **Cannot infer implicit skills** (e.g., someone listing "TensorFlow" clearly knows "Deep Learning")
- **Cannot handle layout diversity** (two-column PDFs, creative designs, tabular formats)

### Our Solution

A **Multi-Agent AI microservices system** that:
1. Parses resumes from multiple formats with layout-awareness
2. Extracts structured entities using LLM-powered extraction
3. Normalizes skills against a 5,000+ skill taxonomy using fuzzy matching and hierarchy inference
4. Performs semantic matching against job descriptions using vector similarity (pgvector)
5. Exposes the entire pipeline through production-grade REST APIs

---

## 2. System Architecture Overview

### 2.1 Architecture Style: Microservices

Each agent is an **independently deployable FastAPI service**. Services communicate via **Redis message queues** for async processing and **direct HTTP calls** for synchronous operations. The LangGraph orchestrator manages the state machine that coordinates the agent pipeline.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                     │
│   React.js UI  │  3rd-Party ATS  │  Python/JS SDK  │  Postman/cURL     │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ REST / SSE
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   GATEWAY SERVICE (FastAPI)                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐             │
│  │ Auth     │  │ Rate     │  │ Request  │  │ Swagger/   │             │
│  │ (API Key)│  │ Limiting │  │ Validate │  │ OpenAPI    │             │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘             │
│  Endpoints: /parse, /parse/batch, /match, /candidates, /skills         │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ Redis Queue / HTTP
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                ORCHESTRATOR SERVICE (LangGraph)                         │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │  LangGraph State Machine                                    │       │
│  │  ┌──────────┐    ┌──────────────┐    ┌───────────────┐     │       │
│  │  │ Node A:  │───>│  Node B:     │───>│  Node C:      │     │       │
│  │  │ Parse    │    │  Normalize   │    │  DB Commit    │     │       │
│  │  └──────────┘    └──────────────┘    └───────────────┘     │       │
│  └─────────────────────────────────────────────────────────────┘       │
│  Workers: Celery + Redis for concurrent resume processing              │
└──────┬──────────────────┬────────────────────┬──────────────────────────┘
       │                  │                    │
       ▼                  ▼                    ▼
┌─────────────┐  ┌────────────────┐  ┌─────────────────┐
│ PARSER      │  │ NORMALIZATION  │  │ MATCHING         │
│ SERVICE     │  │ SERVICE        │  │ SERVICE          │
│             │  │                │  │                  │
│ PyMuPDF     │  │ RapidFuzz      │  │ sentence-        │
│ python-docx │  │ Groq LLM      │  │ transformers     │
│ Groq API    │  │ Hierarchy      │  │ pgvector SQL     │
│ (Llama 3.1) │  │ Inference      │  │ Gap Analysis     │
└──────┬──────┘  └───────┬────────┘  └────────┬─────────┘
       │                 │                     │
       ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ PostgreSQL   │  │ Redis        │  │ Supabase     │                 │
│  │ + pgvector   │  │ (Queue +     │  │ Storage      │                 │
│  │ (Candidates, │  │  Cache)      │  │ (Raw Files)  │                 │
│  │  Skills,     │  │              │  │              │                 │
│  │  Jobs)       │  │              │  │              │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Microservices File Structure

```text
📂 TalentIntel-Enterprise/
│
├── 📂 gateway-service/                 # API Gateway (Auth, Swagger, Routes)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app entry point
│   │   ├── config.py                   # Environment variables & settings
│   │   ├── dependencies.py             # Auth, rate limiting DI
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── parse.py                # POST /api/v1/parse, /parse/batch
│   │   │   ├── match.py                # POST /api/v1/match
│   │   │   ├── candidates.py           # GET /api/v1/candidates/{id}/skills
│   │   │   ├── skills.py               # GET /api/v1/skills/taxonomy
│   │   │   └── webhooks.py             # Webhook registration & dispatch
│   │   ├── middleware/

│   │   │   ├── auth.py                 # API Key validation middleware
│   │   │   ├── rate_limiter.py         # Token bucket rate limiting
│   │   │   └── error_handler.py        # Global exception handler
│   │   └── schemas/
│   │       ├── requests.py             # Pydantic request models
│   │       └── responses.py            # Pydantic response models
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│       └── test_routes.py
│
├── 📂 orchestrator-service/            # LangGraph State Machine + Celery Workers
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI health endpoint + worker bootstrap
│   │   ├── config.py
│   │   ├── graph.py                    # LangGraph graph definition (nodes, edges)
│   │   ├── state.py                    # TypedDict for shared agent state
│   │   ├── workers.py                  # Celery task definitions
│   │   └── callbacks.py               # Webhook callback dispatcher
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│       └── test_graph.py
│
├── 📂 parser-service/                  # Agent 1: Structural Parsing
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI service entry (POST /internal/parse)
│   │   ├── config.py
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py           # PyMuPDF-based PDF text extraction
│   │   │   ├── docx_parser.py          # python-docx-based DOCX extraction
│   │   │   └── txt_parser.py           # Plain text handler
│   │   ├── extraction.py              # Groq LLM call for entity extraction
│   │   └── schemas.py                 # Internal Pydantic models
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│       ├── test_pdf_parser.py
│       └── test_extraction.py
│
├── 📂 normalization-service/           # Agent 2: Skill Normalization + Inference
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI service (POST /internal/normalize)
│   │   ├── config.py
│   │   ├── normalizer.py              # RapidFuzz matching + hierarchy inference
│   │   ├── taxonomy.py                # Skill taxonomy loader from PostgreSQL
│   │   └── schemas.py                 # Pydantic models for skill profiles
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│       └── test_normalizer.py
│
├── 📂 matching-service/                # Agent 3: Semantic Matching + Gap Analysis
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI service (POST /internal/match)
│   │   ├── config.py
│   │   ├── embedder.py                # sentence-transformers embedding generation
│   │   ├── matcher.py                 # pgvector cosine similarity query
│   │   ├── gap_analysis.py            # Skill gap computation
│   │   └── schemas.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│       └── test_matcher.py
│
├── 📂 core-infrastructure/
│   ├── database/
│   │   ├── init.sql                    # PostgreSQL schema + pgvector extension
│   │   └── seed_taxonomy.sql           # 5,000+ skill taxonomy seed data
│   ├── docker-compose.yml              # Full stack orchestration
│   ├── redis.conf                      # Redis queue configuration
│   ├── .env.example                    # Environment variable template
│   └── nginx.conf                      # (Optional) Reverse proxy config
│
├── 📂 sdk/
│   ├── python/
│   │   ├── talentintel/
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # Python SDK client class
│   │   │   └── models.py             # SDK data models
│   │   ├── setup.py
│   │   └── examples/
│   │       └── quickstart.py
│   └── javascript/
│       ├── src/
│       │   └── index.js               # JS SDK client
│       ├── package.json
│       └── examples/
│           └── quickstart.js
│
├── 📂 data/                            # Synthetic datasets for evaluation
│   ├── resumes/                        # 500+ sample resumes (PDF, DOCX, TXT)
│   ├── job_descriptions/              # 100+ sample JDs
│   └── ground_truth/                  # Expert-labeled matching scores
│
├── README.md
└── Makefile                            # Dev convenience commands
```

---

## 3. Technology Stack (With Justifications)

| Layer | Technology | Why This Choice |
|-------|-----------|-----------------|
| **API Gateway** | FastAPI (Python 3.12) | Native async, auto-generated OpenAPI/Swagger docs, Pydantic validation, production-proven |
| **Multi-Agent Orchestration** | LangGraph | Deterministic, graph-based state machine; supports conditional branching, parallel fan-out, and retry at the node level; superior to CrewAI for structured pipelines |
| **LLM Provider** | Groq (Llama 3.1 8B) | ~500 tokens/second inference speed; free tier available; structured JSON output support; cost: ~$0.05/1M input tokens |
| **PDF Parsing** | pymupdf4llm (built on PyMuPDF) | Converts PDF pages directly to **LLM-ready Markdown** (headings, tables, lists preserved); handles multi-column layouts and creative designs automatically; output is ideal for feeding into Groq Llama 3.1 without manual text cleanup |
| **DOCX Parsing** | python-docx | Native .docx reading; preserves paragraph and table structure |
| **Skill Fuzzy Matching** | RapidFuzz | C++ backend, 10x faster than FuzzyWuzzy; handles abbreviations ("JS" → "JavaScript") with configurable thresholds |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) | 384-dim vectors; runs locally (no API cost); good balance of speed (14k sentences/sec on GPU) and quality |
| **Vector Database** | PostgreSQL + pgvector | No separate vector DB needed; native SQL integration means JOINs between candidate metadata and embeddings in one query; cosine similarity via `<=>` operator |
| **Relational Database** | PostgreSQL 16 | ACID compliance for candidate records; JSONB for flexible schema storage; mature ecosystem |
| **Message Queue** | Redis 7 + Celery | Redis Streams for job queuing; Celery workers for parallel resume processing; built-in retry and dead-letter support |
| **File Storage** | Supabase Storage | S3-compatible API; built-in CDN; row-level security; free tier: 1GB storage |
| **Containerization** | Docker + Docker Compose | Reproducible builds; single `docker compose up` for full stack; service isolation |

---

## 4. Detailed Agent Specifications

### 4.1 Agent 1 — Parser Service (Structural Extraction)

**Purpose:** Convert raw resume files (PDF, DOCX, TXT) into a structured JSON object.

**Internal Endpoint:** `POST http://parser-service:8001/internal/parse`

**Input:**
```json
{
  "file_url": "https://supabase.co/storage/v1/resumes/abc123.pdf",
  "file_type": "pdf"
}
```

**Processing Logic:**

```
1. DOWNLOAD file from Supabase Storage URL
2. DETECT file type and route to appropriate parser:
   ├── PDF  → PyMuPDF (fitz)
   │         - Extract text blocks with coordinates (x0, y0, x1, y1)
   │         - Sort blocks by: page → column (x-position clusters) → y-position
   │         - This prevents two-column resumes from interleaving text
   │         - Merge blocks into coherent sections
   ├── DOCX → python-docx
   │         - Extract paragraphs preserving heading styles
   │         - Extract tables (for tabular skill/experience sections)
   └── TXT  → Direct read with encoding detection (chardet)
3. SEND extracted text to Groq API (Llama 3.1 8B) with this system prompt:

   SYSTEM PROMPT:
   "You are a resume parsing expert. Extract the following fields from the
    resume text into a strict JSON schema. If a field is not found, use null.
    Do NOT hallucinate information. Return ONLY valid JSON."

4. VALIDATE LLM output against Pydantic schema
5. RETURN structured JSON
```

**Output Schema (Pydantic):**
```python
class PersonalInfo(BaseModel):
    name: str
    email: str | None
    phone: str | None
    location: str | None
    linkedin_url: str | None
    portfolio_url: str | None

class WorkExperience(BaseModel):
    company: str
    role: str
    start_date: str | None        # "Jan 2020" or "2020"
    end_date: str | None           # "Present" or "Dec 2023"
    duration_months: int | None    # Calculated by LLM
    responsibilities: list[str]    # Bullet points

class Education(BaseModel):
    institution: str
    degree: str                    # "B.Tech", "M.S.", "PhD"
    field_of_study: str | None
    graduation_year: int | None
    gpa: float | None

class Certification(BaseModel):
    name: str
    issuer: str | None
    year: int | None

class Project(BaseModel):
    name: str
    description: str | None
    technologies: list[str]

class ParsedResume(BaseModel):
    personal_info: PersonalInfo
    work_experience: list[WorkExperience]
    education: list[Education]
    raw_skills: list[str]          # Unprocessed skill strings from resume
    certifications: list[Certification]
    projects: list[Project]
    publications: list[str]
    summary: str | None            # Professional summary if present
```

**Error Handling:**
- If Groq API times out → Retry 3x with exponential backoff (1s, 2s, 4s)
- If file is corrupted → Return `{"status": "failed", "error": "FILE_CORRUPT"}`
- If LLM returns invalid JSON → Re-prompt with stricter instruction (1 retry)

---

### 4.2 Agent 2 — Normalization Service (Skill Cleaning + Inference)

**Purpose:** Map raw, messy skill strings to canonical entries in the 5,000-skill taxonomy and infer implicit parent skills.

**Internal Endpoint:** `POST http://normalization-service:8002/internal/normalize`

**Input:**
```json
{
  "raw_skills": ["React.js", "K8s", "ML", "python3", "TensorFlow", "agile methodology"],
  "work_experience": [{"role": "ML Engineer", "duration_months": 36, "responsibilities": ["..."]}]
}
```

**Processing Logic:**

```
1. LOAD skill taxonomy from PostgreSQL into memory (cached in Redis, TTL=1hr)
   Taxonomy structure:
   ┌─────────────────────────────────────────────────────┐
   │ Technical Skills                                     │
   │ ├── Programming Languages                           │
   │ │   ├── Python (aliases: python3, py)               │
   │ │   ├── JavaScript (aliases: JS, ECMAScript)        │
   │ │   └── TypeScript (aliases: TS)                    │
   │ ├── Frameworks                                      │
   │ │   ├── React (aliases: React.js, ReactJS)          │
   │ │   ├── Django (aliases: django-rest-framework)     │
   │ │   └── FastAPI                                     │
   │ ├── Cloud & DevOps                                  │
   │ │   ├── Kubernetes (aliases: K8s, k8s)              │
   │ │   ├── Docker                                      │
   │ │   └── AWS (aliases: Amazon Web Services)          │
   │ ├── AI & Machine Learning                           │
   │ │   ├── Machine Learning (aliases: ML)              │
   │ │   ├── Deep Learning (aliases: DL)                 │
   │ │   ├── TensorFlow                                  │
   │ │   ├── PyTorch                                     │
   │ │   └── Natural Language Processing (aliases: NLP)  │
   │ └── ...                                             │
   ├── Soft Skills                                       │
   │   ├── Agile Methodology (aliases: agile, scrum)     │
   │   ├── Leadership                                    │
   │   └── ...                                           │
   └─────────────────────────────────────────────────────┘

2. For EACH raw_skill:
   a. EXACT MATCH: Check if skill exists literally in the taxonomy (case-insensitive)
   b. ALIAS MATCH: Check if skill matches any alias in the taxonomy
   c. FUZZY MATCH: If no exact/alias match, use RapidFuzz:
      - Algorithm: token_sort_ratio (handles word order differences)
      - Threshold: score >= 85 → auto-map
      - Score 70-84 → map but flag for human review
      - Score < 70 → flag as "EMERGING_SKILL" for human review
   d. RECORD: { raw: "K8s", canonical: "Kubernetes", confidence: 0.98, method: "alias" }

3. HIERARCHY INFERENCE (Rule-Based):
   Rules are stored as a JSON config:
   {
     "TensorFlow": ["Deep Learning", "Machine Learning", "AI"],
     "PyTorch": ["Deep Learning", "Machine Learning", "AI"],
     "React": ["Frontend Development", "Web Development"],
     "Kubernetes": ["Container Orchestration", "DevOps", "Cloud Computing"],
     "Django": ["Backend Development", "Web Development"],
     ...
   }
   For each matched canonical skill → add its parent skills to the profile.

4. PROFICIENCY ESTIMATION:
   - If work experience mentions the skill in responsibilities + duration >= 36 months → "Expert"
   - If duration 12-35 months → "Intermediate"
   - If only listed in skills section (no experience context) → "Beginner"
   - If certification exists for the skill → boost one level

5. RETURN normalized skill profile
```

**Output Schema:**
```python
class NormalizedSkill(BaseModel):
    canonical_name: str           # "Kubernetes"
    raw_input: str                # "K8s"
    category: str                 # "Cloud & DevOps"
    parent_category: str          # "Technical Skills"
    proficiency: str              # "Expert" | "Intermediate" | "Beginner"
    confidence: float             # 0.0 - 1.0 (matching confidence)
    match_method: str             # "exact" | "alias" | "fuzzy" | "inferred"
    is_emerging: bool             # True if not in taxonomy

class NormalizedProfile(BaseModel):
    canonical_skills: list[NormalizedSkill]
    inferred_skills: list[NormalizedSkill]   # Parent skills added by inference
    emerging_skills: list[str]                # Skills flagged for human review
    skill_summary: dict[str, int]             # { "Technical Skills": 12, "Soft Skills": 3 }
```

---

### 4.3 Agent 3 — Matching Service (Semantic Similarity + Gap Analysis)

**Purpose:** Given a Job Description, find the best-matching candidates using vector similarity and produce a gap analysis.

**Internal Endpoint:** `POST http://matching-service:8003/internal/match`

**Input:**
```json
{
  "job_description": "We are looking for a Senior ML Engineer with 5+ years...",
  "required_skills": ["Python", "TensorFlow", "Kubernetes", "MLOps"],
  "nice_to_have_skills": ["Rust", "ONNX", "Triton"],
  "threshold": 0.65,
  "top_k": 10,
  "weights": {
    "skill_match": 0.5,
    "experience_depth": 0.3,
    "education_relevance": 0.2
  }
}
```

**Processing Logic:**

```
1. EMBED the Job Description:
   - Model: sentence-transformers/all-MiniLM-L6-v2 (loaded once, cached in memory)
   - Output: 384-dimensional float vector
   - jd_vector = model.encode(job_description)

2. QUERY PostgreSQL with pgvector:
   SQL:
   SELECT
     c.id,
     c.name,
     c.skills_summary,
     c.experience_years,
     1 - (c.embedding <=> :jd_vector) AS semantic_similarity
   FROM candidates c
   WHERE 1 - (c.embedding <=> :jd_vector) > :threshold
   ORDER BY semantic_similarity DESC
   LIMIT :top_k;

3. For EACH candidate returned:
   a. SKILL MATCH SCORE:
      matched_required = intersection(candidate.skills, required_skills)
      matched_nice = intersection(candidate.skills, nice_to_have_skills)
      skill_score = (len(matched_required) / len(required_skills)) * 0.8
                  + (len(matched_nice) / len(nice_to_have_skills)) * 0.2

   b. EXPERIENCE DEPTH SCORE:
      For each required skill, check candidate's proficiency level:
        Expert = 1.0, Intermediate = 0.6, Beginner = 0.3
      experience_score = average(proficiency scores for required skills)

   c. COMPOSITE SCORE:
      final_score = (weights.skill_match * skill_score)
                  + (weights.experience_depth * experience_score)
                  + (weights.education_relevance * education_score)
                    # education_score: 1.0 if degree matches field, 0.5 otherwise

   d. GAP ANALYSIS:
      missing_skills = required_skills - candidate.skills
      upskill_suggestions = for each missing skill, query taxonomy for:
        - Related online courses (stored in taxonomy metadata)
        - Estimated learning time
        - Prerequisite skills the candidate already has

4. RETURN ranked results
```

**Output Schema:**
```python
class SkillGap(BaseModel):
    skill_name: str
    importance: str               # "required" | "nice_to_have"
    suggested_resources: list[str] # Learning path suggestions

class CandidateMatch(BaseModel):
    candidate_id: str
    candidate_name: str
    semantic_similarity: float    # 0.0 - 1.0 from pgvector
    skill_match_score: float      # 0.0 - 1.0
    experience_score: float       # 0.0 - 1.0
    composite_score: float        # 0.0 - 1.0 (weighted)
    matched_skills: list[str]
    missing_skills: list[SkillGap]
    proficiency_breakdown: dict[str, str]  # { "Python": "Expert", "K8s": "Intermediate" }

class MatchResult(BaseModel):
    job_description_hash: str
    total_candidates_scanned: int
    threshold_used: float
    results: list[CandidateMatch]
    processing_time_ms: int
```

---

## 5. Orchestrator Service — LangGraph State Machine

### 5.1 State Definition

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ResumeProcessingState(TypedDict):
    # Input
    job_id: str
    file_url: str
    file_type: str                        # "pdf" | "docx" | "txt"

    # After Parser Agent
    parsed_resume: dict | None            # ParsedResume as dict
    parse_error: str | None

    # After Normalization Agent
    normalized_profile: dict | None       # NormalizedProfile as dict
    normalization_error: str | None

    # After DB Commit
    candidate_id: str | None
    embedding_stored: bool

    # Metadata
    status: str                           # "parsing" | "normalizing" | "storing" | "complete" | "failed"
    retries: dict                         # { "parser": 0, "normalizer": 0 }
    start_time: float
    end_time: float | None
    latency_ms: int | None
```

### 5.2 Graph Definition

```python
def build_resume_graph():
    graph = StateGraph(ResumeProcessingState)

    # Add nodes
    graph.add_node("parse",      call_parser_service)
    graph.add_node("normalize",  call_normalization_service)
    graph.add_node("store",      store_candidate_in_db)
    graph.add_node("notify",     send_webhook_callback)
    graph.add_node("handle_error", handle_partial_failure)

    # Add edges
    graph.add_edge("__start__", "parse")
    graph.add_conditional_edges("parse", check_parse_result, {
        "success": "normalize",
        "retry":   "parse",            # Max 3 retries
        "fail":    "handle_error"
    })
    graph.add_conditional_edges("normalize", check_normalize_result, {
        "success": "store",
        "retry":   "normalize",
        "fail":    "handle_error"
    })
    graph.add_edge("store", "notify")
    graph.add_edge("notify", END)
    graph.add_edge("handle_error", "notify")  # Notify even on failure (partial results)

    return graph.compile()
```

### 5.3 Celery Worker Integration

```python
# workers.py
from celery import Celery

celery_app = Celery("orchestrator", broker="redis://redis:6379/0")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_resume_task(self, job_id: str, file_url: str, file_type: str):
    """Each resume in a batch is processed as an independent Celery task."""
    graph = build_resume_graph()
    initial_state = {
        "job_id": job_id,
        "file_url": file_url,
        "file_type": file_type,
        "parsed_resume": None,
        "parse_error": None,
        "normalized_profile": None,
        "normalization_error": None,
        "candidate_id": None,
        "embedding_stored": False,
        "status": "parsing",
        "retries": {"parser": 0, "normalizer": 0},
        "start_time": time.time(),
        "end_time": None,
        "latency_ms": None,
    }
    result = graph.invoke(initial_state)
    return result
```

### 5.4 Graceful Degradation

If the **Parser** succeeds but the **Normalizer** fails:
- The system stores the raw parsed data with `status: "partially_processed"`
- The raw skills are stored un-normalized
- A webhook callback is sent with `{ "status": "partial", "completed_steps": ["parse"] }`
- The job can be retried later via `POST /api/v1/parse/retry/{job_id}`

---

## 6. Database Schema (PostgreSQL + pgvector)

### 6.1 Schema SQL

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- API Keys for authentication
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(64) NOT NULL UNIQUE,     -- SHA-256 hash of the API key
    owner_name VARCHAR(255) NOT NULL,
    permissions TEXT[] DEFAULT ARRAY['read', 'write'],
    rate_limit_per_minute INT DEFAULT 60,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Candidates (parsed resumes)
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    location VARCHAR(255),
    linkedin_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    summary TEXT,

    -- Structured data stored as JSONB for flexible querying
    work_experience JSONB DEFAULT '[]',
    education JSONB DEFAULT '[]',
    certifications JSONB DEFAULT '[]',
    projects JSONB DEFAULT '[]',
    publications JSONB DEFAULT '[]',

    -- Skills
    raw_skills TEXT[],                          -- Original from resume
    canonical_skills TEXT[],                    -- After normalization
    skill_proficiencies JSONB DEFAULT '{}',     -- {"Python": "Expert", "K8s": "Intermediate"}
    inferred_skills TEXT[],                     -- Skills added by hierarchy inference

    -- Embeddings for semantic matching
    embedding vector(384),                      -- sentence-transformers output

    -- Metadata
    source_file_url VARCHAR(1000),
    file_type VARCHAR(10),
    processing_status VARCHAR(20) DEFAULT 'pending',  -- pending|processing|complete|partial|failed
    processing_latency_ms INT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast vector similarity search
CREATE INDEX idx_candidates_embedding ON candidates USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Skill Taxonomy (5,000+ entries)
CREATE TABLE skill_taxonomy (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    aliases TEXT[] DEFAULT '{}',                 -- ["JS", "ECMAScript", "ES6"]
    category VARCHAR(100),                       -- "Programming Languages"
    parent_category VARCHAR(100),                -- "Technical Skills"
    hierarchy_path TEXT,                          -- "Technical Skills > Programming Languages > JavaScript"
    parent_skills TEXT[] DEFAULT '{}',            -- Skills this implies (e.g., React → ["Frontend Dev"])
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Batch Jobs (for async processing tracking)
CREATE TABLE batch_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id),
    total_files INT DEFAULT 0,
    processed_files INT DEFAULT 0,
    failed_files INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',        -- pending|processing|complete|partial_failure
    webhook_url VARCHAR(1000),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Individual file tracking within a batch
CREATE TABLE batch_job_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_job_id UUID REFERENCES batch_jobs(id),
    candidate_id UUID REFERENCES candidates(id),
    file_name VARCHAR(255),
    file_url VARCHAR(1000),
    status VARCHAR(20) DEFAULT 'pending',        -- pending|processing|complete|failed
    error_message TEXT,
    processing_latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Emerging Skills (flagged for human review)
CREATE TABLE emerging_skills (
    id SERIAL PRIMARY KEY,
    raw_skill VARCHAR(255) NOT NULL,
    occurrence_count INT DEFAULT 1,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed BOOLEAN DEFAULT FALSE,
    added_to_taxonomy BOOLEAN DEFAULT FALSE,
    canonical_mapping VARCHAR(255)               -- Set after human review
);
```

---

## 7. API Specification (Gateway Service)

### 7.1 Authentication

All endpoints require an `X-API-Key` header. Keys are validated against hashed values in the `api_keys` table.

```
X-API-Key: sk_live_abc123def456
```

Unauthenticated requests receive:
```json
{ "error": "UNAUTHORIZED", "message": "Invalid or missing API key", "status_code": 401 }
```

### 7.2 Rate Limiting

- Default: **60 requests/minute** per API key
- Implemented via Redis sliding window counter
- Rate-limited responses:
```json
{ "error": "RATE_LIMITED", "message": "Rate limit exceeded. Retry after 23 seconds.", "retry_after": 23, "status_code": 429 }
```

### 7.3 Endpoint Specifications

---

#### `POST /api/v1/parse` — Single Resume Parse (Synchronous)

**Description:** Upload a single resume file and receive the parsed, normalized result synchronously.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF, DOCX, or TXT, max 10MB)

**Response (200):**
```json
{
  "candidate_id": "uuid-here",
  "personal_info": { "name": "Jane Doe", "email": "jane@example.com", ... },
  "work_experience": [ ... ],
  "education": [ ... ],
  "skills": {
    "canonical": ["Python", "TensorFlow", "Deep Learning"],
    "proficiencies": { "Python": "Expert", "TensorFlow": "Intermediate" },
    "inferred": ["Machine Learning", "AI"],
    "emerging": ["LangGraph"]
  },
  "certifications": [ ... ],
  "projects": [ ... ],
  "processing_time_ms": 3240
}
```

**Errors:**
- `400` — Unsupported file type
- `413` — File too large (>10MB)
- `422` — File could not be parsed
- `503` — LLM service unavailable

---

#### `POST /api/v1/parse/batch` — Batch Resume Parse (Asynchronous)

**Description:** Upload a ZIP containing up to 50 resumes. Returns immediately with a job ID.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (ZIP, max 100MB), `webhook_url` (optional)

**Response (202 Accepted):**
```json
{
  "job_id": "batch-uuid-here",
  "total_files": 47,
  "status": "processing",
  "status_url": "/api/v1/parse/status/batch-uuid-here",
  "estimated_completion_seconds": 120
}
```

---

#### `GET /api/v1/parse/status/{job_id}` — Check Batch Status

**Response (200):**
```json
{
  "job_id": "batch-uuid-here",
  "status": "processing",
  "progress": { "total": 47, "completed": 32, "failed": 1 },
  "failed_files": [{ "file_name": "corrupt_resume.pdf", "error": "FILE_CORRUPT" }],
  "candidate_ids": ["uuid-1", "uuid-2", "..."],
  "elapsed_seconds": 78
}
```

---

#### `GET /api/v1/candidates/{id}/skills` — Get Candidate Skill Profile

**Response (200):**
```json
{
  "candidate_id": "uuid-here",
  "name": "Jane Doe",
  "canonical_skills": [
    { "name": "Python", "category": "Programming Languages", "proficiency": "Expert" },
    { "name": "TensorFlow", "category": "AI & ML", "proficiency": "Intermediate" }
  ],
  "inferred_skills": ["Deep Learning", "Machine Learning"],
  "emerging_skills": ["LangGraph"],
  "total_skill_count": 15,
  "category_breakdown": { "Technical Skills": 12, "Soft Skills": 3 }
}
```

---

#### `POST /api/v1/match` — Match Candidates to Job Description

**Request:**
```json
{
  "job_description": "We need a Senior ML Engineer with 5+ years of experience...",
  "required_skills": ["Python", "TensorFlow", "Kubernetes"],
  "nice_to_have_skills": ["Rust", "ONNX"],
  "threshold": 0.65,
  "top_k": 10,
  "weights": { "skill_match": 0.5, "experience_depth": 0.3, "education_relevance": 0.2 }
}
```

**Response (200):**
```json
{
  "matches": [
    {
      "candidate_id": "uuid-1",
      "candidate_name": "Jane Doe",
      "composite_score": 0.89,
      "semantic_similarity": 0.92,
      "skill_match_score": 0.85,
      "experience_score": 0.90,
      "matched_skills": ["Python", "TensorFlow"],
      "missing_skills": [
        { "skill": "Kubernetes", "importance": "required", "suggestion": "CKA Certification course" }
      ],
      "proficiency_breakdown": { "Python": "Expert", "TensorFlow": "Intermediate" }
    }
  ],
  "total_scanned": 1247,
  "processing_time_ms": 450
}
```

---

#### `GET /api/v1/skills/taxonomy` — Browse Skill Taxonomy

**Query Params:** `?search=python&category=Technical Skills&page=1&limit=50`

**Response (200):**
```json
{
  "skills": [
    {
      "canonical_name": "Python",
      "aliases": ["python3", "py", "cpython"],
      "category": "Programming Languages",
      "parent_category": "Technical Skills",
      "hierarchy_path": "Technical Skills > Programming Languages > Python"
    }
  ],
  "total": 5432,
  "page": 1,
  "limit": 50
}
```

---

#### Webhook Callback Payload (on batch completion)

```json
POST {webhook_url}
Content-Type: application/json

{
  "event": "batch.completed",
  "job_id": "batch-uuid-here",
  "status": "complete",
  "results": {
    "total": 47,
    "successful": 46,
    "failed": 1
  },
  "candidate_ids": ["uuid-1", "uuid-2", "..."],
  "timestamp": "2026-03-30T16:15:00Z"
}
```

---

## 8. Skill Taxonomy Seed (5,000+ Skills)

The taxonomy is seeded via `core-infrastructure/database/seed_taxonomy.sql`. Here is the hierarchical structure:

### Top-Level Categories (8)
1. **Technical Skills** (~3,000 skills)
2. **Soft Skills** (~400 skills)
3. **Business Skills** (~350 skills)
4. **Design Skills** (~250 skills)
5. **Data & Analytics** (~400 skills)
6. **Industry Knowledge** (~300 skills)
7. **Certifications** (~200 skills)
8. **Tools & Platforms** (~500 skills)

### Sub-Category Examples (Technical Skills)
| Sub-Category | Example Skills | Count |
|---|---|---|
| Programming Languages | Python, JavaScript, Go, Rust, C++, Java, TypeScript, Ruby, Kotlin, Swift | ~80 |
| Frontend Frameworks | React, Angular, Vue.js, Svelte, Next.js, Nuxt.js | ~40 |
| Backend Frameworks | Django, FastAPI, Express.js, Spring Boot, Flask, NestJS | ~50 |
| Databases | PostgreSQL, MongoDB, MySQL, Redis, Cassandra, DynamoDB | ~60 |
| Cloud Platforms | AWS, GCP, Azure, DigitalOcean, Heroku | ~30 (with 200+ sub-services) |
| AI & Machine Learning | TensorFlow, PyTorch, scikit-learn, Hugging Face, LangChain, RAG | ~150 |
| DevOps & Infrastructure | Docker, Kubernetes, Terraform, Ansible, CI/CD, GitHub Actions | ~100 |
| Cybersecurity | OWASP, Penetration Testing, SOC, SIEM, Zero Trust | ~80 |

### Hierarchy Inference Rules (Stored as JSON Config)
```json
{
  "inference_rules": {
    "TensorFlow":    { "implies": ["Deep Learning", "Machine Learning", "AI"] },
    "PyTorch":       { "implies": ["Deep Learning", "Machine Learning", "AI"] },
    "React":         { "implies": ["Frontend Development", "Web Development", "JavaScript"] },
    "Next.js":       { "implies": ["React", "Frontend Development", "Server-Side Rendering"] },
    "Kubernetes":    { "implies": ["Container Orchestration", "DevOps", "Cloud Computing"] },
    "Docker":        { "implies": ["Containerization", "DevOps"] },
    "PostgreSQL":    { "implies": ["SQL", "Relational Databases", "Database Management"] },
    "FastAPI":       { "implies": ["Python", "Backend Development", "REST API Development"] },
    "LangChain":     { "implies": ["LLM Development", "AI", "Prompt Engineering"] },
    "Spark":         { "implies": ["Big Data", "Data Engineering", "Distributed Computing"] }
  }
}
```

---

## 9. Docker Compose (Full Stack)

```yaml
# core-infrastructure/docker-compose.yml
version: "3.9"

services:
  # --- Data Layer ---
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: talentintel
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ./database/seed_taxonomy.sql:/docker-entrypoint-initdb.d/02-seed.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf

  # --- Application Services ---
  gateway:
    build: ../gateway-service
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://admin:${POSTGRES_PASSWORD}@postgres:5432/talentintel
      - REDIS_URL=redis://redis:6379/0
      - PARSER_SERVICE_URL=http://parser:8001
      - NORMALIZATION_SERVICE_URL=http://normalizer:8002
      - MATCHING_SERVICE_URL=http://matcher:8003
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  parser:
    build: ../parser-service
    ports:
      - "8001:8001"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}

  normalizer:
    build: ../normalization-service
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://admin:${POSTGRES_PASSWORD}@postgres:5432/talentintel
      - REDIS_URL=redis://redis:6379/0
      - GROQ_API_KEY=${GROQ_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy

  matcher:
    build: ../matching-service
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql://admin:${POSTGRES_PASSWORD}@postgres:5432/talentintel
    depends_on:
      postgres:
        condition: service_healthy

  orchestrator:
    build: ../orchestrator-service
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://admin:${POSTGRES_PASSWORD}@postgres:5432/talentintel
      - PARSER_SERVICE_URL=http://parser:8001
      - NORMALIZATION_SERVICE_URL=http://normalizer:8002
      - MATCHING_SERVICE_URL=http://matcher:8003
    depends_on:
      - redis
      - parser
      - normalizer
      - matcher

  # --- Celery Worker (runs in orchestrator context) ---
  celery-worker:
    build: ../orchestrator-service
    command: celery -A app.workers worker --loglevel=info --concurrency=4
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://admin:${POSTGRES_PASSWORD}@postgres:5432/talentintel
      - PARSER_SERVICE_URL=http://parser:8001
      - NORMALIZATION_SERVICE_URL=http://normalizer:8002
      - MATCHING_SERVICE_URL=http://matcher:8003
    depends_on:
      - redis
      - orchestrator

volumes:
  pgdata:
```

---

## 10. Evaluation Criteria & Targets

| Metric | Target | How Measured |
|--------|--------|-------------|
| **Resume parsing F1-score** | ≥ 0.90 (per-field) | Compare extracted fields against expert-labeled ground truth for 100 resumes |
| **Skill normalization precision** | ≥ 0.92 | % of raw skills correctly mapped to canonical taxonomy entries |
| **Matching NDCG@10** | ≥ 0.85 | Normalized Discounted Cumulative Gain vs. expert-ranked candidate lists |
| **End-to-end latency (single)** | < 5 seconds | Time from file upload to stored candidate profile (parse + normalize + store, including LLM call via Groq) |
| **Batch throughput** | 50 resumes in < 3 min | With 4 Celery workers processing concurrently (~5s each, parallelized) |
| **API uptime** | 99.9% | Health check monitoring across all services |
| **API documentation** | Complete Swagger | All endpoints documented with examples at `/docs` |

---

## 11. SDK Examples

### Python SDK
```python
from talentintel import TalentIntelClient

client = TalentIntelClient(api_key="sk_live_abc123", base_url="https://api.talentintel.dev")

# Parse a single resume
result = client.parse_resume("resume.pdf")
print(result.skills.canonical)  # ["Python", "TensorFlow", "Kubernetes"]

# Batch parse
job = client.parse_batch("resumes.zip", webhook_url="https://myapp.com/webhook")
print(job.job_id)  # "batch-uuid-here"

# Match candidates to a JD
matches = client.match(
    job_description="Senior ML Engineer with 5+ years...",
    required_skills=["Python", "TensorFlow"],
    threshold=0.7,
    top_k=5
)
for m in matches.results:
    print(f"{m.candidate_name}: {m.composite_score:.2f}")
```

### JavaScript SDK
```javascript
import { TalentIntelClient } from '@talentintel/sdk';

const client = new TalentIntelClient({ apiKey: 'sk_live_abc123' });

// Parse a single resume
const result = await client.parseResume(file);
console.log(result.skills.canonical); // ["Python", "TensorFlow"]

// Match candidates
const matches = await client.match({
  jobDescription: 'Senior ML Engineer...',
  requiredSkills: ['Python', 'TensorFlow'],
  threshold: 0.7,
  topK: 5,
});
matches.results.forEach(m => console.log(`${m.candidateName}: ${m.compositeScore}`));
```

---

## 12. Environment Variables (.env.example)

```env
# Database
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://admin:your_secure_password_here@postgres:5432/talentintel

# Redis
REDIS_URL=redis://redis:6379/0

# Groq (LLM for parsing & normalization)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Supabase (File Storage)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# API Security
API_SECRET_KEY=your_jwt_secret_for_signing

# Embedding Model (sentence-transformers)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

---

*This document serves as the complete blueprint for the TalentIntel Enterprise system. A developer with access to this PRD should be able to implement the full system without additional context.*
