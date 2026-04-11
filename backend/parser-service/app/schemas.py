from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional, List

class WorkExperience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    is_current: bool = False

class Education(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    duration: Optional[str] = None

class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None

class ParseRequest(BaseModel):
    file_url: str
    file_type: str
    candidate_id: Optional[UUID] = None
    
    @field_validator("file_type")
    def validate_file_type(cls, v):
        v = v.lower()
        if v not in {"pdf", "docx", "txt"}:
            raise ValueError("Unsupported file type. Must be 'pdf', 'docx', or 'txt'.")
        return v

class ParsedCandidate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None
    total_experience_years: Optional[float] = None
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    raw_skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    raw_text: str = ""
    confidence_score: float = 0.0
    warnings: List[str] = Field(default_factory=list)

class ParseResponse(BaseModel):
    success: bool
    candidate_id: Optional[UUID] = None
    data: Optional[ParsedCandidate] = None
    error: Optional[str] = None
    processing_time_ms: int
