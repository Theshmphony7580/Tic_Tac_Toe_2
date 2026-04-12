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

-- Skill Embeddings (for semantic normalization)
-- Each canonical skill gets a 384-dim vector so semantically similar skills cluster together
-- e.g., "K8s", "Kubernetes", "Container Orchestration" all close in vector space
CREATE TABLE IF NOT EXISTS skill_embeddings (
    id SERIAL PRIMARY KEY,
    skill_id INT NOT NULL REFERENCES skill_taxonomy(id) ON DELETE CASCADE,
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_skill_embeddings_vector ON skill_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
CREATE INDEX idx_skill_embeddings_name ON skill_embeddings(canonical_name);

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

-- ═══════════════════════════════════════════════════════════════════
-- AUTH TABLES
-- ═══════════════════════════════════════════════════════════════════

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    avatar_url VARCHAR(500),
    provider VARCHAR(20) DEFAULT 'email',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- OAuth Accounts (Google, etc.)
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL,
    provider_account_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    UNIQUE (provider, provider_account_id)
);

CREATE INDEX idx_oauth_accounts_user ON oauth_accounts(user_id);

-- Refresh Tokens (session management)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    device_name VARCHAR(255),
    ip_address VARCHAR(45),
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- Candidate Applications
-- Tracks a candidate's application to a specific role,
-- decoupled from the candidate's parsed resume data.
CREATE TABLE candidate_applications (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id  UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,

    -- Role-specific info
    role          VARCHAR(100) NOT NULL,

    -- Computed match score (0–100)
    skills_match_pct  SMALLINT CHECK (skills_match_pct BETWEEN 0 AND 100),
    suitable          BOOLEAN DEFAULT FALSE,

    -- "4 Years" stored as an integer for sorting/filtering
    -- Display formatting (e.g. "4 Years") is handled at the app layer
    experience_years  SMALLINT,

    -- Where the candidate came from: 'LinkedIn', 'Referral', 'Naukri', etc.
    source        VARCHAR(50),

    applied_date  DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Lifecycle: new | reviewing | shortlisted | rejected | hired
    status        VARCHAR(20) NOT NULL DEFAULT 'new',

    -- Resume file
    resume_file_url   VARCHAR(1000),
    resume_file_type  VARCHAR(10) CHECK (resume_file_type IN ('pdf', 'docx', 'txt')),

    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_applications_candidate   ON candidate_applications(candidate_id);
CREATE INDEX idx_applications_status      ON candidate_applications(status);
CREATE INDEX idx_applications_role        ON candidate_applications(role);
CREATE INDEX idx_applications_applied     ON candidate_applications(applied_date DESC);
CREATE INDEX idx_applications_skills_match ON candidate_applications(skills_match_pct DESC);