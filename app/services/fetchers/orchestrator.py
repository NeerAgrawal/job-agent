"""Fetcher orchestrator for coordinating multiple job fetchers."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.fetchers.greenhouse import GreenhouseFetcher
from app.services.fetchers.lever import LeverFetcher
from app.services.fetchers.wellfound import WellfoundFetcher
from app.services.fetchers.india import InstahyreFetcher, CutshortFetcher, NaukriFetcher
from app.services.source_intelligence import (
    SourceHealthTracker,
    PMRolePreFilter,
    SourceAnalytics,
    FetchEfficiencyAnalyzer
)

# Browser automation imports (optional)
try:
    from app.services.fetchers.browser import (
        InstahyreBrowserFetcher,
        NaukriBrowserFetcher,
        CutshortBrowserFetcher,
        BrowserHealthTracker
    )
    BROWSER_FETCHERS_AVAILABLE = True
except ImportError:
    BROWSER_FETCHERS_AVAILABLE = False

from app.repositories.job import JobRepository
from app.database.session import get_db_session
from app.schemas.job import JobCreate
from app.core.logging import logger


class FetcherOrchestrator:
    """Orchestrates multiple job fetchers with source intelligence."""

    def __init__(self):
        self.logger = logger.bind(service="orchestrator")
        
        # Initialize source intelligence components
        self.health_tracker = SourceHealthTracker()
        self.prefilter = PMRolePreFilter()
        self.analytics = SourceAnalytics()
        self.efficiency_analyzer = FetchEfficiencyAnalyzer()

        # Initialize browser health tracker if available
        self.browser_health_tracker = BrowserHealthTracker() if BROWSER_FETCHERS_AVAILABLE else None

        # Primary lightweight fetchers
        self.fetchers = {
            "greenhouse": GreenhouseFetcher(
                company_boards=[
                    "stripe",
                    "airbnb",
                    "postman"
                ]
            ),
            "lever": LeverFetcher(),
            "wellfound": WellfoundFetcher(),
            "instahyre": InstahyreFetcher(),
            "cutshort": CutshortFetcher(),
            "naukri": NaukriFetcher()
        }

        # Optional browser fetchers for fallback
        self.browser_fetchers = {}
        if BROWSER_FETCHERS_AVAILABLE:
            self.browser_fetchers = {
                "instahyre_browser": InstahyreBrowserFetcher(),
                "cutshort_browser": CutshortBrowserFetcher(),
                "naukri_browser": NaukriBrowserFetcher()
            }

        # bounded concurrency
        self.semaphore = asyncio.Semaphore(3)
        self.browser_semaphore = asyncio.Semaphore(2)  # Limit browser concurrency

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
                self._safe_fetch_with_browser_fallback(
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

            saved_count = await self.save_all_jobs(all_jobs)
            
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_sources": len(self.fetchers),
                "successful_sources": len([
                    r["source"] for r in fetch_results.values()
                    if r["success"]
                ]),
                "successful_sources": len([
                    r["source"] for r in fetch_results.values()
                    if r["success"]
                ]),
                "total_jobs_fetched": len(all_jobs),
                "jobs_after_filtering": len(all_jobs),
                "unique_jobs": len(unique_jobs),
                "saved_count": saved_count,
                "source_results": fetch_results,
                "source_intelligence": self._generate_intelligence_summary()
            }

            self.logger.info(
                f"Orchestrated fetch complete "
                f"fetched={summary['total_jobs_fetched']} "
                f"saved={saved_count}"
            )

            return summary
    
    def _generate_intelligence_summary(self) -> Dict[str, Any]:
        """Generate source intelligence summary with browser metrics."""
        try:
            # Get health metrics from all sources
            health_summary = self.health_tracker.get_overall_health()
            
            # Get efficiency analysis
            source_data = {}
            for source_name, metrics in health_summary.get('source_details', {}).items():
                source_data[source_name] = {
                    'total_fetched': metrics.get('total_fetched', 0),
                    'pm_accepted': metrics.get('pm_accepted', 0),
                    'pm_rejected': metrics.get('pm_rejected', 0),
                    'pm_density': metrics.get('pm_density', '0%'),
                    'acceptance_rate': metrics.get('acceptance_rate', '0%'),
                    'quality_score': metrics.get('quality_score', '0'),
                    'avg_fetch_duration': metrics.get('avg_fetch_duration', '0s')
                }
            
            # Generate analytics report
            analytics_report = self.analytics.generate_performance_report(source_data)
            
            # Get browser health metrics if available
            browser_health = {}
            if self.browser_health_tracker:
                browser_health = self.browser_health_tracker.get_overall_health()
            
            return {
                'health_summary': health_summary,
                'efficiency_analysis': self.efficiency_analyzer.analyze_fetch_efficiency(source_data),
                'analytics_report': analytics_report,
                'browser_health': browser_health,
                'recommendations': health_summary.get('recommendations', []),
                'browser_available': BROWSER_FETCHERS_AVAILABLE,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate intelligence summary: {e}")
            return {
                'health_summary': {'status': 'error'},
                'efficiency_analysis': {'status': 'error'},
                'analytics_report': {'status': 'error'},
                'browser_health': {'status': 'error'},
                'recommendations': ['Failed to generate intelligence summary'],
                'browser_available': BROWSER_FETCHERS_AVAILABLE,
                'generated_at': datetime.utcnow().isoformat()
            }

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
        """Safely fetch jobs from a source with intelligence tracking."""
        
        # Start tracking fetch
        self.health_tracker.start_fetch(source_name)
        fetch_start_time = datetime.utcnow()
        
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
                
                # Apply pre-filtering for early rejection
                prefilter_result = self.prefilter.prefilter_jobs(jobs)
                filtered_jobs = prefilter_result['accepted']
                rejected_jobs = prefilter_result['rejected']
                
                # Record fetch metrics
                fetch_duration = (datetime.utcnow() - fetch_start_time).total_seconds()
                self.health_tracker.record_fetch_result(
                    source_name=source_name,
                    total_fetched=len(jobs),
                    pm_accepted=len(filtered_jobs),
                    pm_rejected=len(rejected_jobs),
                    duration=fetch_duration
                )
                
                return {
                    "source": source_name,
                    "success": True,
                    "jobs": filtered_jobs,
                    "count": len(filtered_jobs),
                    "prefilter_stats": prefilter_result['stats']
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
    
    async def _safe_fetch_with_browser_fallback(
        self,
        source_name: str,
        fetcher,
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Safely fetch jobs with optional browser fallback."""
        
        # Try primary lightweight fetcher first
        primary_result = await self._safe_fetch(source_name, fetcher, limit, filters)
        
        # If primary fetcher failed or returned no jobs, try browser fallback
        if (not primary_result["success"] or primary_result["count"] == 0) and BROWSER_FETCHERS_AVAILABLE:
            
            # Map source names to browser fetchers
            browser_source_map = {
                "instahyre": "instahyre_browser",
                "cutshort": "cutshort_browser", 
                "naukri": "naukri_browser"
            }
            
            browser_source_name = browser_source_map.get(source_name)
            if browser_source_name and browser_source_name in self.browser_fetchers:
                
                self.logger.info(f"Attempting browser fallback for {source_name}")
                
                # Try browser fetcher with limited concurrency
                async with self.browser_semaphore:
                    browser_result = await self._safe_browser_fetch(
                        browser_source_name,
                        self.browser_fetchers[browser_source_name],
                        limit,
                        filters
                    )
                    
                    # If browser fetch succeeded, use it
                    if browser_result["success"] and browser_result["count"] > 0:
                        self.logger.info(f"Browser fallback succeeded for {source_name}")
                        return browser_result
                    else:
                        self.logger.warning(f"Browser fallback failed for {source_name}")
        
        # Return primary result (success or failure)
        return primary_result
    
    async def _safe_browser_fetch(
        self,
        source_name: str,
        browser_fetcher,
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Safely fetch jobs using browser automation."""
        
        # Start browser session tracking
        session_id = None
        if self.browser_health_tracker:
            session_id = self.browser_health_tracker.start_browser_session(source_name)
        
        browser_start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting browser fetch from {source_name}")
            
            jobs = await asyncio.wait_for(
                browser_fetcher.fetch_jobs(
                    limit=limit,
                    filters=filters
                ),
                timeout=120  # Longer timeout for browser operations
            )
            
            # Apply pre-filtering for early rejection
            prefilter_result = self.prefilter.prefilter_jobs(jobs)
            filtered_jobs = prefilter_result['accepted']
            rejected_jobs = prefilter_result['rejected']
            
            # Record browser metrics
            browser_duration = (datetime.utcnow() - browser_start_time).total_seconds()
            if self.browser_health_tracker:
                self.browser_health_tracker.record_extraction_results(
                    source_name=source_name,
                    total_jobs=len(jobs),
                    pm_jobs=len(filtered_jobs),
                    session_duration=browser_duration
                )
            
            return {
                "source": source_name,
                "success": True,
                "jobs": filtered_jobs,
                "count": len(filtered_jobs),
                "prefilter_stats": prefilter_result['stats'],
                "browser_extracted": True,
                "browser_duration": browser_duration
            }
            
        except asyncio.TimeoutError:
            self.logger.error(f"Browser fetch timeout for {source_name}")
            if self.browser_health_tracker and session_id:
                self.browser_health_tracker.record_timeout(source_name, session_id)
            
            return {
                "source": source_name,
                "success": False,
                "jobs": [],
                "error": "browser_timeout",
                "browser_extracted": False
            }
            
        except Exception as e:
            self.logger.exception(f"Browser fetch failed for {source_name}")
            if self.browser_health_tracker and session_id:
                self.browser_health_tracker.record_browser_crash(source_name, session_id)
            
            return {
                "source": source_name,
                "success": False,
                "jobs": [],
                "error": "browser_failure",
                "browser_extracted": False
            }
            
        finally:
            # End browser session
            if self.browser_health_tracker and session_id:
                self.browser_health_tracker.end_browser_session(source_name, session_id)

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
        jobs_failed = 0

        async with get_db_session() as session:

            repo = JobRepository(session)

            for job_data in jobs:

                try:
                    existing_job = await repo.get_by_job_url(
                        job_data.job_url
                    )
                    if existing_job:
                        continue
                    
                    # Validate URL before saving
                    job_url = job_data.job_url
                    if not repo.validate_job_url(job_url):
                        self.logger.warning(f"Rejected invalid URL: {job_url}")
                        jobs_failed += 1
                        continue
                    
                    await repo.create(job_data.model_dump())
                    saved_count += 1
                    self.logger.info(f"Saved job: {job_data.title}")
                except Exception as e:
                    jobs_failed += 1
                    self.logger.exception(f"Failed to save job: {e}")

        self.logger.info(
            f"Saved jobs count={saved_count}, failed={jobs_failed}"
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