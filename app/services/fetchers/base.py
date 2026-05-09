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
    async def validate_job(
        self,
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and normalize job data."""
        pass

    async def save_jobs(
        self,
        jobs: List[Job]
    ) -> Dict[str, Any]:
        """Save jobs to database."""
        pass

    def is_pm_role(self, title: str) -> bool:
        """
        Strict PM role filtering.
        Only allow real PM roles.
        """

        if not title:
            return False

        title = title.lower().strip()

        ACCEPT_KEYWORDS = [
            "product manager",
            "technical product manager",
            "senior product manager",
            "associate product manager",
            "platform product manager",
            "ai product manager",
            "growth product manager",
            "apm",
            "product owner",
        ]

        REJECT_KEYWORDS = [
            "account executive",
            "sales",
            "recruiter",
            "coordinator",
            "designer",
            "engineer",
            "developer",
            "marketing",
            "finance",
            "operations",
            "customer success",
            "support",
            "attorney",
            "legal",
            "hr",
            "analyst",
            "scientist",
            "android",
            "ios",
            "frontend",
            "backend",
            "full stack",
            "data engineer",
            "software engineer",
        ]

        has_accept = any(
            keyword in title
            for keyword in ACCEPT_KEYWORDS
        )

        has_reject = any(
            keyword in title
            for keyword in REJECT_KEYWORDS
        )

        return has_accept and not has_reject