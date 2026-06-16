from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum  # <-- ADD THIS LINE

class ExperienceLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    ALL = "all"

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
    experience_level: Optional[str] = None
    keywords_found: list[str] = []

class JobResponse(BaseModel):
    id: UUID
    title: str
    company: str
    location: Optional[str]
    apply_url: Optional[str]
    source: str
    is_remote: bool
    experience_level: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int