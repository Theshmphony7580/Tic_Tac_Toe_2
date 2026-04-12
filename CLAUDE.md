# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TalentIntel Enterprise** — A multi-agent AI system for resume parsing, skill normalization, and talent matching. The repo name (`Tic_Tac_Toe_2`) does not reflect the actual project.

## Development Commands

### Backend (Docker-based)
```bash
make up          # Start all services (Docker Compose)
make down        # Stop services
make restart     # Restart all services
make logs        # Stream service logs
make test        # Run pytest on backend/
make lint        # Run ruff on backend/
make seed        # Seed PostgreSQL with skill taxonomy
make db-reset    # Reset database volumes
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Starts on http://localhost:3000
```

### Integration Testing
```bash
python backend/test_pipeline.py --resume path/to/resume.pdf
```

### Running a Single Test
```bash
pytest backend/path/to/test_file.py::test_function_name
```

## Service Ports

| Service | Port |
|---------|------|
| API Gateway | 8000 |
| Parser Service | 8001 |
| Normalization Service | 8002 |
| Matching Service | 8003 |
| Orchestrator Service | 8004 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Frontend | 3000 |

## Architecture

Multi-agent microservices system with LangGraph orchestration:

```
Frontend (Next.js 16, React 19)
    ↓ REST
API Gateway (FastAPI :8000) — API key auth, rate limiting, CORS
    ↓
Orchestrator (LangGraph + Celery :8004) ←→ Redis Queue (:6379)
    ↓ coordinates
Parser (:8001) → Normalization (:8002) → Matcher (:8003)
    ↓                ↓                        ↓
                 PostgreSQL 16 + pgvector (:5432)
```

**Data flow:** File upload → text extraction (PyMuPDF/python-docx) → LLM structured extraction (Groq Llama 3.1 8B) → skill normalization (RapidFuzz + LLM fallback) → semantic matching (sentence-transformers + pgvector) → results stored in PostgreSQL.

## Key Files

| File | Role |
|------|------|
| `implementation_plan.md` | Comprehensive PRD with architecture, agent specs, API docs |
| `backend/core-infrastructure/docker-compose.yml` | Primary Docker Compose for all services |
| `backend/gateway-service/app/main.py` | Gateway FastAPI entry point; auth middleware |
| `backend/gateway-service/app/routers/parse.py` | `POST /api/v1/parse` main endpoint |
| `backend/parser-service/app/extraction.py` | Groq LLM extraction logic |
| `backend/parser-service/app/parsers/` | PDF/DOCX/TXT file parsers |
| `backend/normalization-service/app/fuzzy_matcher.py` | RapidFuzz skill matching + taxonomy |
| `backend/normalization-service/app/llm_fallback.py` | Groq LLM fallback for ambiguous skills |
| `backend/matching-service/app/matcher.py` | pgvector cosine similarity queries |
| `backend/matching-service/app/gap_analysis.py` | Skill gap computation |
| `backend/orchestrator-service/app/main.py` | LangGraph state machine + Celery bootstrap |
| `backend/core-infrastructure/database/init.sql` | PostgreSQL schema |
| `backend/core-infrastructure/database/seed_taxonomy.sql` | 5,000+ skill taxonomy seed data |
| `backend/test_pipeline.py` | Full pipeline integration test |

## Environment Variables

Copy `backend/EXAMPLE_ENV` to `backend/.env`. Required variables:
```
DATABASE_URL=postgresql://admin:changeme@postgres:5432/talentintel
REDIS_URL=redis://redis:6379/0
GROQ_API_KEY=<your_groq_api_key>
POSTGRES_PASSWORD=changeme
```
`SUPABASE_URL` and `SUPABASE_KEY` are optional.

## Tech Stack

- **Backend:** Python 3.12 (uv), FastAPI, Uvicorn, asyncpg
- **LLM:** Groq API (Llama 3.1 8B) for extraction and skill normalization fallback
- **Skill matching:** RapidFuzz (fuzzy), sentence-transformers + pgvector (semantic)
- **Orchestration:** LangGraph state machine, Celery + Redis for async batch jobs
- **File parsing:** PyMuPDF4LLM (PDF), python-docx (DOCX)
- **Frontend:** Next.js 16.2.3, React 19, TailwindCSS v4, shadcn/ui, Zod
- **Database:** PostgreSQL 16 + pgvector extension
- **Linting:** Ruff (Python), ESLint (TypeScript)

## Inter-Service Communication

- **Synchronous:** HTTP calls between gateway and microservices (internal network)
- **Asynchronous:** Celery tasks via Redis for batch resume processing
- Each service exposes internal endpoints (e.g., `POST /internal/parse`) not meant for external consumption

## Current State Notes

- LangGraph orchestration layer is partially implemented
- Frontend is early-stage (basic auth flow only)
- No CI/CD pipeline exists yet
- SDKs available in `sdk/python/` and `sdk/javascript/` for API consumers
