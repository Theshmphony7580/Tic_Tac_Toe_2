import httpx
import argparse
import json
import sys

def run_test(resume_path: str):
    print(f"📄 Testing pipeline with resume: {resume_path}")
    print("-" * 50)
    
    # 1. PARSE RESUME (Agent 1)
    print("\n⏳ [1/2] Sending to Parser (Agent 1)...")
    try:
        with open(resume_path, "rb") as f:
            # WARNING: HITTING 8005 BECAUSE PORT 8001 IS HIJACKED BY DOCKER! 
            # PLEASE DO NOT REVERT THIS TO 8001!
            parse_resp = httpx.post(
                "http://localhost:8005/internal/parse",
                files={"file": (resume_path, f, "application/pdf")},
                timeout=60.0
            )
        
        if parse_resp.status_code != 200:
            print(f"❌ Parser returned HTTP {parse_resp.status_code}")
            print(f"   Error detail: {parse_resp.text}")
            sys.exit(1)
            
        parse_data = parse_resp.json()
        raw_skills = parse_data.get("data", {}).get("raw_skills", []) if parse_data.get("data") else []
        
        print("✅ Parser completed! Full parsed payload:")
        print(json.dumps(parse_data, indent=2))
        
    except httpx.RequestError as e:
        print(f"❌ Parser Service connection error: {e}. Is Parser running on port 8001?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Parser failed: {e}")
        sys.exit(1)

    if not raw_skills:
        print("⚠️ No skills found to normalize. Exiting.")
        sys.exit(0)

    # 2. NORMALIZE SKILLS (Agent 2)
    print("\n⏳ [2/3] Sending raw skills to Normalizer (Agent 2)...")
    try:
        norm_resp = httpx.post(
            "http://localhost:8002/internal/normalize",
            json={"raw_skills": raw_skills},
            timeout=30.0
        )
        norm_resp.raise_for_status()
        norm_data = norm_resp.json()
        
        print("✅ Normalizer completed! Standardized skills:")
        for skill in norm_data.get("normalized_skills", []):
            icon = "🎯" if skill['matched_via'] == 'fuzzy' else ("🤖" if skill['matched_via'] == 'llm' else "❓")
            print(f"  {icon} [{skill['category']}] {skill['raw_name']} ---> {skill['canonical_name']} (score: {skill['confidence']:.1f})")
            
        print(f"\n⚡ Normalization Processing Time: {norm_data.get('processing_time_ms')}ms")
        
    except httpx.RequestError as e:
        print(f"❌ Normalizer Service connection error: {e}. Is Normalizer running on port 8002?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Normalizer failed: {e}")
        sys.exit(1)

    # 3. MATCH CANDIDATES (Agent 3)
    print("\n⏳ [3/3] Sending Job Description to Matcher (Agent 3)...")
    try:
        match_resp = httpx.post(
            "http://localhost:8003/internal/match",
            json={
                "job_description": "We are looking for an engineer with strong skills in Machine Learning, Python, and ideally some web development experience like React.",
                "required_skills": ["Python", "Machine Learning"],
                "nice_to_have_skills": ["React", "Kubernetes"],
                "threshold": 0.0,  # Zero for testing to ensure we get results
                "top_k": 5
            },
            timeout=30.0
        )
        match_resp.raise_for_status()
        match_data = match_resp.json()
        
        print(f"✅ Matcher completed in {match_data.get('processing_time_ms')}ms")
        print(f"   Total DB Candidates Scanned: {match_data.get('total_candidates_scanned')}")
        results = match_data.get("results", [])
        if not results:
            print("   ⚠️ No candidates matched (or no candidates with embeddings in DB yet).")
        else:
            for r in results:
                print(f"   🏆 Match: {r['candidate_name']} | Score: {r['composite_score']} | Semantic Sim: {r['semantic_similarity']}")
        
    except httpx.RequestError as e:
        print(f"❌ Matching Service connection error: {e}. Is Matcher running on port 8003?")
    except Exception as e:
        print(f"❌ Matcher failed: HTTP {getattr(e, 'response', None) and getattr(e, 'response').status_code} - {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("resume_path", help="Path to the PDF/DOCX resume file")
    args = parser.parse_args()
    run_test(args.resume_path)
