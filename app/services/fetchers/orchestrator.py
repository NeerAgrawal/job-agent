"""Fetcher orchestrator for coordinating multiple job fetchers."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.fetchers.greenhouse import GreenhouseFetcher
from app.services.fetchers.lever import LeverFetcher
from app.services.fetchers.wellfound import WellfoundFetcher

from app.repositories.job import JobRepository
from app.database.session import get_db_session
from app.schemas.job import JobCreate
from app.core.logging import logger


class FetcherOrchestrator:
    """Orchestrates multiple job fetchers."""

    def __init__(self):
        self.logger = logger.bind(service="orchestrator")

        self.fetchers = {
            "greenhouse": GreenhouseFetcher(
                company_boards=[
                    "stripe",
                    "airbnb",
                    "notion",
                    "openai"
                ]
            ),
            "lever": LeverFetcher(),
            "wellfound": WellfoundFetcher()
        }

        # bounded concurrency
        self.semaphore = asyncio.Semaphore(3)

    async def fetch_from_all_sources(
        self,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch jobs from all configured sources."""

        self.logger.info(
            f"Starting orchestrated fetch "
            f"limit={limit}"
        )

        try:
            tasks = [
                self._safe_fetch(
                    source_name,
                    fetcher,
                    limit,
                    filters
                )
                for source_name, fetcher
                in self.fetchers.items()
            ]

            results = await asyncio.gather(
                *tasks,
                return_exceptions=False
            )

            all_jobs = []
            fetch_results = {}

            for result in results:
                source_name = result["source"]

                fetch_results[source_name] = {
                    "success": result["success"],
                    "count": len(result["jobs"]),
                    "error": result.get("error")
                }

                if result["success"]:
                    all_jobs.extend(result["jobs"])

            filtered_jobs = self._filter_jobs(
                all_jobs,
                filters
            )

            unique_jobs = self._deduplicate_jobs(
                filtered_jobs
            )

            saved_count = await self.save_all_jobs(
                unique_jobs
            )

            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_sources": len(self.fetchers),
                "successful_sources": len([
                    r for r in fetch_results.values()
                    if r["success"]
                ]),
                "failed_sources": len([
                    r for r in fetch_results.values()
                    if not r["success"]
                ]),
                "total_jobs_fetched": len(all_jobs),
                "jobs_after_filtering": len(filtered_jobs),
                "unique_jobs": len(unique_jobs),
                "jobs_saved": saved_count,
                "source_results": fetch_results
            }

            self.logger.info(
                f"Orchestrated fetch complete "
                f"fetched={summary['total_jobs_fetched']} "
                f"saved={saved_count}"
            )

            return summary

        except Exception:
            self.logger.exception(
                "Orchestrated fetch failed"
            )

            return {
                "success": False,
                "error": "orchestrator_failure"
            }

    async def _safe_fetch(
        self,
        source_name: str,
        fetcher,
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Safely fetch jobs from a source."""

        async with self.semaphore:

            try:
                self.logger.info(
                    f"Fetching from source={source_name}"
                )

                jobs = await asyncio.wait_for(
                    fetcher.fetch_jobs(
                        limit=limit,
                        filters=filters
                    ),
                    timeout=60
                )

                self.logger.info(
                    f"Fetch success source={source_name} "
                    f"count={len(jobs)}"
                )

                return {
                    "source": source_name,
                    "success": True,
                    "jobs": jobs
                }

            except asyncio.TimeoutError:
                self.logger.error(
                    f"Fetch timeout source={source_name}"
                )

                return {
                    "source": source_name,
                    "success": False,
                    "jobs": [],
                    "error": "timeout"
                }

            except Exception:
                self.logger.exception(
                    f"Fetch failed source={source_name}"
                )

                return {
                    "source": source_name,
                    "success": False,
                    "jobs": [],
                    "error": "fetch_failure"
                }

    async def fetch_from_source(
        self,
        source: str,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch from a single source."""

        if source not in self.fetchers:
            self.logger.error(
                f"Unknown source={source}"
            )
            return []

        try:
            fetcher = self.fetchers[source]

            jobs = await fetcher.fetch_jobs(
                limit=limit,
                filters=filters,
                **kwargs
            )

            return jobs

        except Exception:
            self.logger.exception(
                f"Single source fetch failed "
                f"source={source}"
            )

            return []

    def _filter_jobs(
        self,
        jobs: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter jobs safely."""

        if not filters:
            return jobs

        filtered_jobs = jobs

        # PM role filtering
        if filters.get("pm_roles"):

            pm_roles = [
                role.lower()
                for role in filters["pm_roles"]
            ]

            filtered_jobs = [
                job for job in filtered_jobs
                if any(
                    role in job.title.lower()
                    for role in pm_roles
                )
            ]

            self.logger.info(
                f"PM role filtering returned "
                f"{len(filtered_jobs)} jobs"
            )

        # Location filtering
        if filters.get("locations"):

            allowed_locations = [
                loc.lower()
                for loc in filters["locations"]
            ]

            filtered_jobs = [
                job for job in filtered_jobs
                if any(
                    loc in job.location.lower()
                    for loc in allowed_locations
                )
            ]

            self.logger.info(
                f"Location filtering returned "
                f"{len(filtered_jobs)} jobs"
            )

        # Search filtering
        if filters.get("search"):

            search_term = filters["search"].lower()

            filtered_jobs = [
                job for job in filtered_jobs
                if (
                    search_term in job.title.lower()
                    or search_term in job.company.lower()
                    or search_term in job.jd_text.lower()
                )
            ]

            self.logger.info(
                f"Search filtering returned "
                f"{len(filtered_jobs)} jobs"
            )

        return filtered_jobs

    def _deduplicate_jobs(
        self,
        jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate jobs."""

        seen = set()
        unique_jobs = []

        for job in jobs:

            identifier = (
                job.title.lower(),
                job.company.lower(),
                job.job_url
            )

            if identifier not in seen:
                seen.add(identifier)
                unique_jobs.append(job)

        self.logger.info(
            f"Deduplication reduced "
            f"{len(jobs)} -> {len(unique_jobs)}"
        )

        return unique_jobs

    async def save_all_jobs(
        self,
        jobs: List[JobCreate]
    ) -> int:
        """Persist jobs safely."""

        if not jobs:
            return 0

        saved_count = 0

        async with get_db_session() as session:

            repo = JobRepository(session)

            for job in jobs:

                try:
                    existing_job = await repo.get_by_job_url(
                        job.job_url
                    )

                    if existing_job:
                        self.logger.debug(
                            f"Duplicate skipped "
                            f"url={job.job_url}"
                        )
                        continue

                    await repo.create(
                        job.model_dump()
                    )

                    saved_count += 1

                except Exception:
                    self.logger.exception(
                        f"Failed saving job "
                        f"title={job.title}"
                    )

        self.logger.info(
            f"Saved jobs count={saved_count}"
        )

        return saved_count

    async def get_statistics(
        self
    ) -> Dict[str, Any]:
        """Return orchestrator statistics."""

        try:
            async with get_db_session() as session:

                repo = JobRepository(session)

                total_jobs = await repo.count()

                recent_jobs = await repo.get_recent_jobs(
                    days=7
                )

                return {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_sources": len(self.fetchers),
                    "total_jobs": total_jobs,
                    "recent_jobs": len(recent_jobs),
                    "active_fetchers": list(
                        self.fetchers.keys()
                    )
                }

        except Exception:
            self.logger.exception(
                "Failed retrieving orchestrator statistics"
            )

            return {
                "error": "statistics_failure"
            }