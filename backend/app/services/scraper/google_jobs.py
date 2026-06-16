import hashlib
from typing import List
from serpapi import GoogleSearch
from app.config import settings
from app.schemas.job import JobCreate

class GoogleJobsScraper:
    def __init__(self):
        self.api_key = settings.serpapi_key
    
    async def search(
        self,
        keywords: List[str],
        location: str = "United States",
        remote_only: bool = True
    ) -> List[JobCreate]:
        all_jobs = []
        
        for keyword in keywords:
            params = {
                "api_key": self.api_key,
                "engine": "google_jobs",
                "q": keyword,
                "location": location,
                "hl": "en",
            }
            if remote_only:
                params["ltype"] = "1"
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            for job in results.get("jobs_results", []):
                job_data = self._parse_job(job, keyword)
                if job_data:
                    all_jobs.append(job_data)
        
        return all_jobs
    
    def _parse_job(self, job: dict, keyword: str) -> JobCreate:
        raw_id = f"{job.get('title', '')}-{job.get('company_name', '')}-{job.get('location', '')}"
        external_id = hashlib.md5(raw_id.encode()).hexdigest()
        
        apply_link = job.get("apply_link") or ""
        if not apply_link:
            related = job.get("related_links", [])
            if related:
                apply_link = related[0].get("link", "")
        
        return JobCreate(
            external_id=external_id,
            title=job.get("title", ""),
            company=job.get("company_name", ""),
            location=job.get("location", ""),
            description=job.get("description", ""),
            apply_url=apply_link,
            source="google_jobs",
            is_remote="remote" in job.get("location", "").lower(),
            keywords_found=[keyword],
        )