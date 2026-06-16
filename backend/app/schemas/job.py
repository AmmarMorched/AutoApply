from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class JobCreate(BaseModel):
    external_id: Optional[str] = None
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    apply_url: Optional[str] = None
    source: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    is_remote: bool = False
    keywords_found: list[str] = []

class JobResponse(BaseModel):
    id: UUID
    title: str
    company: str
    location: Optional[str]
    apply_url: Optional[str]
    source: str
    is_remote: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int