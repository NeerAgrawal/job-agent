"""Base fetcher abstract class."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

from app.database.repositories import JobRepository
from app.database.session import get_db_session
from app.models.entities import Job
from app.core.logging import logger


class BaseFetcher(ABC):
    """Abstract base class for all job fetchers."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
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
    
    async def get_fetch_statistics(self) -> Dict[str, Any]:
        """Get fetch statistics."""
        pass
    
    def _log_info(self, message: str, **kwargs):
        """Log information message."""
        self.logger.info(message, **kwargs)
    
    def _log_error(self, message: str, error: Exception, **kwargs):
        """Log error message."""
        self.logger.error(f"{message}: {error}", **kwargs)
    
    def _log_warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def _log_debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
