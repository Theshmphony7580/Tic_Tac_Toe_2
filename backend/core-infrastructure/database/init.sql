-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- API Keys for authentication
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(64) NOT NULL UNIQUE,     -- SHA-256 hash of the API key
    owner_name VARCHAR(255) NOT NULL,
    permissions TEXT[] DEFAULT ARRAY['read', 'write'],
    rate_limit_per_minute INT DEFAULT 60,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Candidates (parsed resumes)
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- Index for fast vector similarity search (100 lists is a good starting point)
CREATE INDEX idx_candidates_embedding ON candidates USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- B-tree indexes for fast lookups
CREATE INDEX idx_candidates_email ON candidates(email);

-- Skill Taxonomy (Lookup table)
CREATE TABLE skill_taxonomy (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    aliases TEXT[] DEFAULT '{}',                 -- ["JS", "ECMAScript", "ES6"]
    category VARCHAR(100),                       -- "Programming Languages"
    parent_category VARCHAR(100),                -- "Technical Skills"
    hierarchy_path TEXT,                          -- "Technical Skills > Programming Languages > JavaScript"
    parent_skills TEXT[] DEFAULT '{}',            -- Skills this implies (e.g., React -> ["Frontend Dev"])
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for the taxonomy
CREATE INDEX idx_skill_taxonomy_name ON skill_taxonomy(canonical_name);
CREATE INDEX idx_skill_taxonomy_aliases ON skill_taxonomy USING GIN(aliases);

-- Batch Jobs (for async processing tracking)
CREATE TABLE batch_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES api_keys(id),
    total_files INT DEFAULT 0,
    processed_files INT DEFAULT 0,
    failed_files INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',        -- pending|processing|complete|partial_failure
    webhook_url VARCHAR(1000),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_batch_jobs_status ON batch_jobs(status);

-- Individual file tracking within a batch
CREATE TABLE batch_job_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    raw_skill VARCHAR(255) NOT NULL UNIQUE,
    occurrence_count INT DEFAULT 1,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed BOOLEAN DEFAULT FALSE,
    added_to_taxonomy BOOLEAN DEFAULT FALSE,
    canonical_mapping VARCHAR(255)               -- Set after human review
);
