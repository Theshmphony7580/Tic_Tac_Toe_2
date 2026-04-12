import httpx
import time
import sys
import argparse
import uuid

def test_full_flow(file_path: str):
    orchestrator_url = "http://localhost:8004"
    
    print(f"🚀 Starting Full TalentIntel Pipeline Flow")
    print(f"📄 File: {file_path}")
    print("-" * 50)

    # 1. Trigger the process via Orchestrator
    print("\n⏳ [1/3] Triggering Orchestrator (/process)...")
    try:
        resp = httpx.post(
            f"{orchestrator_url}/process",
            json={"file_url": file_path, "file_type": "pdf"},
            timeout=10.0
        )
        if resp.status_code != 202:
            print(f"❌ Orchestrator rejected request: {resp.status_code}")
            print(f"   Detail: {resp.text}")
            return

        data = resp.json()
        job_id = data["job_id"]
        print(f"✅ Job Created! ID: {job_id}")
        
    except httpx.RequestError as e:
        print(f"❌ Could not connect to Orchestrator at {orchestrator_url}")
        print("   Make sure the FastAPI app is running on port 8004.")
        return

    # 2. Poll for status
    print(f"\n⏳ [2/3] Polling for completion (Job: {job_id})...")
    start_time = time.time()
    max_wait = 120 # 2 minutes
    
    while True:
        try:
            status_resp = httpx.get(f"{orchestrator_url}/status/{job_id}")
            status_data = status_resp.json()
            status = status_data["status"]
            
            elapsed = time.time() - start_time
            print(f"   [{int(elapsed)}s] Status: {status}")
            
            if status == "complete":
                print(f"✅ Pipeline Finished Successfully!")
                break
            elif status == "failed":
                print(f"❌ Pipeline Failed.")
                # Try to get the error from the status endpoint if we added it
                return
            
            if elapsed > max_wait:
                print(f"❌ Timeout after {max_wait}s.")
                return
                
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error polling status: {e}")
            return

    # 3. Verify in Matcher (Optional but helpful)
    print("\n⏳ [3/3] Verifying data visibility via Matcher (/match)...")
    try:
        matcher_url = "http://localhost:8003"
        match_resp = httpx.post(
            f"{matcher_url}/internal/match",
            json={
                "job_description": "General TalentIntel Test Match",
                "threshold": 0.1,
                "top_k": 3
            },
            timeout=10.0
        )
        if match_resp.status_code == 200:
            match_data = match_resp.json()
            results = match_data.get("results", [])
            print(f"✅ Matcher check complete. Found {len(results)} potential candidates.")
            for r in results:
                print(f"   🏆 Match: {r['candidate_name']} ({r['composite_score']})")
        else:
            print(f"⚠️ Matcher returned {match_resp.status_code}. It might not be running or empty.")
    except Exception as e:
        print(f"ℹ️ Skipping matcher check (Matcher might not be running).")

    print("\n" + "="*50)
    print("✨ INTEGRATION TEST COMPLETE ✨")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", help="Local absolute path to resume PDF")
    args = parser.parse_args()
    test_full_flow(args.file_path)
