"""Remotely job fetcher implementation."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from bs4 import BeautifulSoup
import httpx

from app.services.fetchers.base import BaseFetcher
from app.schemas.job import JobCreate
from app.core.logging import logger


class RemotelyFetcher(BaseFetcher):
    """Remotely.com (or similar remote-first) job board fetcher."""

    def __init__(self):
        super().__init__("Remotely")
        # Placeholder base URL - in a real implementation we would target the specific remote jobs API/HTML
        self.base_url = "https://remotely.work/api/jobs" 
        self.rate_limiter = asyncio.Semaphore(5)
        
    async def fetch_jobs(
        self,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[JobCreate]:
        """Fetch jobs from Remotely."""
        
        logger.info(f"Starting Remotely job fetch with limit={limit}")
        
        try:
            jobs_data = await self._fetch_jobs_data()
            
            if not jobs_data:
                logger.warning("No jobs returned from Remotely")
                return []
                
            normalized_jobs = []
            
            for job_data in jobs_data:
                normalized_job = await self.validate_job(job_data)
                if normalized_job:
                    normalized_jobs.append(normalized_job)
                    
            filtered_jobs = self._apply_filters(normalized_jobs, filters)
            
            logger.info(
                f"Remotely fetch completed successfully. "
                f"Fetched={len(normalized_jobs)}, "
                f"Filtered={len(filtered_jobs)}"
            )
            
            return filtered_jobs[:limit]
            
        except Exception as e:
            logger.exception(f"Remotely fetch failed: {e}")
            return []
            
    async def _fetch_jobs_data(self) -> List[Dict[str, Any]]:
        """Fetch job data from Remotely."""
        # Using a dummy implementation for now.
        # This should hit a remote jobs API.
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        try:
            # We would normally do an httpx GET here. For the agent we return mock data
            # until the exact remote jobs endpoint is provided or scraped via beautifulsoup.
            # return await httpx.get(self.base_url, headers=headers).json()
            
            return [] # Empty for now, acts as a template/stub
            
        except Exception as e:
            logger.exception("Failed fetching Remotely jobs")
            return []

    def _apply_filters(
        self,
        jobs: List[JobCreate],
        filters: Optional[Dict[str, Any]]
    ) -> List[JobCreate]:
        """Apply optional filters. Remotely is an international source, so remote-only
        enforcement always applies regardless of whether other filters are provided."""

        filtered_jobs = [j for j in jobs if j.remote_status.lower() == "remote"]

        if not filters:
            return filtered_jobs

        if filters.get("search"):
            search_term = filters["search"].lower()
            filtered_jobs = [
                job for job in filtered_jobs
                if search_term in job.title.lower()
                or search_term in job.company.lower()
                or search_term in job.jd_text.lower()
            ]
            
        return filtered_jobs

    async def validate_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        """Validate and normalize job."""
        try:
            description = job_data.get("description", "")
            
            job_dict = {
                "title": job_data.get("title", ""),
                "company": job_data.get("company", ""),
                "location": job_data.get("location", "Remote"),
                "salary": None,  # Parse if available
                "source": "Remotely",
                "job_url": job_data.get("url", ""),
                "posted_at": self._parse_datetime(job_data.get("posted_at", "")),
                "jd_text": description,
                "applicant_count": job_data.get("applicant_count", 0),
                "remote_status": "remote", # Always remote
                "domain_tags": self._extract_domain_tags(description),
                "raw_metadata": job_data
            }
            
            return JobCreate(**job_dict)
            
        except Exception as e:
            logger.exception("Remotely job validation failed")
            return None

    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime safely."""
        if not date_str:
            return datetime.utcnow()
        try:
            if "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.utcnow()

    def _extract_domain_tags(self, description: str) -> List[str]:
        """Extract PM-related domain tags."""
        if not description:
            return []
            
        pm_domains = ["product", "saas", "b2b", "analytics", "ai", "machine learning"]
        description_lower = description.lower()
        tags = [domain for domain in pm_domains if domain in description_lower]
        return list(set(tags))
