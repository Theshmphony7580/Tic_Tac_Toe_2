import pytest
from app.fuzzy_matcher import exact_or_fuzzy_match
from app.schemas import TaxonomyRecord

MOCK_TAXONOMY = [
    TaxonomyRecord(canonical_name="Python", aliases=["py", "python3"], category="Programming Languages"),
    TaxonomyRecord(canonical_name="Kubernetes", aliases=["k8s"], category="Cloud & DevOps"),
    TaxonomyRecord(canonical_name="React", aliases=["React.js", "ReactJS"], category="Frontend Frameworks"),
]

def test_exact_match():
    # Canonical exact match
    res = exact_or_fuzzy_match("Python", MOCK_TAXONOMY)
    assert res is not None
    assert res.canonical_name == "Python"
    assert res.confidence == 100.0

    # Alias exact match
    res = exact_or_fuzzy_match("k8s", MOCK_TAXONOMY)
    assert res is not None
    assert res.canonical_name == "Kubernetes"
    assert res.confidence == 100.0

def test_fuzzy_match_high_confidence():
    # Capitalization & substring differences
    res = exact_or_fuzzy_match("ReAct JS", MOCK_TAXONOMY)
    assert res is not None
    assert res.canonical_name == "React"
    assert res.confidence > 85.0

def test_fuzzy_match_low_confidence():
    # Should not match any
    res = exact_or_fuzzy_match("Photoshop", MOCK_TAXONOMY)
    assert res is None

def test_empty_string():
    res = exact_or_fuzzy_match("   ", MOCK_TAXONOMY)
    assert res is None
