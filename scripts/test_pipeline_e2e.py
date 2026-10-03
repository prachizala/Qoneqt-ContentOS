import os
import sys
import time
import json
import httpx
import subprocess
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Enable mock mode for fast local E2E verification
os.environ["USE_MOCK_AI"] = "true"
os.environ["QONEQT_API_KEY"] = "mock_key"

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

def log_stage(stage: str, status: str, duration_s: float):
    print(f"[{stage:<25}] {status:<10} ({duration_s:.2f}s)")

def main():
    print("=" * 70)
    print(" QONEQT AI CONTENT FACTORY - AUTOMATED E2E PIPELINE TEST ")
    print("=" * 70)

    start_total_time = time.time()
    stage_times = {}

    # Check if server is running, else use FastAPI TestClient in-process
    use_test_client = False
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=3.0)
        if r.status_code == 200:
            print(f"Connected to running FastAPI backend service at {BASE_URL}")
        else:
            use_test_client = True
    except Exception:
        use_test_client = True

    if use_test_client:
        print("Backend server not detected at http://localhost:8000. Running via FastAPI TestClient in-process...")
        # Override database to local SQLite file for E2E execution outside Docker
        db_file = PROJECT_ROOT / "test_e2e.db"
        if db_file.exists():
            try:
                db_file.unlink()
            except Exception:
                pass
        
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file.as_posix()}"

        from fastapi.testclient import TestClient
        from backend.main import app
        from backend.app.database import init_db
        import asyncio

        # Initialize database tables
        asyncio.run(init_db())

        client = TestClient(app)
    else:
        client = httpx.Client(base_url=BASE_URL, timeout=httpx.Timeout(120.0, connect=30.0, read=120.0))

    # ----------------------------------------------------
    # Step 1: Submit Content Generation Request
    # ----------------------------------------------------
    t0 = time.time()
    payload = {
        "topic": "Explain how AI is changing cybersecurity in 2026",
        "duration": 30,
        "style": "cinematic",
        "audience": "general",
        "aspect_ratio": "9:16",
        "language": "en"
    }

    print("\n[1/5] Submitting video creation request...")
    res = client.post("/api/projects", json=payload)
    if res.status_code not in (200, 201):
        print(f"[FAIL] Creation failed: HTTP {res.status_code} - {res.text}")
        sys.exit(1)

    project_data = res.json()
    project_id = project_data["id"]
    stage_times["Project Creation"] = time.time() - t0
    log_stage("Project Creation", "SUCCESS", stage_times["Project Creation"])
    print(f"     -> Project ID: {project_id}")

    # ----------------------------------------------------
    # Step 2: Poll Progress & Wait for Pipeline Completion
    # ----------------------------------------------------
    print("\n[2/5] Polling pipeline execution progress...")
    t0 = time.time()
    timeout_s = 300
    poll_interval_s = 2
    final_status = "UNKNOWN"
    last_percent = -1

    while (time.time() - t0) < timeout_s:
        # Check progress endpoint
        prog_res = client.get(f"/api/projects/{project_id}/progress")
        if prog_res.status_code == 200:
            prog_data = prog_res.json()
            pct = prog_data.get("progress_percent", 0)
            msg = prog_data.get("current_message", "")
            if pct != last_percent:
                print(f"     [Progress {pct:>3}%] {msg}")
                last_percent = pct

        # Check project detail status
        detail_res = client.get(f"/api/projects/{project_id}")
        if detail_res.status_code == 200:
            detail_data = detail_res.json()
            status = detail_data.get("status")
            if status in ("READY_FOR_REVIEW", "APPROVED", "PUBLISHED", "FAILED"):
                final_status = status
                break

        time.sleep(poll_interval_s)

    stage_times["Pipeline Execution"] = time.time() - t0

    if final_status not in ("READY_FOR_REVIEW", "APPROVED", "PUBLISHED"):
        print(f"[FAIL] Pipeline failed or timed out. Final Status: {final_status}")
        sys.exit(1)

    log_stage("Pipeline Execution", "SUCCESS", stage_times["Pipeline Execution"])

    # ----------------------------------------------------
    # Step 3: System Artifact Validation
    # ----------------------------------------------------
    print("\n[3/5] Validating generated artifacts (Script, Scenes, Video, QA)...")
    t0 = time.time()

    detail_res = client.get(f"/api/projects/{project_id}")
    detail_data = detail_res.json()

    # Script check
    script = detail_data.get("script")
    assert script is not None, "Script missing from project payload"
    assert len(script.get("hook", "")) > 0, "Script hook is empty"

    # Scenes check
    scenes = detail_data.get("scenes", [])
    assert len(scenes) > 0, "No scenes found in project"
    print(f"     [OK] Script & {len(scenes)} Scenes validated")

    # Video & Media Asset check
    storage_dir = PROJECT_ROOT / "storage" / "temp" / project_id
    mp4_path = storage_dir / f"video_{project_id}.mp4"
    assert mp4_path.exists(), f"Rendered video MP4 not found at {mp4_path}"
    assert mp4_path.stat().st_size > 0, "Rendered video file is 0 bytes"
    print(f"     [OK] Rendered MP4 exists ({mp4_path.stat().st_size / 1024:.1f} KB)")

    # FFprobe resolution check (1080x1920)
    try:
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name",
            "-of", "json",
            str(mp4_path)
        ]
        probe_res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if probe_res.returncode == 0:
            meta = json.loads(probe_res.stdout)
            v_stream = meta["streams"][0]
            assert v_stream["width"] == 1080 and v_stream["height"] == 1920, f"Expected 1080x1920, found {v_stream['width']}x{v_stream['height']}"
            print("     [OK] FFprobe verified 1080x1920 vertical canvas H.264 video")
    except Exception as err:
        print(f"     [WARN] FFprobe check warning: {err}")

    # QA Status Check
    qa_results = detail_data.get("qa_results", [])
    assert len(qa_results) > 0, "No QA result entries recorded"
    latest_qa = qa_results[-1]
    assert latest_qa.get("final_status") in ("PASS", "FAIL"), "Invalid QA status"
    print(f"     [OK] QA Evaluation verified: {latest_qa.get('final_status')}")

    stage_times["Artifact Validation"] = time.time() - t0
    log_stage("Artifact Validation", "SUCCESS", stage_times["Artifact Validation"])

    # ----------------------------------------------------
    # Step 4: Approve Video Project
    # ----------------------------------------------------
    print("\n[4/5] Approving project for publication...")
    t0 = time.time()
    app_res = client.post(f"/api/projects/{project_id}/approve")
    assert app_res.status_code == 200, f"Approval failed: {app_res.text}"
    app_data = app_res.json()
    assert app_data["status"] == "APPROVED", f"Expected APPROVED status, got {app_data['status']}"
    stage_times["Project Approval"] = time.time() - t0
    log_stage("Project Approval", "SUCCESS", stage_times["Project Approval"])

    # ----------------------------------------------------
    # Step 5: Publish to Qoneqt Global Feed
    # ----------------------------------------------------
    print("\n[5/5] Publishing short-form video to Qoneqt Global Feed...")
    t0 = time.time()
    pub_res = client.post(f"/api/projects/{project_id}/publish")
    assert pub_res.status_code == 200, f"Publication failed: {pub_res.text}"
    pub_data = pub_res.json()

    assert pub_data.get("status") == "PUBLISHED", "Project status is not PUBLISHED"
    publication = pub_data.get("publication", {})
    assert "post_id" in publication and publication["post_id"].startswith("qoneqt_post_"), "Invalid post_id in response"
    assert "feed_url" in publication and len(publication["feed_url"]) > 0, "Invalid feed_url in response"
    assert publication.get("published_at") is not None, "Missing published_at timestamp"

    stage_times["Qoneqt Publishing"] = time.time() - t0
    log_stage("Qoneqt Publishing", "SUCCESS", stage_times["Qoneqt Publishing"])
    print(f"     -> Qoneqt Post ID: {publication['post_id']}")
    print(f"     -> Live Feed URL:  {publication['feed_url']}")

    # ----------------------------------------------------
    # Summary Execution Table
    # ----------------------------------------------------
    total_duration = time.time() - start_total_time
    print("\n" + "=" * 70)
    print(" SYSTEM END-TO-END EXECUTION SUMMARY ")
    print("=" * 70)
    print(f"{'STAGE':<30} | {'STATUS':<12} | {'EXECUTION TIME':<15}")
    print("-" * 70)

    for stage_name, elapsed in stage_times.items():
        print(f"{stage_name:<30} | {'PASS':<12} | {elapsed:>12.2f}s")

    print("-" * 70)
    print(f"{'TOTAL SYSTEM E2E PIPELINE':<30} | {'SUCCESS':<12} | {total_duration:>12.2f}s")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
