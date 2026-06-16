import os
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.services.resume.tailor import ResumeTailor
from app.services.resume.generator import DocxGenerator
from app.services.resume.generator import PdfGenerator
from app.services.resume.parser import ResumeParser
from app.services.resume.structurer import ResumeStructurer


router = APIRouter(prefix="/resumes", tags=["resumes"])


# ─────────────────────────────────────────────────
# LOAD MASTER RESUME
# ─────────────────────────────────────────────────
def _load_master_resume():
    """Load master resume from JSON file."""
    master_path = os.path.join(
        os.path.dirname(__file__),
        "..", "services", "resume", "master_resume.json"
    )
    master_path = os.path.abspath(master_path)
    
    if os.path.exists(master_path):
        with open(master_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback default
    return {
        "name": "Your Name",
        "email": "your@email.com",
        "phone": "+1234567890",
        "location": "City, Country",
        "summary": "Experienced professional...",
        "experience": [],
        "skills": [],
        "education": [],
        "languages": [],
        "certifications": [],
    }


def _save_master_resume(data: dict):
    """Save master resume to JSON file."""
    master_path = os.path.join(
        os.path.dirname(__file__),
        "..", "services", "resume", "master_resume.json"
    )
    master_path = os.path.abspath(master_path)
    os.makedirs(os.path.dirname(master_path), exist_ok=True)
    
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────
# GENERATE TAILORED RESUME
# ─────────────────────────────────────────────────
@router.post("/generate/{job_id}")
async def generate_resume(job_id: str, db: AsyncSession = Depends(get_db)):
    """Generate an ATS-tailored resume for a specific job."""
    
    # Get the job
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.description:
        raise HTTPException(status_code=400, detail="Job has no description to tailor against")
    
    # Load master resume
    master = _load_master_resume()
    
    # Tailor the resume
    tailor = ResumeTailor()
    tailored_content, match_score, keywords = await tailor.tailor(
        master,
        job.description or "",
        job.title,
        job.company
    )
    
    # Generate DOCX
    generator = PdfGenerator()
    full_resume = {**master, **tailored_content}
    docx_path = generator.generate(full_resume)
    
    # Save to database
    resume = Resume(
        job_id=job.id,
        tailored_content=full_resume,
        docx_path=docx_path,
        match_score=match_score,
        keywords_matched=keywords,
        status="completed"
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    
    return {
        "id": str(resume.id),
        "match_score": match_score,
        "keywords_matched": keywords,
        "download_url": f"/api/v1/resumes/{resume.id}/download"
    }


# ─────────────────────────────────────────────────
# DOWNLOAD RESUME
# ─────────────────────────────────────────────────
@router.get("/{resume_id}/download")
async def download_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    """Download the generated DOCX resume file."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not resume.docx_path or not os.path.exists(resume.docx_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        resume.docx_path,
        media_type="application/pdf",
        filename=f"resume-{resume.job.company if resume.job else 'custom'}.pdf"
    )


# ─────────────────────────────────────────────────
# UPLOAD & STRUCTURE OLD RESUME
# ─────────────────────────────────────────────────
@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
):
    """Upload an old resume (PDF/DOCX) and convert to structured master format."""
    
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.doc', '.txt']
    file_ext = os.path.splitext(file.filename or "resume.pdf")[1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read file
    file_bytes = await file.read()
    
    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Parse the file
    parser = ResumeParser()
    try:
        raw_text = parser.parse(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    if len(raw_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not extract enough text from the file")
    
    # Structure with AI
    structurer = ResumeStructurer()
    structured = await structurer.structure(raw_text)
    structured = structurer.validate_and_clean(structured)
    
    # Save as master resume
    _save_master_resume(structured)
    
    return {
        "message": "Resume processed and saved as master resume",
        "preview": {
            "name": structured.get("name", ""),
            "email": structured.get("email", ""),
            "experience_count": len(structured.get("experience", [])),
            "skills_count": len(structured.get("skills", [])),
            "education_count": len(structured.get("education", [])),
        },
        "full_resume": structured,
        "raw_text_length": len(raw_text),
    }


# ─────────────────────────────────────────────────
# VIEW / EDIT MASTER RESUME
# ─────────────────────────────────────────────────
@router.get("/master")
async def get_master_resume():
    """View the current master resume."""
    return _load_master_resume()


@router.put("/master")
async def update_master_resume(resume_data: dict):
    """Manually update the master resume."""
    _save_master_resume(resume_data)
    return {
        "message": "Master resume updated",
        "skills_count": len(resume_data.get("skills", [])),
        "experience_count": len(resume_data.get("experience", [])),
    }