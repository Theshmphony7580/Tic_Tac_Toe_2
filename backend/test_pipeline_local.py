"""
Local Integration Test — Agent 1 → Agent 2 → Agent 3

Tests the full pipeline WITHOUT Supabase:
  1. Parser: Extract from PDF
  2. Normalizer: Map skills to taxonomy
  3. Matcher: Generate embeddings & score

Usage:
    cd backend
    python test_pipeline_local.py path/to/resume.pdf
"""

import sys
import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "parser-service"))
sys.path.insert(0, str(Path(__file__).parent / "normalization-service"))
sys.path.insert(0, str(Path(__file__).parent / "matching-service"))

from app.parsers.pdf_parser import parse_pdf
from app.extraction import extract_from_text as parse_extract

# Re-path for normalization
sys.path.insert(0, str(Path(__file__).parent / "normalization-service"))
from app.fuzzy_matcher import normalize_skills_via_fuzzy
from app.schemas import TaxonomyRecord

from sentence_transformers import SentenceTransformer


async def load_sample_taxonomy() -> list[TaxonomyRecord]:
    """Load a small sample taxonomy without needing DB."""
    return [
        TaxonomyRecord(canonical_name="Python", aliases=["python3", "py"], category="Programming Languages"),
        TaxonomyRecord(canonical_name="JavaScript", aliases=["JS"], category="Programming Languages"),
        TaxonomyRecord(canonical_name="React", aliases=["React.js"], category="Frontend Frameworks"),
        TaxonomyRecord(canonical_name="Kubernetes", aliases=["K8s", "k8s"], category="Cloud & DevOps"),
        TaxonomyRecord(canonical_name="Docker", aliases=[], category="Cloud & DevOps"),
        TaxonomyRecord(canonical_name="AWS", aliases=[], category="Cloud Platforms"),
        TaxonomyRecord(canonical_name="Machine Learning", aliases=["ML"], category="AI & Machine Learning"),
        TaxonomyRecord(canonical_name="TensorFlow", aliases=["TF"], category="AI & Machine Learning"),
        TaxonomyRecord(canonical_name="FastAPI", aliases=[], category="Backend Frameworks"),
        TaxonomyRecord(canonical_name="Django", aliases=[], category="Backend Frameworks"),
        TaxonomyRecord(canonical_name="PostgreSQL", aliases=["Postgres"], category="Databases"),
        TaxonomyRecord(canonical_name="MongoDB", aliases=["Mongo"], category="Databases"),
        TaxonomyRecord(canonical_name="Git", aliases=[], category="Version Control"),
    ]


def test_pipeline(resume_path: str):
    """Run local pipeline test."""

    print("\n" + "="*70)
    print("LOCAL INTEGRATION TEST: Parser → Normalizer → Matcher")
    print("="*70 + "\n")

    resume_file = Path(resume_path)
    if not resume_file.exists():
        print(f"✗ Resume not found: {resume_path}")
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # AGENT 1: Parser
    # ─────────────────────────────────────────────────────────────────────────
    print("[AGENT 1] PARSER SERVICE")
    print("-" * 70)
    try:
        print(f"Parsing: {resume_file.name}")
        file_bytes = resume_file.read_bytes()
        raw_text = parse_pdf(file_bytes)
        print(f"  ✓ Extracted {len(raw_text)} chars")

        print("Extracting structured data with LLM...")
        parsed = parse_extract(raw_text)
        print(f"  ✓ Confidence: {parsed.confidence_score:.2f}")
        print(f"  ✓ Name: {parsed.name or 'N/A'}")
        print(f"  ✓ Raw skills: {len(parsed.raw_skills)} found")
        print(f"    {parsed.raw_skills[:3]}...")  # Preview first 3
    except Exception as e:
        print(f"  ✗ Parser failed: {e}")
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # AGENT 2: Normalizer
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[AGENT 2] NORMALIZATION SERVICE")
    print("-" * 70)
    try:
        print("Loading skill taxonomy...")
        taxonomy = asyncio.run(load_sample_taxonomy())
        print(f"  ✓ Loaded {len(taxonomy)} skills")

        print("Normalizing raw skills...")
        normalized, unresolved = normalize_skills_via_fuzzy(parsed.raw_skills, taxonomy)
        print(f"  ✓ Matched: {len(normalized)} skills")
        print(f"  ✓ Unresolved: {len(unresolved)} skills")
        if normalized:
            print(f"    Matched examples: {[n.canonical_name for n in normalized[:3]]}")
    except Exception as e:
        print(f"  ✗ Normalizer failed: {e}")
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # AGENT 3: Matcher (Embeddings)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[AGENT 3] MATCHING SERVICE")
    print("-" * 70)
    try:
        print("Loading embedding model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("  ✓ Model loaded (384-dim vectors)")

        print("Generating embeddings for resume...")
        embed_text = parsed.summary or raw_text[:1000]
        embedding = model.encode(embed_text, convert_to_numpy=True)
        print(f"  ✓ Generated {len(embedding)}-dim embedding")
        print(f"    Vector shape: {embedding.shape}")
        print(f"    Sample values: {embedding[:3]}")

        # Generate embeddings for candidate skills too
        if normalized:
            skill_text = " ".join([n.canonical_name for n in normalized])
            skill_embedding = model.encode(skill_text, convert_to_numpy=True)
            print(f"  ✓ Generated skill embedding from {len(normalized)} skills")

            # Compute similarity
            import numpy as np
            similarity = np.dot(embedding, skill_embedding) / (np.linalg.norm(embedding) * np.linalg.norm(skill_embedding))
            print(f"  ✓ Resume-to-skills cosine similarity: {similarity:.4f}")

    except Exception as e:
        print(f"  ✗ Matcher failed: {e}")
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("✓ LOCAL PIPELINE TEST PASSED")
    print("="*70)
    print(f"\nSummary:")
    print(f"  Candidate: {parsed.name or 'Unknown'}")
    print(f"  Email: {parsed.email or 'N/A'}")
    print(f"  Parsed skills: {len(parsed.raw_skills)}")
    print(f"  Normalized skills: {len(normalized)}")
    print(f"  Embedding dim: {len(embedding)}")
    print(f"\nNext steps:")
    print(f"  1. Set up local PostgreSQL with schema from init.sql")
    print(f"  2. Populate skill_embeddings table")
    print(f"  3. Run populate_vector_db.py on your 567 resumes")
    print()

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline_local.py <resume.pdf>")
        print(f"\nExample: python test_pipeline_local.py '../Mohit Resume.pdf'")
        sys.exit(1)

    success = test_pipeline(sys.argv[1])
    sys.exit(0 if success else 1)
