"""Base fetcher abstract class."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

from app.models import Job
from app.core.logging import logger


class BaseFetcher(ABC):
    """Abstract base class for all job fetchers."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logger.bind(fetcher=name)
    
    @abstractmethod
    async def fetch_jobs(
        self, 
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Job]:
        """Fetch jobs from the source."""
        pass
    
    @abstractmethod
    async def validate_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize job data."""
        pass
    
    async def save_jobs(self, jobs: List[Job]) -> Dict[str, Any]:
        """Save jobs to database."""
        pass
    
    
    
