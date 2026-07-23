"""Lever job fetcher implementation."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

import httpx

from app.services.fetchers.base import BaseFetcher
from app.schemas.job import JobCreate
from app.core.logging import logger
from app.services.ai.title_filters import is_pm_role, is_reject_role


class LeverFetcher(BaseFetcher):
    """Lever job board fetcher."""

    def __init__(self, company_boards: Optional[List[str]] = None):
        super().__init__("Lever")
        self.base_url = "https://api.lever.co/v0/postings"
        self.company_boards = company_boards or ["spotify"]
        self.rate_limiter = asyncio.Semaphore(10)

    async def fetch_jobs(
        self,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[JobCreate]:
        """Fetch jobs from Lever."""

        logger.info(f"Starting Lever job fetch with limit={limit}")

        try:
            postings = await self._get_all_postings()

            if not postings:
                logger.warning("No Lever postings found")
                return []

            jobs = []

            for posting in postings:
                normalized_job = await self.validate_job(posting)

                if normalized_job:
                    jobs.append(normalized_job)
                else:
                    logger.warning("Skipping invalid Lever job")

            filtered_jobs = self._apply_filters(jobs, filters)

            logger.info(
                f"Lever fetch completed successfully. "
                f"Fetched={len(jobs)}, Filtered={len(filtered_jobs)}"
            )

            return filtered_jobs[:limit]

        except Exception:
            logger.exception("Lever fetch failed")
            return []

    async def _get_all_postings(self) -> List[Dict[str, Any]]:
        """Fetch postings from multiple Lever companies."""

        all_postings = []

        for company in self.company_boards:
            try:
                postings = await self._fetch_company_postings(company)

                if postings:
                    all_postings.extend(postings)

            except Exception:
                logger.exception(
                    f"Failed fetching Lever postings for company={company}"
                )

        return all_postings

    async def _fetch_company_postings(
        self,
        company: str
    ) -> List[Dict[str, Any]]:
        """Fetch postings for a specific company."""

        url = f"{self.base_url}/{company}?mode=json"

        headers = {
            "User-Agent": "JobAI-Agent/1.0",
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                async with self.rate_limiter:

                    response = await client.get(
                        url,
                        headers=headers
                    )

                    if response.status_code != 200:
                        logger.warning(
                            f"Lever request failed "
                            f"company={company} "
                            f"status={response.status_code}"
                        )
                        return []

                    data = response.json()

                    if isinstance(data, list):
                        return data

                    return []

        except httpx.TimeoutException:
            logger.warning(
                f"Lever timeout for company={company}"
            )
            return []

        except Exception:
            logger.exception(
                f"Lever request failed for company={company}"
            )
            return []

    def _apply_filters(
        self,
        jobs: List[JobCreate],
        filters: Optional[Dict[str, Any]]
    ) -> List[JobCreate]:
        """Apply optional filters with PM-only filtering."""

        if not filters:
            # Apply PM-only filtering by default
            filtered_jobs = []
            for job in jobs:
                if is_pm_role(job.title) and not is_reject_role(job.title):
                    filtered_jobs.append(job)
            return filtered_jobs

        filtered_jobs = jobs
        
        # Apply PM-only filtering first
        pm_filtered_jobs = []
        for job in filtered_jobs:
            if is_pm_role(job.title) and not is_reject_role(job.title):
                pm_filtered_jobs.append(job)
        
        filtered_jobs = pm_filtered_jobs

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
        """Validate and normalize Lever job."""

        try:
            title = job_data.get("text", "").strip()

            categories = job_data.get("categories", {})

            location = categories.get("location", "")

            company = self._extract_company_from_url(
                job_data.get("applyUrl", "")
            )

            description = job_data.get("description", "")

            salary = self._parse_salary_from_text(description)

            job_dict = {
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "source": "Lever",
                "job_url": job_data.get("applyUrl", ""),
                "posted_at": self._parse_datetime(
                    job_data.get("createdAt", "")
                ),
                "jd_text": description,
                "applicant_count": 0,
                "remote_status": self._determine_remote_status(job_data),
                "domain_tags": self._extract_domain_tags(description),
                "raw_metadata": job_data
            }

            return JobCreate(**job_dict)

        except Exception:
            logger.exception("Lever job validation failed")
            return None

    def _extract_company_from_url(
        self,
        apply_url: str
    ) -> str:
        """Extract company name from Lever apply URL."""

        if not apply_url:
            return ""

        parsed = urlparse(apply_url)

        path_parts = parsed.path.split("/")

        for part in path_parts:
            if (
                part
                and part != "postings"
                and len(part) > 2
            ):
                return part.replace("-", " ").title()

        return ""

    def _parse_salary_from_text(
        self,
        description: str
    ) -> Optional[float]:
        """Extract salary from job description."""

        if not description:
            return None

        import re

        salary_pattern = (
            r"\$(\d+(?:,\d{3})*)"
            r"\s*[-–—]\s*"
            r"\$(\d+(?:,\d{3})*)"
        )

        match = re.search(
            salary_pattern,
            description.lower()
        )

        if not match:
            return None

        try:
            min_salary = float(
                match.group(1).replace(",", "")
            )

            return min_salary

        except ValueError:
            return None

    def _parse_datetime(
    self,
    date_input
    ) -> Optional[datetime]:
        """Parse datetime safely."""

        if not date_input:
            return None

        try:
            # epoch milliseconds
            if isinstance(date_input, int):

                return datetime.fromtimestamp(
                    date_input / 1000
                )

            # numeric string epoch
            if (
                isinstance(date_input, str)
                and date_input.isdigit()
            ):

                return datetime.fromtimestamp(
                    int(date_input) / 1000
                )

            # ISO format
            if (
                isinstance(date_input, str)
                and date_input.endswith("Z")
            ):

                return datetime.fromisoformat(
                    date_input.replace(
                        "Z",
                        "+00:00"
                    )
                )

            return datetime.fromisoformat(
                str(date_input)
            )

        except Exception:

            logger.warning(
                f"Invalid datetime format: "
                f"{date_input}"
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

        categories = job_data.get("categories", {})

        location = (
            categories.get("location", "")
            .lower()
        )

        if (
            "remote" in location
            or "work from home" in description
            or "remote-friendly" in description
        ):
            return "remote"

        if (
            "hybrid" in location
            or "hybrid-friendly" in description
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