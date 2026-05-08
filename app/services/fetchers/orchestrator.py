"""Fetcher orchestrator for coordinating multiple job fetchers."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.fetchers.base import BaseFetcher
from app.services.fetchers.greenhouse import GreenhouseFetcher
from app.services.fetchers.lever import LeverFetcher
from app.services.fetchers.wellfound import WellfoundFetcher
from app.database.repositories import JobRepository
from app.database.session import get_db_session
from app.core.logging import logger


class FetcherOrchestrator:
    """Orchestrates multiple job fetchers."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FetcherOrchestrator")
        self.fetchers = {
            "greenhouse": GreenhouseFetcher(),
            "lever": LeverFetcher(),
            "wellfound": WellfoundFetcher()
        }
        
    async def fetch_all_jobs(
        self,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from all available sources."""
        self.logger.info("Starting orchestrated job fetch from all sources")
        
        try:
            # Create tasks for all fetchers
            tasks = []
            for source_name, fetcher in self.fetchers.items():
                if filters and filters.get("sources") and source_name not in filters["sources"]:
                    continue  # Skip filtered sources
                
                task = asyncio.create_task(
                    fetcher.fetch_jobs(limit=limit, filters=filters, **kwargs)
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all results
            all_jobs = []
            for result in results:
                if isinstance(result, list):
                    all_jobs.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Fetcher {result} failed: {result}")
                else:
                    self.logger.warning(f"Unexpected result from fetcher: {result}")
            
            # Remove duplicates and apply final filters
            unique_jobs = self._remove_duplicates(all_jobs)
            filtered_jobs = self._apply_final_filters(unique_jobs, filters)
            
            # Limit results
            limited_jobs = filtered_jobs[:limit]
            
            self.logger.info(f"Orchestrated fetch complete: {len(limited_jobs)} jobs from {len([r for r in results if isinstance(r, list)])} sources")
            
            return limited_jobs
            
        except Exception as e:
            self.logger.error(f"Orchestrated fetch failed: {e}")
            return []
    
    async def fetch_from_source(
        self,
        source: str,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from a specific source."""
        self.logger.info(f"Starting fetch from source: {source}")
        
        if source not in self.fetchers:
            self.logger.error(f"Unknown source: {source}")
            return []
        
        fetcher = self.fetchers[source]
        return await fetcher.fetch_jobs(limit=limit, filters=filters, **kwargs)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get combined statistics from all fetchers."""
        self.logger.info("Getting combined fetch statistics")
        
        stats = {
            "total_sources": len(self.fetchers),
            "active_fetchers": [],
            "last_fetch": datetime.utcnow().isoformat(),
            "source_stats": {}
        }
        
        for source_name, fetcher in self.fetchers.items():
            try:
                source_stats = await fetcher.get_fetch_statistics()
                stats["source_stats"][source_name] = source_stats
                stats["active_fetchers"].append(source_name)
            except Exception as e:
                self.logger.error(f"Failed to get stats for {source_name}: {e}")
                stats["source_stats"][source_name] = {"error": str(e)}
        
        return stats
    
    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on title, company, and job_url."""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create unique identifier
            identifier = (
                job.get("title", "").lower().strip(),
                job.get("company", "").lower().strip(),
                job.get("job_url", "").strip()
            )
            
            if identifier not in seen:
                seen.add(identifier)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _apply_final_filters(self, jobs: List[Dict[str, Any]], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply final filters after deduplication."""
        if not filters:
            return jobs
        
        filtered_jobs = jobs
        
        # Posted within 24 hours filter
        if filters.get("posted_within_24h"):
            cutoff = datetime.utcnow() - timedelta(hours=24)
            filtered_jobs = [
                job for job in filtered_jobs
                if job.get("posted_at") and job.get("posted_at") >= cutoff
            ]
        
        # PM roles filter
        if filters.get("pm_roles_only"):
            pm_titles = [
                "product manager", "associate product manager", "technical product manager",
                "ai product manager", "platform product manager", "api product manager",
                "junior product manager", "apm", "product owner"
            ]
            
            filtered_jobs = [
                job for job in filtered_jobs
                if any(title in job.get("title", "").lower() for title in pm_titles)
            ]
        
        # Location filter
        if filters.get("locations"):
            allowed_locations = [loc.lower() for loc in filters["locations"]]
            filtered_jobs = [
                job for job in filtered_jobs
                if job.get("location", "").lower() in allowed_locations
            ]
        
        return filtered_jobs
    
    async def save_all_jobs(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Save jobs from all sources to database."""
        self.logger.info(f"Saving {len(jobs)} orchestrated jobs to database")
        
        from app.database.repositories import JobRepository
        from app.schemas.job import JobCreate
        
        await self._ensure_session()
        job_repo = JobRepository(self.session)
        
        saved_count = 0
        for job_data in jobs:
            try:
                job_create = JobCreate(**job_data)
                job = await job_repo.create(job_create.dict())
                saved_count += 1
                self.logger.debug(f"Saved job: {job.get('title')}")
            except Exception as e:
                self.logger.error(f"Failed to save job: {e}")
        
        self.logger.info(f"Successfully saved {saved_count} jobs to database")
        return {"saved_count": saved_count, "total_jobs": len(jobs)}
    
    async def _ensure_session(self):
        """Ensure database session is available."""
        if not hasattr(self, 'session') or not self.session:
            self.session = await get_db_session()
