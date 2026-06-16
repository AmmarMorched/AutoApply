from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.scraper.google_jobs import GoogleJobsScraper
from app.models.job import Job
from app.schemas.job import JobCreate

class ScraperService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.google_scraper = GoogleJobsScraper()
    
    async def scrape_all(self, keywords: List[str]) -> int:
        new_jobs = 0
        google_jobs = await self.google_scraper.search(keywords)
        new_jobs += await self._save_jobs(google_jobs)
        return new_jobs
    
    async def _save_jobs(self, jobs: List[JobCreate]) -> int:
        new_count = 0
        
        for job_data in jobs:
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
                salary_min=job_data.salary_min,
                salary_max=job_data.salary_max,
                is_remote=job_data.is_remote,
                keywords_found=job_data.keywords_found,
            )
            self.db.add(job)
            new_count += 1
        
        await self.db.commit()
        return new_count