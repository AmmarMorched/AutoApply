from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobResponse, JobListResponse
import hashlib
from app.services.scraper.service import ScraperService

router = APIRouter(prefix="/jobs", tags=["jobs"])

# ──────────────────────────────────────────────
# 1. LIST JOBS (with filters)
# ──────────────────────────────────────────────
@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    search: Optional[str] = None,
    remote_only: bool = False,
    experience_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Job)
    
    if source:
        query = query.where(Job.source == source)
    if search:
        query = query.where(
            Job.title.ilike(f"%{search}%") | 
            Job.company.ilike(f"%{search}%")
        )
    if remote_only:
        query = query.where(Job.is_remote == True)
    if experience_level and experience_level != "all":
        if experience_level == "unknown":
            query = query.where(Job.experience_level.is_(None))
        else:
            query = query.where(Job.experience_level == experience_level)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    query = query.order_by(Job.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size
    )

# ──────────────────────────────────────────────
# 2. STATS (MUST be before /{job_id})
# ──────────────────────────────────────────────
@router.get("/stats")
async def job_stats(db: AsyncSession = Depends(get_db)):
    """Get job statistics by experience level and source"""
    
    total_result = await db.execute(select(func.count()).select_from(Job))
    total = total_result.scalar()
    
    exp_result = await db.execute(
        select(Job.experience_level, func.count())
        .group_by(Job.experience_level)
    )
    by_experience = {row[0] or "unknown": row[1] for row in exp_result}
    
    source_result = await db.execute(
        select(Job.source, func.count())
        .group_by(Job.source)
    )
    by_source = {row[0]: row[1] for row in source_result}
    
    return {
        "total_jobs": total,
        "by_experience": by_experience,
        "by_source": by_source
    }

# ──────────────────────────────────────────────
# 3. SCRAPE (MUST be before /{job_id})
# ──────────────────────────────────────────────
@router.post("/scrape")
async def scrape_jobs(
    keywords: list[str] = Query(["informatique", "développeur"]),
    location: str = "Tunisia",
    db: AsyncSession = Depends(get_db)
):
    scraper = ScraperService(db)
    new_jobs = await scraper.scrape_all(keywords, location)
    return {"message": "Scraping complete", "new_jobs_found": new_jobs}

# ──────────────────────────────────────────────
# 4. SINGLE JOB (MUST be LAST — catches all /{id})
# ──────────────────────────────────────────────
@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)



@router.post("/manual", response_model=JobResponse)
async def add_manual_job(
    title: str,
    company: str,
    apply_url: str = "",
    location: str = "Tunisia",
    description: str = "",
    experience_level: Optional[str] = None,
    source: str = "manual",
    db: AsyncSession = Depends(get_db)
):
    """Manually add a job you found yourself"""
    
    ext_id = hashlib.md5(f"{title}-{company}-manual-{title}".encode()).hexdigest()
    
    job = Job(
        external_id=ext_id,
        title=title,
        company=company,
        location=location,
        description=description,
        apply_url=apply_url,
        source=source,
        experience_level=experience_level,
        keywords_found=[title],
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return JobResponse.model_validate(job)