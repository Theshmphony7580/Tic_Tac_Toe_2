# TalentIntel Enterprise 🧠

### Multi-Agent AI System for Intelligent Resume Parsing, Skill Normalization, and Semantic Talent Matching

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange)](https://github.com/langchain-ai/langgraph)
[![PostgreSQL + pgvector](https://img.shields.io/badge/PostgreSQL-pgvector-blue?logo=postgresql)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docker.com)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Table of Contents

1. [Overview](#1-overview)
2. [The Problem](#2-the-problem)
3. [Our Solution](#3-our-solution)
4. [System Architecture](#4-system-architecture)
5. [Technology Stack](#5-technology-stack)
6. [Repository Structure](#6-repository-structure)
7. [Microservices Deep Dive](#7-microservices-deep-dive)
   - [Gateway Service](#71-gateway-service-port-8000)
   - [Orchestrator Service](#72-orchestrator-service-langgraph--celery)
   - [Parser Service](#73-parser-service-port-8001)
   - [Normalization Service](#74-normalization-service-port-8002)
   - [Matching Service](#75-matching-service-port-8003)
   - [Auth Service](#76-auth-service-port-8001-standalone)
   - [Frontend](#77-frontend-nextjs-16)
8. [Database Schema](#8-database-schema)
9. [API Reference](#9-api-reference)
10. [Getting Started](#10-getting-started)
11. [Configuration](#11-configuration)
12. [Running Tests](#12-running-tests)
13. [Evaluation Metrics](#13-evaluation-metrics)
14. [SDK Usage](#14-sdk-usage)
15. [Contributing](#15-contributing)

---

## 1. Overview

**TalentIntel Enterprise** is a production-grade, multi-agent SaaS platform that solves the core intelligence gap in modern recruitment: the disconnect between how candidates describe their skills and how employers specify their requirements.

It is built as a **microservices system** where four specialized AI agents — Parser, Normalizer, Matcher, and Orchestrator — work together in a **LangGraph state machine** to transform raw resume files into rich, queryable talent intelligence, surfaced through a REST API and a React dashboard.

> Built for Tic-Tech-Toe '26 · Prama Innovations · Problem Statement 9 (FinOps + Agentic AI)

---

## 2. The Problem

Recruitment teams process thousands of resumes daily across diverse formats. Each resume contains inconsistent terminology:

| Resume says | Job Description says |
|---|---|
| `React.js` | `ReactJS` |
| `K8s` | `Kubernetes` |
| `ML` | `Machine Learning` |
| `python3` | `Python` |

Current ATS (Applicant Tracking Systems) rely on **rigid keyword matching** that:

- ❌ **Misses qualified candidates** due to synonym mismatches
- ❌ **Cannot infer implicit skills** (someone listing "TensorFlow" clearly knows "Deep Learning")
- ❌ **Cannot handle layout diversity** (two-column PDFs, creative designs, tabular formats)
- ❌ **Provides no gap analysis** to explain why a candidate was ranked lower

---

## 3. Our Solution

A **four-agent AI microservices pipeline** that:

1. **Parses** resumes from PDF, DOCX, and TXT with layout-awareness (bounding-box-aware multi-column handling)
2. **Extracts** structured entities using Groq's Llama 3.1 8B LLM
3. **Normalizes** skills against a 5,000+ skill taxonomy using RapidFuzz and hierarchy inference (e.g., `TensorFlow → Deep Learning → AI`)
4. **Matches** candidates semantically to job descriptions using `all-MiniLM-L6-v2` embeddings + pgvector cosine similarity
5. **Surfaces** gap analysis and upskilling paths for every candidate match
6. **Exposes** the entire pipeline through a production-grade REST API with Swagger docs

---

## 4. System Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                    │
│  Next.js UI  │  3rd-Party ATS  │  Python/JS SDK  │  Postman/cURL         │
└─────────────────────────────┬─────────────────────────────────────────────┘
                              │ REST / SSE
                              ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                  GATEWAY SERVICE  :8000  (FastAPI)                        │
│    Auth (API Key)  │  Rate Limiting  │  Validation  │  Swagger/OpenAPI    │
│  Endpoints: /parse  /parse/batch  /match  /candidates  /skills            │
└─────────────────────────────┬─────────────────────────────────────────────┘
                              │ Redis Queue / HTTP
                              ▼
┌───────────────────────────────────────────────────────────────────────────┐
│              ORCHESTRATOR SERVICE  (LangGraph + Celery)                   │
│  ┌───────────┐    ┌────────────────┐    ┌───────────────┐                │
│  │  Node A   │───▶│    Node B      │───▶│    Node C     │                │
│  │  Parse    │    │  Normalize     │    │   DB Commit   │                │
│  └───────────┘    └────────────────┘    └───────────────┘                │
│  Retry logic │ Graceful degradation │ Webhook callbacks                   │
└──────┬────────────────────┬──────────────────────┬────────────────────────┘
       │                    │                      │
       ▼                    ▼                      ▼
┌─────────────┐  ┌──────────────────┐  ┌────────────────────┐
│   PARSER    │  │  NORMALIZATION   │  │     MATCHING       │
│  :8001      │  │    :8002         │  │      :8003         │
│             │  │                  │  │                    │
│ PyMuPDF     │  │ RapidFuzz        │  │ sentence-          │
│ pymupdf4llm │  │ Groq LLM         │  │ transformers       │
│ python-docx │  │ Hierarchy Rules  │  │ pgvector SQL       │
│ Groq API    │  │ Redis Cache      │  │ Gap Analysis       │
└──────┬──────┘  └────────┬─────────┘  └─────────┬──────────┘
       │                  │                       │
       ▼                  ▼                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                      │
│  PostgreSQL 16 + pgvector  │  Redis 7  │  Supabase Storage               │
│  candidates, skill_taxonomy │  Queues  │  Raw resume files               │
│  batch_jobs, api_keys       │  Taxonomy │                                │
│  embedding vector(384)      │  Cache   │                                 │
└───────────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Orchestration | LangGraph state machine | Deterministic, conditional branching, per-node retry — superior to CrewAI for structured pipelines |
| LLM Inference | Groq (Llama 3.1 8B) | ~500 tokens/sec, structured JSON output, ~$0.05/1M tokens |
| PDF Parsing | pymupdf4llm | Outputs LLM-ready Markdown; handles multi-column layouts automatically |
| Fuzzy Matching | RapidFuzz | C++ backend, 10× faster than FuzzyWuzzy |
| Embeddings | all-MiniLM-L6-v2 | 384-dim, runs locally (no API cost), 14k sentences/sec on GPU |
| Vector Search | pgvector (PostgreSQL) | No separate vector DB; JOINs between metadata + embeddings in one SQL query |
| Async Jobs | Redis + Celery | Native retry, dead-letter support, 4-worker concurrency out of the box |

---

## 5. Technology Stack

### Backend

| Layer | Technology | Version |
|---|---|---|
| API Gateway | FastAPI | 0.111+ |
| Agent Orchestration | LangGraph | Latest |
| LLM Provider | Groq (Llama 3.1 8B / 70B) | API |
| PDF Parsing | pymupdf4llm + PyMuPDF | 0.0.17+ |
| DOCX Parsing | python-docx | 1.1+ |
| Skill Fuzzy Matching | RapidFuzz | 3.9+ |
| Embeddings | sentence-transformers | 3.0+ |
| Vector Search | pgvector | 0.7+ |
| Relational DB | PostgreSQL | 16 |
| Message Queue | Redis + Celery | 7 / 5.x |
| File Storage | Supabase Storage | API |
| Containerization | Docker + Docker Compose | Latest |

### Frontend

| Layer | Technology |
|---|---|
| Framework | Next.js 16.2 |
| UI Components | Radix UI + shadcn/ui |
| Styling | Tailwind CSS v4 |
| Icons | Lucide React |
| Auth Context | Custom React Context + HttpOnly cookies |
| Form Validation | Zod v4 |

### Infrastructure

| Component | Technology |
|---|---|
| Auth Service | FastAPI + asyncpg + bcrypt + PyJWT |
| OAuth | Google OAuth 2.0 |
| Email | Resend API |
| Observability | LangSmith (optional) |

---

## 6. Repository Structure

```
📂 TalentIntel-Enterprise/
│
├── 📂 backend/
│   ├── 📂 gateway-service/          # API Gateway: auth, rate limiting, routes
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI app entry, router mounting
│   │   │   ├── config.py            # Settings from env vars
│   │   │   ├── dependencies.py      # API key validation
│   │   │   ├── db.py                # SQLAlchemy connection
│   │   │   ├── middleware/
│   │   │   │   └── auth.py          # APIKeyMiddleware
│   │   │   └── routers/
│   │   │       ├── parse.py         # POST /api/v1/parse
│   │   │       ├── match.py         # POST /api/v1/match
│   │   │       ├── candidates.py    # GET  /api/v1/candidates/{id}/skills
│   │   │       └── skills.py        # GET  /api/v1/skills/taxonomy
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── 📂 orchestrator-service/     # LangGraph state machine + Celery workers
│   │   ├── app/
│   │   │   └── main.py              # Orchestrates parser → normalizer → DB
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── 📂 parser-service/           # Agent 1: Structural extraction
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI  POST /internal/parse
│   │   │   ├── config.py
│   │   │   ├── extraction.py        # Groq LLM call for entity extraction
│   │   │   ├── schemas.py           # ParsedResume, ParseResponse Pydantic models
│   │   │   └── parsers/
│   │   │       ├── pdf_parser.py    # pymupdf4llm → LLM-ready Markdown
│   │   │       ├── docx_parser.py   # python-docx extraction
│   │   │       └── txt_parser.py    # Encoding-safe text handler
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_parsers.py
│   │
│   ├── 📂 normalization-service/    # Agent 2: Skill normalization + hierarchy inference
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI  POST /internal/normalize
│   │   │   ├── config.py
│   │   │   ├── database.py          # asyncpg + Redis taxonomy cache
│   │   │   ├── fuzzy_matcher.py     # RapidFuzz WRatio matching
│   │   │   ├── llm_fallback.py      # Groq fallback for unknown skills
│   │   │   ├── schemas.py
│   │   │   └── routers/
│   │   │       └── normalize.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_normalizer.py
│   │
│   ├── 📂 matching-service/         # Agent 3: Semantic matching + gap analysis
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI  POST /internal/match
│   │   │   ├── config.py
│   │   │   ├── database.py          # asyncpg connection pool
│   │   │   ├── embedder.py          # sentence-transformers model loader
│   │   │   ├── matcher.py           # pgvector cosine similarity + scoring
│   │   │   ├── gap_analysis.py      # Skill gap computation + upskilling paths
│   │   │   ├── schemas/
│   │   │   │   └── match_schemas.py
│   │   │   └── routers/
│   │   │       └── match.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_matcher.py
│   │
│   ├── 📂 auth-service/             # Standalone auth microservice
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI: signup, signin, OAuth, session
│   │   │   ├── config.py
│   │   │   ├── database.py          # asyncpg pool
│   │   │   ├── dependencies.py      # JWT require_auth dependency
│   │   │   ├── lib/
│   │   │   │   ├── auth.py          # JWT, bcrypt, token generation
│   │   │   │   └── email.py         # Resend email verification
│   │   │   └── routers/
│   │   │       ├── signup.py
│   │   │       ├── signin.py
│   │   │       ├── session.py       # /refresh, /logout, /me
│   │   │       ├── verification.py  # Email verification + resend
│   │   │       └── google.py        # Google OAuth 2.0 callback
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── 📂 data/                     # Synthetic evaluation datasets
│   │   ├── resumes/                 # Sample PDF, DOCX, TXT resumes
│   │   ├── job_descriptions/        # Sample JDs for matching
│   │   └── ground_truth/            # Expert-labeled match scores
│   │
│   └── test_pipeline.py             # End-to-end integration test script
│
├── 📂 core-infrastructure/
│   ├── 📂 database/
│   │   ├── init.sql                 # Full PostgreSQL schema + pgvector
│   │   └── seed_taxonomy.sql        # 500+ skill taxonomy seed (expandable to 5,000+)
│   ├── docker-compose.yml           # Full stack orchestration
│   └── redis.conf                   # Redis LRU config
│
├── 📂 frontend/                     # Next.js 16 dashboard
│   ├── app/
│   │   ├── (auth)/                  # Auth routes: signIn, signUp, verify
│   │   ├── (main)/                  # Protected routes: analyser, dashboard
│   │   ├── api/upload/              # Next.js route handler for file upload
│   │   ├── components/
│   │   │   ├── auth/                # AuthLayout, AuthFormWrapper, OAuthButtons
│   │   │   ├── sidebar/             # Collapsible sidebar with user menu
│   │   │   └── ui/                  # shadcn/ui component library
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx      # Global auth state + apiFetch helper
│   │   └── lib/
│   │       ├── utils.ts             # cn() Tailwind merge utility
│   │       └── validations/auth.ts  # Zod schemas for auth forms
│   ├── middleware.ts                 # Route protection (has_session cookie)
│   └── package.json
│
├── 📂 sdk/
│   ├── python/talentintel/          # Python client SDK
│   └── javascript/src/              # JavaScript client SDK
│
├── Makefile                         # Dev convenience commands
└── README.md                        # ← You are here
```

---

## 7. Microservices Deep Dive

### 7.1 Gateway Service (Port 8000)

The API Gateway is the **single entry point** for all external traffic. It handles:

- **API Key Authentication** — SHA-256 hashed keys stored in PostgreSQL; validated on every request via middleware
- **Rate Limiting** — 60 requests/minute per key (configurable), Redis sliding window counter
- **Request Routing** — Proxies requests to internal services (parser, orchestrator, matcher)
- **Swagger/OpenAPI** — Auto-generated docs at `/docs` and `/redoc`

**Public Endpoints:**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/parse` | Single resume parse (sync) |
| `POST` | `/api/v1/parse/batch` | Batch resume parse (async) |
| `GET` | `/api/v1/parse/status/{job_id}` | Poll batch job status |
| `GET` | `/api/v1/candidates/{id}/skills` | Get candidate skill profile |
| `POST` | `/api/v1/match` | Match candidates to a JD |
| `GET` | `/api/v1/skills/taxonomy` | Browse the skill taxonomy |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

### 7.2 Orchestrator Service (LangGraph + Celery)

The Orchestrator is the **brain of the pipeline**. It manages a LangGraph state machine that coordinates the three agents sequentially, with retry logic and graceful degradation.

**LangGraph State Machine:**

```
START
  │
  ▼
[parse]  ──error──▶  [handle_error]
  │                        │
  ▼ success                │
[normalize] ──error──▶ [handle_error]
  │                        │
  ▼ success                │
[store in DB]               │
  │                        │
  ▼                        ▼
[notify webhook] ◀──────────┘
  │
  ▼
END
```

**Key behaviors:**
- Each node retries up to **3 times** with exponential backoff (1s, 2s, 4s)
- If parser succeeds but normalizer fails → candidate stored with `status: partial`, raw skills preserved
- Webhook callback fires on both success and partial failure
- Batch jobs dispatch one **Celery task per resume**, enabling 4× parallel processing

---

### 7.3 Parser Service (Port 8001)

Converts raw resume files to structured JSON. The two-stage pipeline is:

**Stage 1 — File → Text:**

```
PDF   → pymupdf4llm  → LLM-ready Markdown (headings, tables, multi-column preserved)
DOCX  → python-docx  → Paragraphs + tables as plain text
TXT   → chardet      → Encoding-safe string decode
```

**Stage 2 — Text → Structured JSON (Groq Llama 3.1 8B):**

The LLM is prompted with a strict JSON schema template and extracts:

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "work_experience": [
    {
      "company": "Acme Corp",
      "title": "Senior ML Engineer",
      "start_date": "Jan 2021",
      "end_date": "Present",
      "duration_months": 39,
      "technologies": ["Python", "TensorFlow", "K8s"],
      "is_current": true
    }
  ],
  "raw_skills": ["Python", "TensorFlow", "K8s", "React"],
  "confidence_score": 0.94,
  "warnings": []
}
```

**Error handling:**
- Groq timeout → 3× retry with exponential backoff, then return `confidence_score: 0.0`
- Invalid JSON from LLM → regex fallback extracts email + phone
- Empty document → `422 Unprocessable Entity`

**Internal endpoint:** `POST /internal/parse` (multipart form, file + optional candidate_id)

---

### 7.4 Normalization Service (Port 8002)

Maps raw, messy skill strings from resumes to canonical taxonomy entries and infers implicit parent skills.

**Two-Stage Matching:**

**Stage 1 — RapidFuzz (Fast Path):**
1. Exact match (case-insensitive) against `canonical_name` column
2. Exact match against `aliases` array (e.g., `k8s` → `Kubernetes`)
3. Fuzzy `WRatio` match across canonical + aliases:
   - Score ≥ 85 → auto-map, `matched_via: "fuzzy"`
   - Score 70–84 → map + flag for human review
   - Score < 70 → send to LLM fallback

**Stage 2 — Groq LLM Fallback:**
- Skills that RapidFuzz cannot map are sent to `llama-3.1-8b-instant` with a taxonomy category classification prompt
- Result has `confidence: 60.0` and `matched_via: "llm"`
- Truly unknown skills are flagged as `matched_via: "unresolved"` and stored in the `emerging_skills` table for human review

**Hierarchy Inference:**
```
TensorFlow  →  adds  →  Deep Learning, Machine Learning, AI
React       →  adds  →  Frontend Development, Web Development, JavaScript
Kubernetes  →  adds  →  Container Orchestration, DevOps, Cloud Computing
```

**Taxonomy Cache:** The full taxonomy is loaded from PostgreSQL into Redis on startup (TTL: 24 hours). Cache is invalidated and reloaded automatically on miss.

**Internal endpoint:** `POST /internal/normalize`

---

### 7.5 Matching Service (Port 8003)

Semantic candidate-to-job matching powered by vector embeddings and multi-factor scoring.

**Pipeline:**

```
1. Embed JD text
   all-MiniLM-L6-v2 → 384-dim float vector (loaded once at startup)

2. Query pgvector
   SELECT id, name, canonical_skills, skill_proficiencies, ...
          1 - (embedding <=> $1::vector) AS semantic_similarity
   FROM candidates
   WHERE 1 - (embedding <=> $1::vector) >= threshold
   ORDER BY semantic_similarity DESC
   LIMIT top_k;

3. Score each candidate (configurable weights)
   skill_score       = (matched_required / total_required) × 0.8
                     + (matched_nice / total_nice) × 0.2
   experience_score  = avg(proficiency_score per required skill)
                       Expert=1.0, Intermediate=0.6, Beginner=0.3
   education_score   = 1.0 if tech degree + tech JD, else 0.5
   composite_score   = w1 × skill_score
                     + w2 × experience_score
                     + w3 × education_score

4. Gap Analysis
   missing_required = required_skills − candidate.canonical_skills
   missing_nice     = nice_to_have − candidate.canonical_skills
   → Each gap includes: skill name, importance, suggested_resources[]
```

**Evaluation target:** NDCG@10 ≥ 0.85

**Internal endpoint:** `POST /internal/match`

---

### 7.6 Auth Service (Port 8001 standalone)

A self-contained authentication microservice used by the frontend dashboard.

**Features:**
- Email/password signup with bcrypt hashing
- Email verification via Resend (JWT token, 24-hour expiry)
- Sign in with session creation (access token: 15-min JWT, refresh token: 30-day random hex)
- **Token rotation** on every refresh — old token deleted, new token issued
- **Google OAuth 2.0** — authorization code flow, upserts users, sets same HttpOnly cookies
- HttpOnly cookie strategy (no tokens in localStorage):
  - `access_token` — httpOnly, 15 min
  - `refresh_token` — httpOnly, path `/auth/refresh`, 30 days
  - `has_session` — readable by Next.js middleware, 30 days
- Rate-limited resend verification: 3 requests per 30 minutes per email
- `/auth/me` protected endpoint returns current user profile

**Endpoints:** `POST /auth/signup`, `POST /auth/signin`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, `GET /auth/verify-email`, `POST /auth/resend-verification`, `GET /auth/google`, `GET /auth/google/callback`

---

### 7.7 Frontend (Next.js 16)

A dark-mode-ready, production-grade React dashboard.

**Pages:**

| Route | Description |
|---|---|
| `/` | Landing / redirect |
| `/signIn` | Email + password sign in, Google OAuth button |
| `/signUp` | Registration with Zod validation |
| `/verify-pending` | Email verification waiting screen with auto-poll + resend |
| `/error` | OAuth/verification error display |
| `/analyser` | Resume upload UI with XHR progress tracking |
| `/dashboard` | (In progress) Candidate insights dashboard |

**Key frontend patterns:**
- `AuthContext` provides `user`, `accessToken`, `login`, `logout`, `signup`, `apiFetch` globally
- `apiFetch` transparently retries with a refresh call on `401` before re-sending
- `middleware.ts` protects routes using the `has_session` cookie (no server-side JWT needed)
- File upload component uses raw `XMLHttpRequest` for real-time progress events
- Sidebar collapses to 64px on hover-out; expands with CSS transition

---

## 8. Database Schema

### Core Tables

```sql
-- Skill taxonomy: 5,000+ canonical skills with aliases and hierarchy
CREATE TABLE skill_taxonomy (
    id            SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    aliases        TEXT[]   DEFAULT '{}',      -- ["K8s", "k8s", "kube"]
    category       VARCHAR(100),               -- "Cloud & DevOps"
    parent_category VARCHAR(100),              -- "Technical Skills"
    hierarchy_path TEXT,                       -- "Technical Skills > Cloud & DevOps > Kubernetes"
    parent_skills  TEXT[]   DEFAULT '{}',      -- ["Container Orchestration", "DevOps"]
    description    TEXT,
    is_active      BOOLEAN  DEFAULT TRUE
);

-- Parsed candidates with vector embeddings
CREATE TABLE candidates (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                  VARCHAR(255),
    email                 VARCHAR(255),
    -- ... contact fields ...
    work_experience        JSONB DEFAULT '[]',
    education             JSONB DEFAULT '[]',
    raw_skills            TEXT[],              -- Original from resume
    canonical_skills      TEXT[],              -- After normalization
    skill_proficiencies   JSONB DEFAULT '{}',  -- {"Python": "Expert"}
    inferred_skills       TEXT[],             -- From hierarchy inference
    embedding             vector(384),        -- all-MiniLM-L6-v2 output
    processing_status     VARCHAR(20)         -- pending|processing|complete|partial|failed
);

-- Index for sub-millisecond vector search
CREATE INDEX idx_candidates_embedding
ON candidates USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Async batch job tracking
CREATE TABLE batch_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    total_files     INT DEFAULT 0,
    processed_files INT DEFAULT 0,
    failed_files    INT DEFAULT 0,
    status          VARCHAR(20),   -- pending|processing|complete|partial_failure
    webhook_url     VARCHAR(1000),
    completed_at    TIMESTAMPTZ
);

-- Auth tables
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    provider      VARCHAR(20) DEFAULT 'email',  -- 'email' | 'google'
    is_verified   BOOLEAN DEFAULT FALSE
);

CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,   -- SHA-256 of raw token
    device_name VARCHAR(255),
    ip_address  VARCHAR(45),
    expires_at  TIMESTAMPTZ NOT NULL
);
```

---

## 9. API Reference

### Authentication

All API endpoints require the `X-API-Key` header:

```
X-API-Key: sk_live_your_key_here
```

### Parse a Single Resume

```http
POST /api/v1/parse
Content-Type: multipart/form-data
X-API-Key: sk_live_...

file: <resume.pdf>
```

**Response 200:**
```json
{
  "candidate_id": "3fa85f64-...",
  "personal_info": { "name": "Jane Doe", "email": "jane@example.com" },
  "skills": {
    "canonical": ["Python", "TensorFlow", "Deep Learning"],
    "proficiencies": { "Python": "Expert", "TensorFlow": "Intermediate" },
    "inferred": ["Machine Learning", "AI"],
    "emerging": ["LangGraph"]
  },
  "processing_time_ms": 3240
}
```

### Match Candidates to a Job Description

```http
POST /api/v1/match
Content-Type: application/json
X-API-Key: sk_live_...

{
  "job_description": "Senior ML Engineer with 5+ years...",
  "required_skills": ["Python", "TensorFlow", "Kubernetes"],
  "nice_to_have_skills": ["Rust", "ONNX"],
  "threshold": 0.65,
  "top_k": 10,
  "weights": {
    "skill_match": 0.5,
    "experience_depth": 0.3,
    "education_relevance": 0.2
  }
}
```

**Response 200:**
```json
{
  "matches": [
    {
      "candidate_id": "...",
      "candidate_name": "Jane Doe",
      "composite_score": 0.89,
      "semantic_similarity": 0.92,
      "skill_match_score": 0.85,
      "matched_skills": ["Python", "TensorFlow"],
      "missing_skills": [
        {
          "skill_name": "Kubernetes",
          "importance": "required",
          "suggested_resources": ["CKA Certification (Linux Foundation)", "Kubernetes the Hard Way"]
        }
      ],
      "proficiency_breakdown": { "Python": "Expert", "TensorFlow": "Intermediate" }
    }
  ],
  "total_candidates_scanned": 1247,
  "processing_time_ms": 450
}
```

### Error Responses

```json
{ "error": "UNAUTHORIZED",   "message": "Invalid or missing API key",    "status_code": 401 }
{ "error": "RATE_LIMITED",   "message": "Retry after 23 seconds.",       "retry_after": 23,  "status_code": 429 }
{ "error": "FILE_TOO_LARGE", "message": "File exceeds 10MB limit.",                          "status_code": 413 }
{ "error": "PARSE_FAILED",   "message": "Document could not be parsed.", "status_code": 422 }
```

Full Swagger documentation is available at **`http://localhost:8000/docs`** when running locally.

---

## 10. Getting Started

### Prerequisites

- Docker & Docker Compose (v2.x+)
- Python 3.12+ (for local development without Docker)
- Node.js 20+ (for frontend development)
- A [Groq API key](https://console.groq.com) (free tier available)
- A [Supabase project](https://supabase.com) (free tier, for file storage)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/talentintel-enterprise.git
cd talentintel-enterprise
```

### 2. Configure environment variables

```bash
cp core-infrastructure/.env.example core-infrastructure/.env
```

Edit `.env` with your values (see [Configuration](#11-configuration) below).

For the frontend:

```bash
cp backend/.env.example backend/.env
# Fill in DATABASE_URL, JWT_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, RESEND_API_KEY
```

### 3. Start the full stack

```bash
make up
# OR
docker compose -f core-infrastructure/docker-compose.yml up -d
```

This starts:

| Service | Port | URL |
|---|---|---|
| Gateway API | 8000 | http://localhost:8000/docs |
| Parser | 8001 | http://localhost:8001/docs |
| Normalizer | 8002 | http://localhost:8002/docs |
| Matcher | 8003 | http://localhost:8003/docs |
| Orchestrator | 8004 | http://localhost:8004 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

The database is initialized automatically with:
- Full schema (`core-infrastructure/database/init.sql`)
- 500+ skill taxonomy seed (`core-infrastructure/database/seed_taxonomy.sql`)
- pgvector and uuid-ossp extensions enabled

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**.

### 5. Test the pipeline end-to-end

```bash
# Upload a resume and run through all three agents
python backend/test_pipeline.py path/to/resume.pdf
```

This will print the parsed JSON, normalized skills (with match methods and confidence scores), and matching results from the database.

### Makefile Commands

```bash
make up          # Start all Docker services
make down        # Stop all services
make logs        # Tail all service logs
make restart     # down + up
make db-reset    # Wipe volumes and restart fresh
make seed        # Re-run taxonomy seed SQL
make test        # Run all pytest suites
make lint        # Run ruff linter on backend/
```

---

## 11. Configuration

### `core-infrastructure/.env`

```env
# PostgreSQL
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://redis:6379/0

# LLM (required)
GROQ_API_KEY=gsk_your_groq_key_here

# Supabase Storage (required for file handling)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Embeddings (default works out of the box)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### `backend/.env` (Auth Service + Frontend API)

```env
DATABASE_URL=postgresql://admin:password@localhost:5432/talentintel
JWT_SECRET=your_32_char_random_secret_here
RESEND_API_KEY=re_your_resend_key
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
EMAIL_FROM=noreply@yourdomain.com
FRONTEND_URL=http://localhost:3000
APP_URL=http://localhost:8001
NODE_ENV=development
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## 12. Running Tests

Each service has its own test suite using `pytest`:

```bash
# Run all tests
make test

# Run specific service tests
cd backend/parser-service && pytest tests/ -v
cd backend/normalization-service && pytest tests/ -v
cd backend/matching-service && pytest tests/ -v
```

### What's Tested

**Parser Service (`tests/test_parsers.py`)**
- `GET /internal/health` returns `{ "status": "ok" }`
- TXT parser handles UTF-8 and Latin-1 encoding
- Unsupported file types return `422`
- Successful extraction with mocked Groq client
- Groq timeout returns `confidence_score: 0.0` with `"LLM timeout"` warning

**Normalization Service (`tests/test_normalizer.py`)**
- Exact canonical name match returns `confidence: 100.0`
- Alias match (`k8s` → `Kubernetes`) returns `confidence: 100.0`
- High-confidence fuzzy match (`ReAct JS` → `React`, score > 85)
- Low-confidence skill (`Photoshop`) returns `None` (not mapped)
- Empty/whitespace input returns `None`

**Matching Service (`tests/test_matcher.py`)**
- Missing required skill appears in gap output
- Missing optional skill marked `importance: "nice_to_have"`
- Fully matched candidate produces empty gaps list
- Importance labels are correct (`required` vs `nice_to_have`)

---

## 13. Evaluation Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| Resume parsing F1-score | ≥ 0.90 per field | Compare extracted fields vs. expert-labeled ground truth for 100 resumes |
| Skill normalization precision | ≥ 0.92 | % of raw skills correctly mapped to canonical taxonomy entries |
| Matching NDCG@10 | ≥ 0.85 | Normalized Discounted Cumulative Gain vs. expert-ranked candidate lists |
| End-to-end P95 latency | < 5 seconds | Parse + normalize + store (single resume, including Groq LLM call) |
| Batch throughput | 50 resumes < 3 min | 4 Celery workers × ~5s each, fully parallelized |
| API uptime | 99.9% | Health check monitoring across all services |
| API documentation | Complete | All endpoints documented with request/response examples at `/docs` |

### Dataset

Evaluation uses:
- `backend/data/resumes/` — 500+ sample resumes (PDF, DOCX, TXT) for parsing evaluation
- `backend/data/job_descriptions/` — 100+ sample JDs for matching evaluation
- `backend/data/ground_truth/` — Expert-labeled matching scores for NDCG@10 computation

---

## 14. SDK Usage

### Python SDK

```python
from talentintel import TalentIntelClient

client = TalentIntelClient(
    api_key="sk_live_abc123",
    base_url="https://api.talentintel.dev"  # or http://localhost:8000
)

# Parse a single resume (synchronous)
result = client.parse_resume("resume.pdf")
print(result.skills.canonical)
# ["Python", "TensorFlow", "Deep Learning", "Machine Learning", "AI"]

# Parse a batch asynchronously
job = client.parse_batch(
    "resumes.zip",
    webhook_url="https://myapp.com/webhooks/talentintel"
)
print(job.job_id)  # "batch-uuid-here"

# Poll for status
status = client.get_status(job.job_id)
print(status.progress)  # { "total": 47, "completed": 32, "failed": 1 }

# Match candidates to a job description
matches = client.match(
    job_description="Senior ML Engineer with 5+ years of Python, TensorFlow...",
    required_skills=["Python", "TensorFlow"],
    nice_to_have_skills=["Rust", "ONNX"],
    threshold=0.7,
    top_k=5
)
for m in matches.results:
    print(f"{m.candidate_name}: {m.composite_score:.2f} — missing: {[g.skill_name for g in m.missing_skills]}")
```

### JavaScript SDK

```javascript
import { TalentIntelClient } from '@talentintel/sdk';

const client = new TalentIntelClient({
  apiKey: 'sk_live_abc123',
  baseUrl: 'http://localhost:8000'
});

// Parse a resume from a File object
const result = await client.parseResume(file);
console.log(result.skills.canonical);

// Match candidates
const matches = await client.match({
  jobDescription: 'Senior ML Engineer with 5+ years...',
  requiredSkills: ['Python', 'TensorFlow'],
  threshold: 0.7,
  topK: 5,
});
matches.results.forEach(m =>
  console.log(`${m.candidateName}: ${m.compositeScore.toFixed(2)}`)
);
```

---

## 15. Contributing

### Team Roles (Hackathon)

| Role | Responsibilities |
|---|---|
| **M1 — AI Architect** | LangGraph orchestration, agent prompts, `graph.py`, asyncio fan-out |
| **M2 — Backend/Data** | FastAPI services, PostgreSQL schema, Redis/Celery |
| **M3 — Frontend/UX** | Next.js dashboard, auth UI, SSE integration |
| **M4 — Growth/Product** | Demo video, FinOps pitch, Resume Roaster feature |

### Development Workflow

```bash
# 1. Branch from main
git checkout -b feature/your-feature

# 2. Make changes + run linter
make lint

# 3. Run tests
make test

# 4. Open PR against main
```

### Adding Skills to the Taxonomy

Edit `core-infrastructure/database/seed_taxonomy.sql` and add a new `INSERT` row:

```sql
INSERT INTO skill_taxonomy (canonical_name, aliases, category, parent_category, hierarchy_path, parent_skills, description)
VALUES (
  'LangGraph',
  ARRAY['langgraph'],
  'AI & Machine Learning',
  'Technical Skills',
  'Technical Skills > AI & Machine Learning > LangGraph',
  ARRAY['LLM Development', 'AI', 'Agentic Workflows'],
  'A library for building stateful, multi-actor applications with LLMs.'
) ON CONFLICT (canonical_name) DO NOTHING;
```

Then re-run: `make seed`

---

## License

MIT © 2026 TalentIntel Enterprise Team · Tic-Tech-Toe '26 · DA-IICT

---

<div align="center">
  <strong>Built with ❤️ at DA-IICT for Prama Innovations · Tic-Tech-Toe '26</strong><br/>
  <em>FinOps + Agentic AI · Problem Statement 9</em>
</div>
