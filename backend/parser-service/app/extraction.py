import json
import logging
import re
from groq import Groq
import groq
from app.schemas import ParsedCandidate
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """
You are an expert resume parser with 10 years of experience reading 
resumes from all industries. Your task is to extract structured 
information from the provided resume text.

CRITICAL RULES:
1. Extract skills EXACTLY as written in the resume — do NOT normalize or expand them.
   e.g., if resume says "K8s", keep "K8s", not "Kubernetes"
2. For dates, use the exact format found in the resume (e.g., "Jan 2021", "2021-01")
3. If a field cannot be found, return null (not an empty string)
4. raw_skills must contain ALL skills mentioned anywhere in the document
   (work experience, projects, skills section, certifications)
5. Extract ALL work experiences, not just the most recent
6. confidence_score: 
   0.9–1.0 = well-formatted resume, all sections clear
   0.7–0.89 = minor ambiguities (missing dates, unclear sections)
   0.5–0.69 = poorly formatted, sections unclear
   0.0–0.49 = could not reliably extract (e.g., image-based PDF, 
               broken encoding, non-resume document)
7. warnings: list any fields that are missing or ambiguous as plain strings
8. Calculate total_experience_years by summing all work experience durations. Use your best estimation if months are missing.

Return ONLY valid JSON. No markdown, no explanation, no code blocks.
"""

def _regex_fallback(raw_text: str) -> ParsedCandidate:
    """Fallback extraction if LLM fails completely."""
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', raw_text)
    phone_match = re.search(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}', raw_text)
    
    return ParsedCandidate(
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        raw_text=raw_text,
        confidence_score=0.3,
        warnings=["LLM extraction failed, used regex fallback"]
    )

def extract_from_text(raw_text: str) -> ParsedCandidate:
    # Truncate if too long (Groq Llama 3.1 8B context is usually 8k, so keep it safe)
    max_chars = 12000
    if len(raw_text) > max_chars:
        logger.warning(f"Resume text truncated from {len(raw_text)} to {max_chars} chars")
        raw_text = raw_text[:max_chars]

    json_template = """
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "555-1234",
  "location": "New York, NY",
  "linkedin_url": null,
  "portfolio_url": null,
  "summary": "Experienced engineer...",
  "total_experience_years": 5.5,
  "work_experience": [
    {
      "company": "Tech Corp",
      "title": "Software Engineer",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "duration_months": 36,
      "description": "Built scalable APIs...",
      "technologies": ["Python", "AWS", "Docker"],
      "is_current": true
    }
  ],
  "education": [
    {
      "institution": "University X",
      "degree": "B.Sc. Computer Science",
      "field": "Computer Science",
      "graduation_year": "2019",
      "gpa": "3.8"
    }
  ],
  "certifications": [
    {
      "name": "AWS Solutions Architect",
      "issuer": "Amazon",
      "year": "2021"
    }
  ],
  "projects": [
    {
      "name": "Personal Website",
      "description": "Portfolio site",
      "technologies": ["React", "CSS"],
      "url": "https://jane.dev",
      "duration": null
    }
  ],
  "raw_skills": ["Python", "AWS", "Docker", "React", "CSS", "Machine Learning"],
  "languages": ["English", "Spanish"],
  "confidence_score": 0.95,
  "warnings": []
}"""

    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nEXPECTED JSON FORMAT (Match this structure exactly):\n{json_template}"},
        {"role": "user", "content": f"Parse this resume:\n\n{raw_text}"}
    ]

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=4096,
            timeout=settings.parser_timeout_seconds,
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        data["raw_text"] = raw_text
        
        return ParsedCandidate.model_validate(data)
        
    except groq.APITimeoutError:
        logger.error(f"Groq API timed out after {settings.parser_timeout_seconds}s")
        return ParsedCandidate(
            raw_text=raw_text,
            confidence_score=0.0,
            warnings=["LLM timeout"]
        )
    except groq.RateLimitError:
        logger.error("Groq rate limit hit")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Groq returned invalid JSON: {e}")
        return _regex_fallback(raw_text)
    except Exception as e:
        msg = str(e)
        if "invalid_api_key" in msg.lower() or "invalid api key" in msg.lower():
            logger.error(f"Groq authentication error: {e}")
            return ParsedCandidate(
                raw_text=raw_text,
                confidence_score=0.0,
                warnings=["Invalid API key for Groq. Please update GROQ_API_KEY."],
            )
        
        logger.error(f"Unexpected extraction error: {e}")
        return ParsedCandidate(
            raw_text=raw_text,
            confidence_score=0.0,
            warnings=[f"Unexpected error: {str(e)}"]
        )
