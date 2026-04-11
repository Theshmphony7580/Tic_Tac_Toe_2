from pydantic import BaseModel, Field
from typing import Optional

# --- Request ---
class ScoreWeights(BaseModel):
    skill_match: float = 0.5
    experience_depth: float = 0.3
    education_relevance: float = 0.2

class MatchRequest(BaseModel):
    job_description: str = Field(..., min_length=10)
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    threshold: float = Field(default=0.55, ge=0.0, le=1.0)
    top_k: int = Field(default=10, ge=1, le=50)
    weights: ScoreWeights = Field(default_factory=ScoreWeights)

# --- Response ---
class SkillGap(BaseModel):
    skill_name: str
    importance: str                     # "required" | "nice_to_have"
    suggested_resources: list[str]      # ["Kubernetes CKA course", "Docker fundamentals"]

class CandidateMatch(BaseModel):
    candidate_id: str
    candidate_name: str
    semantic_similarity: float
    skill_match_score: float
    experience_score: float
    education_score: float
    composite_score: float
    matched_skills: list[str]
    missing_skills: list[SkillGap]
    proficiency_breakdown: dict[str, str]   # {"Python": "Expert", "K8s": "Intermediate"}

class MatchResult(BaseModel):
    job_description_hash: str
    total_candidates_scanned: int
    threshold_used: float
    results: list[CandidateMatch]
    processing_time_ms: int
