import pytest
from app.gap_analysis import compute_gaps
from app.schemas import SkillGap

def test_gap_analysis_required_missing():
    candidate = ["Python", "FastAPI"]
    required = ["Python", "Kubernetes"]
    nice = ["Rust"]
    
    gaps = compute_gaps(candidate, required, nice)
    
    gap_names = [g.skill_name for g in gaps]
    assert "Kubernetes" in gap_names
    assert "Rust" in gap_names
    assert "Python" not in gap_names

def test_gap_analysis_importance_labels():
    candidate = []
    required = ["Python"]
    nice = ["Rust"]
    
    gaps = compute_gaps(candidate, required, nice)
    
    by_name = {g.skill_name: g for g in gaps}
    assert by_name["Python"].importance == "required"
    assert by_name["Rust"].importance == "nice_to_have"

def test_gap_analysis_all_matched():
    candidate = ["Python", "Kubernetes"]
    required = ["Python", "Kubernetes"]
    nice = []
    
    gaps = compute_gaps(candidate, required, nice)
    assert len(gaps) == 0
