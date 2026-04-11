from app.schemas import SkillGap

# Static learning resource map — top missing skills → suggested resources
LEARNING_RESOURCES: dict[str, list[str]] = {
    "kubernetes": ["CKA Certification (Linux Foundation)", "Kubernetes the Hard Way (GitHub)"],
    "docker": ["Docker Mastery (Udemy)", "Play with Docker (labs.play-with-docker.com)"],
    "terraform": ["HashiCorp Terraform Associate Cert", "Terraform on AWS (A Cloud Guru)"],
    "python": ["Python.org Official Tutorial", "Automate the Boring Stuff (free)"],
    "tensorflow": ["TensorFlow Developer Certificate (Google)", "DeepLearning.AI TF Course"],
    "pytorch": ["PyTorch 60-min Blitz (pytorch.org)", "Fast.ai Practical Deep Learning"],
    "react": ["React Official Docs + Tutorial", "Full Stack Open (University of Helsinki)"],
    "typescript": ["TypeScript Handbook (typescriptlang.org)", "Total TypeScript (free tier)"],
    "aws": ["AWS Cloud Practitioner Essentials (free)", "AWS Solutions Architect Associate"],
    "mlops": ["MLflow Documentation", "Made With ML (madewithml.com)"],
    "rust": ["The Rust Book (doc.rust-lang.org/book)", "Rustlings exercises"],
    "onnx": ["ONNX Documentation", "ONNX Runtime Python API Docs"],
}

DEFAULT_RESOURCES = ["Search Coursera / Udemy for skill-specific courses", "Check official documentation"]


def compute_gaps(
    candidate_skills: list[str],
    required_skills: list[str],
    nice_to_have_skills: list[str],
) -> list[SkillGap]:
    lowered_candidate = {s.lower() for s in candidate_skills}
    gaps: list[SkillGap] = []

    for skill in required_skills:
        if skill.lower() not in lowered_candidate:
            resources = LEARNING_RESOURCES.get(skill.lower(), DEFAULT_RESOURCES)
            gaps.append(SkillGap(
                skill_name=skill,
                importance="required",
                suggested_resources=resources,
            ))

    for skill in nice_to_have_skills:
        if skill.lower() not in lowered_candidate:
            resources = LEARNING_RESOURCES.get(skill.lower(), DEFAULT_RESOURCES)
            gaps.append(SkillGap(
                skill_name=skill,
                importance="nice_to_have",
                suggested_resources=resources,
            ))

    return gaps
