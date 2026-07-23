"""Base class for India job fetchers with PM role validation and India-specific features."""

import asyncio
import httpx
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from app.core.logging import logger
from app.services.ai.title_filters import get_title_category
from .utils import IndiaFetchUtils


class BaseIndiaFetcher:
    """Base class for India job fetchers."""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.logger = logger.bind(service=f"india_{name}")
        self.utils = IndiaFetchUtils()
    
    async def fetch_jobs(
    self,
    limit: int = 50,
    filters: dict | None = None,
    **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from the source."""

        try:

            self.logger.info(
                f"Starting {self.name} job fetch with limit={limit}"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:

                # Implementation overridden by subclasses
                jobs = await self._fetch_from_source(
                    client,
                    limit
                )

            # Apply PM filtering
            filtered_jobs = self._filter_pm_roles(jobs)

            self.logger.info(
                f"{self.name} fetch completed: "
                f"{len(jobs)} total, "
                f"{len(filtered_jobs)} PM jobs"
            )

            return filtered_jobs

        except Exception as e:

            self.logger.error(
                f"{self.name} fetch failed: {e}"
            )

            return []
    
    async def _fetch_from_source(self, client: httpx.AsyncClient, limit: int) -> List[Dict[str, Any]]:
        """Override in subclasses to implement actual fetching logic."""
        raise NotImplementedError("Subclasses must implement _fetch_from_source method")
    
    def _filter_pm_roles(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter jobs to target product-transition roles.

        Delegates to the shared title taxonomy so this coarse first-pass filter
        stays consistent with the orchestrator prefilter and the scorer.
        """
        pm_jobs = []

        for job in jobs:
            title = job.get('title', '')
            if get_title_category(title) == "pm":
                pm_jobs.append(job)
            else:
                self.logger.debug(f"Filtered non-target role: {title}")

        return pm_jobs
    
    def _validate_job(self, job: Dict[str, Any]) -> bool:
        """Validate job data completeness."""
        required_fields = ['title', 'company', 'location', 'job_url']
        
        for field in required_fields:
            if not job.get(field):
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate URL
        job_url = job.get('job_url', '')
        if not self.utils.is_valid_url(job_url):
            self.logger.warning(f"Invalid job URL: {job_url}")
            return False
        
        return True

    def _determine_remote_status(self, *signals: str) -> str:
        """Determine remote/hybrid/onsite from one or more raw text signals
        (e.g. location text, description, a structured remote-type tag). Combining
        every available signal here avoids subclasses deriving remote_status from a
        different field than the one used for the displayed location, which can
        otherwise show contradictory results (e.g. location 'Remote India' next to
        remote_status 'On-site')."""
        combined = " ".join(str(s) for s in signals if s).lower()

        if any(keyword in combined for keyword in ["remote_okay", "remote", "work from home", "wfh"]):
            return "remote"
        if "hybrid" in combined:
            return "hybrid"
        return "onsite"

    def _normalize_location(self, location: str) -> str:
        """Normalize India location names."""
        if not location:
            return "Not specified"
        
        location_lower = location.lower()
        
        # City mappings
        city_mappings = {
            'bengaluru': 'Bangalore',
            'gurugram': 'Gurgaon', 
            'noida': 'Noida',
            'chennai': 'Chennai',
            'mumbai': 'Mumbai',
            'delhi': 'Delhi NCR',
            'hyderabad': 'Hyderabad',
            'pune': 'Pune'
        }
        
        # Apply city normalization
        for city, normalized in city_mappings.items():
            if city in location_lower:
                return normalized
        
        # Handle remote/hybrid
        if any(remote in location_lower for remote in ['remote', 'hybrid', 'work from home']):
            return 'Remote India'
        
        if any(india in location_lower for india in ['india']):
            return 'India'
        
        return location.title()
    
    def _parse_salary(self, salary_text: str) -> str:
        """Parse salary information."""
        if not salary_text:
            return "Not specified"
        
        # Look for LPA format
        if 'lpa' in salary_text.lower():
            return salary_text
        
        # Look for range format
        if '-' in salary_text and any(char.isdigit() for char in salary_text):
            return f"₹{salary_text}"
        
        return salary_text
    
    def _extract_domain_tags(self, description: str) -> List[str]:
        """Extract domain tags from job description."""
        if not description:
            return []
        
        description_lower = description.lower()
        domain_tags = []
        
        # Tech domains
        tech_domains = ['saas', 'fintech', 'healthcare', 'education', 'e-commerce', 'banking']
        for domain in tech_domains:
            if domain in description_lower:
                domain_tags.append(domain)
        
        return list(set(domain_tags))
