from typing import List, Optional
from pydantic import BaseModel, Field

class NormalizeRequest(BaseModel):
    candidate_id: Optional[str] = None
    raw_skills: List[str] = Field(..., description="List of raw skill strings extracted from the parser.")

class NormalizedSkill(BaseModel):
    raw_name: str
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    confidence: float
    matched_via: str = Field(..., description="'fuzzy', 'llm', or 'unresolved'")

class NormalizeResponse(BaseModel):
    success: bool
    candidate_id: Optional[str] = None
    normalized_skills: List[NormalizedSkill]
    processing_time_ms: int
    
class TaxonomyRecord(BaseModel):
    canonical_name: str
    aliases: List[str]
    category: str
