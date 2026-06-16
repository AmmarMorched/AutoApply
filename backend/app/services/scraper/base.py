# Abstract scraper class

from abc import ABC, abstractmethod
from typing import List
from app.schemas.job import JobCreate

class BaseScraper(ABC):
    @abstractmethod
    async def search(self, keywords: List[str], location: str, 
                     days_old: int = 7) -> List[JobCreate]:
        pass
    
    @abstractmethod
    async def deduplicate(self, jobs: List[JobCreate]) -> List[JobCreate]:
        pass