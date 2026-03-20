import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

from ai_analyzer import analyze_image
from email_sender import send_email_with_report
from pdf_generator import generate_pdf

# ── Directories ──────────────────────────────────────────────────
UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports")
STATIC_DIR = Path("static")

UPLOAD_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Property Defect Inspection System",
    description="AI-powered property defect detection and report generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


# ── Health check ─────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    return {
        "status": "ok",
        "anthropic_api_key": "configured" if api_key_set else "MISSING – set ANTHROPIC_API_KEY",
        "timestamp": datetime.now().isoformat(),
    }


# ── Upload & Analyze ─────────────────────────────────────────────
@app.post("/api/analyze")
async def analyze_images(
    files: List[UploadFile] = File(...),
    property_address: str = Form(...),
    agent_name: str = Form(...),
    owner_name: str = Form(""),
    inspection_date: str = Form(...),
    unit_number: str = Form(""),
):
    if not files:
        raise HTTPException(400, "At least one image file is required.")

    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    for f in files:
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                400, f"File '{f.filename}' has unsupported type '{f.content_type}'. "
                "Only JPEG, PNG, GIF, and WebP are accepted."
            )

    session_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for upload in files:
        # Sanitise filename
        safe_name = Path(upload.filename).name
        file_path = session_dir / safe_name

        with open(file_path, "wb") as out:
            shutil.copyfileobj(upload.file, out)

        try:
            analysis = analyze_image(str(file_path))
        except Exception as e:
            analysis = {
                "defects": [],
                "overall_condition": "error",
                "summary": f"Analysis error: {e}",
            }

        results.append(
            {
                "filename": safe_name,
                "file_path": str(file_path),
                "analysis": analysis,
            }
        )

    session_data = {
        "session_id": session_id,
        "property_address": property_address,
        "agent_name": agent_name,
        "owner_name": owner_name,
        "inspection_date": inspection_date,
        "unit_number": unit_number,
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }

    with open(session_dir / "session.json", "w") as f:
        json.dump(session_data, f, indent=2)

    return JSONResponse(session_data)


# ── Generate Report ───────────────────────────────────────────────
@app.post("/api/generate-report")
async def generate_report_endpoint(payload: dict):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(400, "session_id is required.")

    session_dir = UPLOAD_DIR / session_id
    session_file = session_dir / "session.json"

    if not session_file.exists():
        raise HTTPException(404, "Session not found. Please re-upload your images.")

    with open(session_file) as f:
        session_data = json.load(f)

    report_path = REPORTS_DIR / f"report_{session_id}.pdf"

    try:
        generate_pdf(session_data, str(report_path))
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {e}")

    return JSONResponse(
        {
            "session_id": session_id,
            "download_url": f"/api/download/{session_id}",
            "message": "Report generated successfully.",
        }
    )


# ── Download Report ───────────────────────────────────────────────
@app.get("/api/download/{session_id}")
async def download_report(session_id: str):
    report_path = REPORTS_DIR / f"report_{session_id}.pdf"
    if not report_path.exists():
        raise HTTPException(404, "Report not found. Please generate the report first.")

    # Build a friendlier filename
    session_file = UPLOAD_DIR / session_id / "session.json"
    friendly = session_id[:8]
    if session_file.exists():
        with open(session_file) as f:
            sd = json.load(f)
        addr = sd.get("property_address", "")[:20].replace(" ", "_")
        date = sd.get("inspection_date", "").replace("-", "")
        friendly = f"{addr}_{date}" if addr else friendly

    return FileResponse(
        str(report_path),
        media_type="application/pdf",
        filename=f"inspection_report_{friendly}.pdf",
    )


# ── Send Email ────────────────────────────────────────────────────
@app.post("/api/send-email")
async def send_email_endpoint(payload: dict):
    session_id = payload.get("session_id")
    email = payload.get("email", "").strip()

    if not session_id:
        raise HTTPException(400, "session_id is required.")
    if not email or "@" not in email:
        raise HTTPException(400, "A valid email address is required.")

    report_path = REPORTS_DIR / f"report_{session_id}.pdf"
    if not report_path.exists():
        raise HTTPException(404, "Report not found. Please generate the report first.")

    session_file = UPLOAD_DIR / session_id / "session.json"
    if not session_file.exists():
        raise HTTPException(404, "Session data not found.")

    with open(session_file) as f:
        session_data = json.load(f)

    try:
        send_email_with_report(email, str(report_path), session_data)
    except ValueError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(500, f"Email delivery failed: {e}")

    return JSONResponse({"message": f"Report successfully sent to {email}."})
