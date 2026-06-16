from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobResponse, JobListResponse
from app.services.scraper.service import ScraperService

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = None,
    search: Optional[str] = None,
    remote_only: bool = False,
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

@router.post("/scrape")
async def scrape_jobs(
    keywords: list[str] = Query(["software engineer", "python developer"]),
    db: AsyncSession = Depends(get_db)
):
    scraper = ScraperService(db)
    new_jobs = await scraper.scrape_all(keywords)
    return {"message": "Scraping complete", "new_jobs_found": new_jobs}

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)