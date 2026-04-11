import json
import logging
from typing import List
from groq import Groq, APITimeoutError
from app.schemas import TaxonomyRecord, NormalizedSkill
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

groq_client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """
You are an expert technical taxonomy normalizer. 
Your task is to take a list of unrecognized raw skills and map them to our official list of canonical categories.

The official broad categories are:
- Programming Languages
- Frontend Frameworks
- Backend Frameworks
- Databases
- Cloud & DevOps
- AI & Machine Learning
- Methodologies
- Interpersonal
- Cognitive
- Management
- Data Analysis
- Data Visualization
- Version Control
- Project Management Tools

If a skill is clearly a typo of a famous technology, you can normalize the canonical_name to the proper spelling, and assign the proper category.
If a skill is too vague, generic, or non-technical jargon, map it to the "Unknown" category.

Respond ONLY with valid JSON in this exact structure:
[
  {
    "raw_name": "<the raw skill you were analyzing>",
    "canonical_name": "<the corrected proper name, or the raw name if correct>",
    "category": "<one of the exact categories listed above, or 'Unknown'>"
  }
]
"""

def resolve_unknown_skills_via_llm(unresolved_skills: List[str], taxonomy: List[TaxonomyRecord]) -> List[NormalizedSkill]:
    """
    Uses a zero-shot LLM prompt to categorize skills the fuzzy matcher failed on.
    """
    if not unresolved_skills:
        return []

    # If the API key is not set, just return them as unresolved
    if not settings.groq_api_key or "your_" in settings.groq_api_key:
        logger.warning("Groq API key not provided, skipping LLM fallback.")
        return [
            NormalizedSkill(
                raw_name=skill,
                canonical_name=skill,
                category="Unknown",
                confidence=0.0,
                matched_via="unresolved"
            ) for skill in unresolved_skills
        ]

    prompt = f"Please analyze these unknown skills/terms:\n{json.dumps(unresolved_skills)}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    try:
        response = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            response_format={"type": "json_object"},  # We trick the prompt into giving an array by wrapping it or returning a dict with a list.
            temperature=0.0,
            timeout=settings.llm_timeout_seconds,
        )
        
        # Note: Groq JSON mode requires the output to be a JSON object, not a top-level array.
        # This means the model might output {"skills": [...]}. We should handle both dict and list parses.
        content = response.choices[0].message.content
        data = json.loads(content)
        
        extracted_list = []
        if isinstance(data, dict):
            # find the first list value in the dict
            for v in data.values():
                if isinstance(v, list):
                    extracted_list = v
                    break
        elif isinstance(data, list):
            extracted_list = data

        results = []
        for mapping in extracted_list:
            raw = mapping.get("raw_name")
            if not raw or raw not in unresolved_skills:
                continue
                
            results.append(NormalizedSkill(
                raw_name=raw,
                canonical_name=mapping.get("canonical_name", raw),
                category=mapping.get("category", "Unknown"),
                confidence=60.0, # Medium confidence for LLM guesses
                matched_via="llm"
            ))
            
        # Catch any that the LLM dropped
        matched_raws = {r.raw_name for r in results}
        for skill in unresolved_skills:
            if skill not in matched_raws:
                results.append(NormalizedSkill(
                    raw_name=skill, canonical_name=skill, category="Unknown", confidence=0.0, matched_via="unresolved"
                ))
                
        return results

    except Exception as e:
        logger.error(f"LLM fallback failed: {e}")
        return [
            NormalizedSkill(
                raw_name=skill,
                canonical_name=skill,
                category="Unknown",
                confidence=0.0,
                matched_via="unresolved"
            ) for skill in unresolved_skills
        ]
