from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.services.resume.tailor import ResumeTailor
from app.services.resume.generator import DocxGenerator

router = APIRouter(prefix="/resumes", tags=["resumes"])

# 🔴 REPLACE THIS WITH YOUR ACTUAL RESUME
MASTER_RESUME = {
    "name": "Your Name",
    "email": "your@email.com",
    "phone": "+1234567890",
    "location": "City, Country",
    "summary": "Experienced software engineer with 5+ years...",
    "experience": [
        {
            "title": "Senior Developer",
            "company": "Current Company",
            "dates": "2021 - Present",
            "bullets": [
                "Led development of microservices architecture serving 1M+ users",
                "Reduced system latency by 40% through optimization",
                "Mentored team of 4 junior developers"
            ]
        },
        {
            "title": "Software Engineer",
            "company": "Previous Company",
            "dates": "2019 - 2021",
            "bullets": [
                "Built REST APIs serving 500K daily requests",
                "Implemented CI/CD pipeline reducing deploy time by 60%"
            ]
        }
    ],
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "React", "TypeScript"],
    "education": [
        {"degree": "BS Computer Science", "school": "University Name", "year": "2019"}
    ]
}

@router.post("/generate/{job_id}")
async def generate_resume(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    tailor = ResumeTailor()
    tailored_content, match_score, keywords = await tailor.tailor(
        MASTER_RESUME,
        job.description or "",
        job.title,
        job.company
    )
    
    generator = DocxGenerator()
    full_resume = {**MASTER_RESUME, **tailored_content}
    docx_path = generator.generate(full_resume)
    
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

@router.get("/{resume_id}/download")
async def download_resume(resume_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return FileResponse(
        resume.docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"resume-{resume.job.company if resume.job else 'custom'}.docx"
    )