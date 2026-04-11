import logging
from rapidfuzz import fuzz, process
from typing import List, Tuple, Optional
from app.schemas import TaxonomyRecord, NormalizedSkill
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def exact_or_fuzzy_match(raw_skill: str, taxonomy: List[TaxonomyRecord]) -> Optional[NormalizedSkill]:
    """
    Attempts to match a raw skill string to the canonical list or aliases using RapidFuzz.
    Returns a NormalizedSkill if it finds a high confidence match, else None.
    """
    raw_lower = raw_skill.strip().lower()
    if not raw_lower:
        return None

    best_score = 0.0
    best_canonical = None
    best_category = None

    for record in taxonomy:
        # Check canonical exact match
        if raw_lower == record.canonical_name.lower():
            return NormalizedSkill(
                raw_name=raw_skill,
                canonical_name=record.canonical_name,
                category=record.category,
                confidence=100.0,
                matched_via="fuzzy"
            )
            
        # Check aliases exact match
        for alias in record.aliases:
            if raw_lower == alias.lower():
                return NormalizedSkill(
                    raw_name=raw_skill,
                    canonical_name=record.canonical_name,
                    category=record.category,
                    confidence=100.0,
                    matched_via="fuzzy"
                )

        # Proceed to Fuzzy Matching (WRatio handles case, substring, and partial matches well)
        score_canonical = fuzz.WRatio(raw_lower, record.canonical_name.lower())
        
        # Take the best score among the canonical name and aliases
        best_candidate_score = score_canonical
        for alias in record.aliases:
            alias_score = fuzz.WRatio(raw_lower, alias.lower())
            if alias_score > best_candidate_score:
                best_candidate_score = alias_score
                
        if best_candidate_score > best_score:
            best_score = best_candidate_score
            best_canonical = record.canonical_name
            best_category = record.category

    # Determine if the best fuzzy match meets the threshold
    if best_score >= settings.fuzz_match_threshold:
        return NormalizedSkill(
            raw_name=raw_skill,
            canonical_name=best_canonical,
            category=best_category,
            confidence=best_score,
            matched_via="fuzzy"
        )

    return None

def normalize_skills_via_fuzzy(raw_skills: List[str], taxonomy: List[TaxonomyRecord]) -> Tuple[List[NormalizedSkill], List[str]]:
    """
    Processes a list of raw skills.
    Returns a tuple: (List of matched normalized skills, List of unresolved raw skills)
    """
    resolved = []
    unresolved = []
    
    for skill in raw_skills:
        match = exact_or_fuzzy_match(skill, taxonomy)
        if match:
            resolved.append(match)
        else:
            unresolved.append(skill)
            
    return resolved, unresolved
