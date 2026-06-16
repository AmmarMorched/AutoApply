from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.job import Job
from app.schemas.job import JobCreate
from app.services.scraper.scraper_engine import ScraperEngine


class ScraperService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = ScraperEngine()
    
    async def scrape_all(self, keywords: List[str], location: str = "Tunisia") -> int:
        jobs = await self.engine.search_all(keywords)
        return await self._save_jobs(jobs)
    
    async def _save_jobs(self, jobs: List[JobCreate]) -> int:
        new_count = 0
        
        for job_data in jobs:
            if not job_data.external_id:
                continue
            
            existing = await self.db.execute(
                select(Job).where(
                    Job.external_id == job_data.external_id,
                    Job.source == job_data.source
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            job = Job(
                external_id=job_data.external_id,
                title=job_data.title,
                company=job_data.company,
                location=job_data.location,
                description=job_data.description,
                apply_url=job_data.apply_url,
                source=job_data.source,
                experience_level=job_data.experience_level,
                keywords_found=job_data.keywords_found,
            )
            self.db.add(job)
            new_count += 1
        
        await self.db.commit()
        print(f"💾 Saved {new_count} new jobs")
        return new_count