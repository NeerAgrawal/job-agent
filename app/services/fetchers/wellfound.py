"""Wellfound job fetcher implementation."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

import httpx

from app.services.fetchers.base import BaseFetcher
from app.schemas.job import JobCreate
from app.core.logging import logger


class WellfoundFetcher(BaseFetcher):
    """Wellfound job board fetcher."""

    def __init__(self):
        super().__init__("Wellfound")
        self.base_url = "https://wellfound.com/jobs"
        self.rate_limiter = asyncio.Semaphore(10)

    async def fetch_jobs(
        self,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[JobCreate]:
        """Fetch jobs from Wellfound."""

        logger.info(
            f"Starting Wellfound job fetch with limit={limit}"
        )

        try:
            jobs_data = await self._fetch_jobs_data()

            if not jobs_data:
                logger.warning("No jobs returned from Wellfound")
                return []

            normalized_jobs = []

            for job_data in jobs_data:
                normalized_job = await self.validate_job(job_data)

                if normalized_job:
                    normalized_jobs.append(normalized_job)

            filtered_jobs = self._apply_filters(
                normalized_jobs,
                filters
            )

            logger.info(
                f"Wellfound fetch completed successfully. "
                f"Fetched={len(normalized_jobs)}, "
                f"Filtered={len(filtered_jobs)}"
            )

            return filtered_jobs[:limit]

        except Exception:
            logger.exception("Wellfound fetch failed")
            return []

    async def _fetch_jobs_data(
        self
    ) -> List[Dict[str, Any]]:
        """
        Fetch job data.

        NOTE:
        Wellfound has anti-bot protections.
        This method includes lightweight mock fallback support
        for development/testing stability.
        """

        try:
            # Temporarily disabled - return empty list until real scraping is implemented
            return []

        except Exception:
            logger.exception(
                "Failed fetching Wellfound jobs"
            )
            return []

    def _apply_filters(
        self,
        jobs: List[JobCreate],
        filters: Optional[Dict[str, Any]]
    ) -> List[JobCreate]:
        """Apply optional filters."""

        if not filters:
            return jobs

        filtered_jobs = jobs

        if filters.get("search"):
            search_term = filters["search"].lower()

            filtered_jobs = [
                job for job in filtered_jobs
                if search_term in job.title.lower()
                or search_term in job.company.lower()
                or search_term in job.jd_text.lower()
            ]

        if filters.get("location"):
            location_filter = filters["location"].lower()

            filtered_jobs = [
                job for job in filtered_jobs
                if location_filter in job.location.lower()
            ]

        if filters.get("remote_status"):
            remote_filter = filters["remote_status"].lower()

            filtered_jobs = [
                job for job in filtered_jobs
                if job.remote_status.lower() == remote_filter
            ]

        return filtered_jobs

    async def validate_job(
        self,
        job_data: Dict[str, Any]
    ) -> Optional[JobCreate]:
        """Validate and normalize job."""

        try:
            description = job_data.get(
                "description",
                ""
            )

            salary = self._parse_salary(
                job_data.get("salary", {})
            )

            job_dict = {
                "title": job_data.get("title", ""),
                "company": job_data.get("company", ""),
                "location": job_data.get("location", ""),
                "salary": salary,
                "source": "Wellfound",
                "job_url": job_data.get("url", ""),
                "posted_at": self._parse_datetime(
                    job_data.get("posted_at", "")
                ),
                "jd_text": description,
                "applicant_count": job_data.get(
                    "applicant_count",
                    0
                ),
                "remote_status": self._determine_remote_status(
                    job_data
                ),
                "domain_tags": self._extract_domain_tags(
                    description
                ),
                "raw_metadata": job_data
            }

            return JobCreate(**job_dict)

        except Exception:
            logger.exception(
                "Wellfound job validation failed"
            )
            return None

    def _parse_salary(
        self,
        salary_data: Dict[str, Any]
    ) -> Optional[float]:
        """Parse salary safely."""

        if not salary_data:
            return None

        salary_str = (
            salary_data
            .get("display", "")
            .replace("$", "")
            .replace(",", "")
            .lower()
        )

        if not salary_str:
            return None

        try:
            if "-" in salary_str:
                parts = salary_str.split("-")

                min_salary = self._parse_salary_part(
                    parts[0]
                )

                return min_salary

            return self._parse_salary_part(
                salary_str
            )

        except Exception:
            logger.warning(
                f"Invalid salary format: {salary_str}"
            )
            return None

    def _parse_salary_part(
        self,
        salary_part: str
    ) -> Optional[float]:
        """Parse salary component."""

        if not salary_part:
            return None

        cleaned = (
            salary_part
            .replace("$", "")
            .replace("k", "000")
            .strip()
        )

        try:
            return float(cleaned)

        except Exception:
            return None

    def _parse_datetime(
        self,
        date_str: str
    ) -> Optional[datetime]:
        """Parse datetime safely."""

        if not date_str:
            return None

        try:
            if "T" in date_str:
                return datetime.fromisoformat(
                    date_str.replace("Z", "+00:00")
                )

            return datetime.fromisoformat(date_str)

        except Exception:
            logger.warning(
                f"Invalid datetime format: {date_str}"
            )
            return None

    def _determine_remote_status(
        self,
        job_data: Dict[str, Any]
    ) -> str:
        """Determine remote/hybrid/onsite."""

        description = (
            job_data.get("description", "")
            .lower()
        )

        location = (
            job_data.get("location", "")
            .lower()
        )

        if (
            "remote" in location
            or "remote" in description
            or "work from home" in description
        ):
            return "remote"

        if (
            "hybrid" in location
            or "hybrid" in description
        ):
            return "hybrid"

        return "onsite"

    def _extract_domain_tags(
        self,
        description: str
    ) -> List[str]:
        """Extract PM-related domain tags."""

        if not description:
            return []

        pm_domains = [
            "product",
            "saas",
            "b2b",
            "analytics",
            "technical",
            "engineering",
            "api",
            "platform",
            "ai",
            "machine learning",
            "data",
            "infrastructure",
            "devops",
            "strategy",
            "growth",
            "microservices"
        ]

        description_lower = description.lower()

        tags = []

        for domain in pm_domains:
            if domain in description_lower:
                tags.append(domain)

        return list(set(tags))