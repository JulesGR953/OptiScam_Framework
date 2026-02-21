"""
OptiScam FastAPI Backend

Start with:
    python -m uvicorn api:app --host 0.0.0.0 --port 8000

The frontend (Next.js) connects to this server via http://localhost:8000.
"""

import os
import uuid
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from main import OptiScamAnalyzer

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="OptiScam API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # open during local development
    allow_credentials=False,      # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Load models once at startup (Qwen3-VL + Whisper + TrOCR)
# ---------------------------------------------------------------------------

print("Initializing OptiScam models (this takes ~30 s on first run)...")
analyzer = OptiScamAnalyzer()
print("Models ready — API is accepting requests.\n")

# In-memory job store: {job_id: {"status": ..., "result": ..., "error": ...}}
jobs: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_safe(obj):
    """Recursively convert numpy / non-JSON-serializable types to plain Python."""
    try:
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# Background analysis worker
# ---------------------------------------------------------------------------

def _run_analysis(
    job_id: str,
    video_path: str,
    title: Optional[str],
    description: Optional[str],
    holistic: bool,
):
    try:
        jobs[job_id]["status"] = "running"

        if holistic:
            result = analyzer.analyze_video_holistic(
                video_path=video_path,
                title=title or None,
                description=description or None,
            )
        else:
            result = analyzer.process_video(
                video_path=video_path,
                title=title or None,
                description=description or None,
            )

        # Drop non-serializable config blob before returning
        result.pop("config", None)

        jobs[job_id] = {
            "status": "done",
            "result": _json_safe(result),
        }

    except Exception as e:
        import traceback
        jobs[job_id] = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

    finally:
        # Remove the uploaded file to free disk space
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """Quick health check — confirms API and models are loaded."""
    return {"status": "ok", "models_loaded": True}


@app.post("/analyze")
async def analyze(
    video: UploadFile,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    holistic: str = Form("false"),          # FormData booleans arrive as strings
):
    """
    Accept a video file upload and start a background analysis job.

    Returns immediately with a job_id.
    Poll GET /job/{job_id} to get status and results.
    """
    job_id = str(uuid.uuid4())
    suffix = Path(video.filename or "video.mp4").suffix or ".mp4"
    video_path = os.path.join(UPLOAD_DIR, f"{job_id}{suffix}")

    # Write uploaded bytes to disk
    content = await video.read()
    with open(video_path, "wb") as f:
        f.write(content)

    jobs[job_id] = {"status": "pending"}

    # Run the ML pipeline in a background thread (it's blocking / GPU-bound)
    thread = threading.Thread(
        target=_run_analysis,
        args=(job_id, video_path, title, description, holistic.lower() == "true"),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id}


@app.post("/analyze-youtube")
async def analyze_youtube(
    url: str = Form(...),
    holistic: str = Form("false"),
):
    """
    Download a YouTube video via yt-dlp, extract its title + description,
    then run the same analysis pipeline as /analyze.

    Returns immediately with a job_id. Poll GET /job/{job_id} for progress.
    Status flow: pending → downloading → running → done / error
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "url": url}

    thread = threading.Thread(
        target=_run_youtube_analysis,
        args=(job_id, url, holistic.lower() == "true"),
        daemon=True,
    )
    thread.start()

    return {"job_id": job_id}


def _run_youtube_analysis(job_id: str, url: str, holistic: bool):
    """Download the YouTube video with yt-dlp, then hand off to _run_analysis."""
    try:
        import yt_dlp
    except ImportError:
        jobs[job_id] = {
            "status": "error",
            "error": "yt-dlp is not installed. Run: pip install yt-dlp",
        }
        return

    video_path = os.path.join(UPLOAD_DIR, f"{job_id}.mp4")

    ydl_opts = {
        # Prefer MP4 ≤720p; fall back to best available
        "format": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": video_path,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        # Write actual output filename into yt-dlp's internal path (handles
        # cases where yt-dlp adds a suffix like .f137.mp4)
        "noplaylist": True,
    }

    try:
        jobs[job_id]["status"] = "downloading"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title         = info.get("title")       or None
        description   = info.get("description") or None
        thumbnail_url = info.get("thumbnail")   or None

        # Expose thumbnail so the frontend can show it during analysis
        if thumbnail_url:
            jobs[job_id]["thumbnail_url"] = thumbnail_url

        # yt-dlp may have named the file differently; find the actual path
        actual_path = video_path
        if not os.path.exists(actual_path):
            # Try common suffixes yt-dlp appends when merging streams
            for candidate in Path(UPLOAD_DIR).glob(f"{job_id}.*"):
                actual_path = str(candidate)
                break

        _run_analysis(job_id, actual_path, title, description, holistic)

    except Exception as e:
        import traceback
        jobs[job_id] = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
        # Clean up any partial download
        for f in Path(UPLOAD_DIR).glob(f"{job_id}*"):
            try:
                f.unlink()
            except Exception:
                pass


@app.get("/job/{job_id}")
def get_job(job_id: str):
    """
    Poll for job status and results.

    Returns:
        {"status": "pending"}      — queued, not started yet
        {"status": "downloading"}  — yt-dlp is fetching the YouTube video
        {"status": "running"}      — AI analysis in progress
        {"status": "done", "result": {...}}   — complete
        {"status": "error", "error": "..."}   — failed
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]
