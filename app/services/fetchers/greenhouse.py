"""Greenhouse job fetcher implementation."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

import httpx

from app.services.fetchers.base import BaseFetcher
from app.schemas.job import JobCreate
from app.core.logging import logger


class GreenhouseFetcher(BaseFetcher):
    """Greenhouse job board fetcher."""

    def __init__(
        self,
        company_boards: Optional[List[str]] = None
    ):
        super().__init__("Greenhouse")

        self.base_url = (
            "https://boards-api.greenhouse.io/v1"
        )

        self.company_boards = company_boards or [
            "stripe",
            "airbnb",
            "postman"
        ]

        self.rate_limiter = asyncio.Semaphore(10)

    async def fetch_jobs(
        self,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0
    ) -> List[JobCreate]:
        """Fetch jobs from Greenhouse."""

        logger.info(
            f"Starting Greenhouse fetch "
            f"limit={limit}"
        )

        try:
            all_jobs = []

            for company in self.company_boards:

                try:
                    company_jobs = await self._fetch_company_jobs(
                        company=company,
                        limit=limit,
                        offset=offset
                    )

                    if company_jobs:
                        all_jobs.extend(company_jobs)

                        logger.info(
                            f"Fetched {len(company_jobs)} "
                            f"jobs from company={company}"
                        )

                except Exception:
                    logger.exception(
                        f"Greenhouse company fetch failed "
                        f"company={company}"
                    )

            filtered_jobs = self._apply_filters(
                all_jobs,
                filters
            )

            logger.info(
                f"Greenhouse fetch completed "
                f"fetched={len(all_jobs)} "
                f"filtered={len(filtered_jobs)}"
            )

            return filtered_jobs[:limit]

        except Exception:
            logger.exception(
                "Greenhouse fetch failed"
            )

            return []

    async def _fetch_company_jobs(
        self,
        company: str,
        limit: int,
        offset: int
    ) -> List[JobCreate]:
        """Fetch jobs for a single company board."""

        url = (
            f"{self.base_url}/boards/"
            f"{company}/jobs"
        )

        params = {
            "limit": min(limit, 100),
            "offset": offset,
            "content": "true"
        }

        headers = {
            "User-Agent": "JobAI-Agent/1.0",
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(
                timeout=30
            ) as client:

                async with self.rate_limiter:

                    response = await client.get(
                        url,
                        params=params,
                        headers=headers
                    )

                    if response.status_code == 404:

                        logger.warning(
                            f"Greenhouse board not found "
                            f"company={company}"
                        )

                        return []

                    response.raise_for_status()

                    data = response.json()

                    jobs_data = data.get(
                        "jobs",
                        []
                    )

                    normalized_jobs = []

                    for raw_job in jobs_data:

                        normalized = await self.validate_job(
                            raw_job
                        )

                        if normalized:
                            normalized_jobs.append(
                                normalized
                            )

                    return normalized_jobs

        except httpx.TimeoutException:

            logger.warning(
                f"Greenhouse timeout "
                f"company={company}"
            )

            return []

        except Exception:

            logger.exception(
                f"Greenhouse request failed "
                f"company={company}"
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

        # Search filter
        if filters.get("search"):

            search_term = (
                filters["search"]
                .lower()
            )

            filtered_jobs = [
                job for job in filtered_jobs
                if (
                    search_term in job.title.lower()
                    or search_term in job.company.lower()
                    or search_term in job.jd_text.lower()
                )
            ]

        # Location filter
        if filters.get("location"):

            location_filter = (
                filters["location"]
                .lower()
            )

            filtered_jobs = [
                job for job in filtered_jobs
                if location_filter in job.location.lower()
            ]

        # Remote filter
        if filters.get("remote_status"):

            remote_filter = (
                filters["remote_status"]
                .lower()
            )

            filtered_jobs = [
                job for job in filtered_jobs
                if job.remote_status.lower()
                == remote_filter
            ]

        return filtered_jobs

    async def validate_job(
        self,
        job_data: Dict[str, Any]
    ) -> Optional[JobCreate]:
        """Validate and normalize Greenhouse job."""

        try:
            location_data = job_data.get(
                "location",
                {}
            )

            if isinstance(location_data, dict):
                location = location_data.get(
                    "name",
                    ""
                )
            else:
                location = str(location_data)

            metadata = job_data.get(
                "metadata",
                []
            )

            description = (
                job_data.get("content", "")
                or job_data.get("description", "")
                or ""
            )

            compensation = (
                self._extract_compensation(
                    metadata
                )
            )

            job_dict = {
                "title": job_data.get(
                    "title",
                    ""
                ),
                "company": job_data.get(
                    "company_name",
                    ""
                ),
                "location": location,
                "salary": compensation,
                "source": "Greenhouse",
                "job_url": job_data.get(
                    "absolute_url",
                    ""
                ),
                "posted_at": self._parse_datetime(
                    job_data.get(
                        "updated_at",
                        ""
                    )
                ),
                "jd_text": description,
                "applicant_count": 0,
                "remote_status": (
                    self._determine_remote_status(
                        location,
                        description
                    )
                ),
                "domain_tags": (
                    self._extract_domain_tags(
                        description
                    )
                ),
                "raw_metadata": job_data
            }

            return JobCreate(**job_dict)

        except Exception:

            logger.exception(
                "Greenhouse job validation failed"
            )

            return None

    def _extract_compensation(
    self,
    metadata: List[Dict[str, Any]]
    ) -> Optional[float]:
        """Extract compensation safely."""

        if not metadata:
            return None

        import re

        for item in metadata:

            try:
                raw_name = item.get("name", "")
                raw_value = item.get("value", "")

                name = str(raw_name).lower()
                value = str(raw_value).lower()

                if (
                    "salary" in name
                    or "compensation" in name
                    or "pay" in name
                ):

                    matches = re.findall(
                        r"\d+(?:,\d+)?",
                        value
                    )

                    if matches:

                        amount = float(
                            matches[0].replace(",", "")
                        )

                        if amount < 1000:
                            amount *= 1000

                        return amount

            except Exception as e:

                logger.warning(
                    f"Compensation parsing failed: {e}"
                )

                continue

        return None

    def _parse_datetime(
        self,
        date_str: str
    ) -> Optional[datetime]:
        """Parse datetime safely."""

        if not date_str:
            return None

        try:
            if date_str.endswith("Z"):

                return datetime.fromisoformat(
                    date_str.replace(
                        "Z",
                        "+00:00"
                    )
                )

            return datetime.fromisoformat(
                date_str
            )

        except Exception:

            logger.warning(
                f"Invalid datetime "
                f"format={date_str}"
            )

            return None

    def _determine_remote_status(
        self,
        location: str,
        description: str
    ) -> str:
        """Determine remote/hybrid/onsite."""

        location_lower = location.lower()
        description_lower = description.lower()

        if (
            "remote" in location_lower
            or "remote" in description_lower
            or "work from home"
            in description_lower
        ):
            return "remote"

        if (
            "hybrid" in location_lower
            or "hybrid" in description_lower
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

        self.company_boards = [
            # High-quality PM-focused companies with strong technical products
            "stripe",
            "postman",
            "datadog",
            "plaid",
            "mongodb",
            "mixpanel",
            "atlassian",
            "segment",
            "cloudflare",
            "vercel",
            "webflow",
            "figma",
            "zapier",
            # Removed: notion (broken board), openai (broken board)
            # Removed: airbnb, discord, coinbase, olark, reddit, robinhood
            # Removed: block, nubank, mercury, affirm, brex, ramp, deel
            # Removed: gusto, justworks, rippling, benchling (non-PM focused)
        ]

        description_lower = (
            description.lower()
        )

        tags = []

        for domain in pm_domains:

            if domain in description_lower:
                tags.append(domain)

        return list(set(tags))