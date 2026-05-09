"""Job cleanup service for maintaining database quality."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.session import get_db_session
from app.models.job import Job
from app.repositories.job import JobRepository
from app.core.logging import logger


class JobCleanup:
    """Cleans up stale and low-quality jobs from database."""
    
    def __init__(self):
        self.max_job_age_days = 30
        self.minimum_quality_score = 40.0
        
    async def cleanup_stale_jobs(self) -> Dict[str, Any]:
        """Remove stale and low-quality jobs from database.
        
        Returns:
            Dict with cleanup statistics
        """
        logger.info("Starting job cleanup process")
        
        stats = {
            "total_jobs_before": 0,
            "stale_jobs_removed": 0,
            "invalid_urls_removed": 0,
            "low_quality_removed": 0,
            "duplicate_urls_removed": 0,
            "total_jobs_after": 0,
            "cleanup_timestamp": datetime.utcnow().isoformat()
        }
        
        async with get_db_session() as session:
            repo = JobRepository(session)
            
            # Count total jobs before cleanup
            total_stmt = select(Job)
            total_result = await session.execute(total_stmt)
            stats["total_jobs_before"] = len(total_result.scalars().all())
            
            # Remove stale jobs (older than 30 days)
            await self._remove_stale_jobs(session, stats)
            
            # Remove jobs with invalid URLs
            await self._remove_invalid_urls(session, stats)
            
            # Remove low-quality jobs
            await self._remove_low_quality_jobs(session, stats)
            
            # Remove duplicate URLs
            await self._remove_duplicate_urls(session, stats)
            
            # Count total jobs after cleanup
            total_result_after = await session.execute(total_stmt)
            stats["total_jobs_after"] = len(total_result_after.scalars().all())
            
            await session.commit()
        
        logger.info(
            f"Cleanup completed: removed {stats['stale_jobs_removed'] + stats['invalid_urls_removed'] + stats['low_quality_removed'] + stats['duplicate_urls_removed']} jobs"
        )
        
        return stats
    
    async def _remove_stale_jobs(self, session: AsyncSession, stats: Dict[str, Any]):
        """Remove jobs older than max age."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.max_job_age_days)
        
        stmt = delete(Job).where(Job.posted_at < cutoff_date)
        result = await session.execute(stmt)
        stats["stale_jobs_removed"] = result.rowcount
        
        if stats["stale_jobs_removed"] > 0:
            logger.info(f"Removed {stats['stale_jobs_removed']} stale jobs")
    
    async def _remove_invalid_urls(self, session: AsyncSession, stats: Dict[str, Any]):
        """Remove jobs with invalid URLs."""
        repo = JobRepository(session)
        
        # Get all jobs
        stmt = select(Job)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        invalid_count = 0
        for job in jobs:
            if not repo.validate_job_url(job.job_url):
                await session.delete(job)
                invalid_count += 1
        
        stats["invalid_urls_removed"] = invalid_count
        
        if invalid_count > 0:
            logger.info(f"Removed {invalid_count} jobs with invalid URLs")
    
    async def _remove_low_quality_jobs(self, session: AsyncSession, stats: Dict[str, Any]):
        """Remove jobs below minimum quality score."""
        stmt = delete(Job).where(
            (Job.final_score < self.minimum_quality_score) |
            (Job.final_score.is_(None))
        )
        result = await session.execute(stmt)
        stats["low_quality_removed"] = result.rowcount
        
        if stats["low_quality_removed"] > 0:
            logger.info(f"Removed {stats['low_quality_removed']} low-quality jobs")
    
    async def _remove_duplicate_urls(self, session: AsyncSession, stats: Dict[str, Any]):
        """Remove duplicate job URLs, keeping the highest scored one."""
        # Get all jobs ordered by score descending
        stmt = select(Job).order_by(Job.final_score.desc().nulls_last())
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        seen_urls = set()
        duplicate_count = 0
        
        for job in jobs:
            if job.job_url in seen_urls:
                await session.delete(job)
                duplicate_count += 1
            else:
                seen_urls.add(job.job_url)
        
        stats["duplicate_urls_removed"] = duplicate_count
        
        if duplicate_count > 0:
            logger.info(f"Removed {duplicate_count} duplicate URLs")
    
    async def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get current database statistics for cleanup planning."""
        async with get_db_session() as session:
            repo = JobRepository(session)
            
            stats = {
                "total_jobs": 0,
                "jobs_with_scores": 0,
                "jobs_above_threshold": 0,
                "jobs_below_threshold": 0,
                "stale_jobs_count": 0,
                "invalid_urls_count": 0,
                "duplicate_urls_estimate": 0,
                "oldest_job_days": 0,
                "newest_job_days": 0
            }
            
            # Total jobs
            total_stmt = select(Job)
            total_result = await session.execute(total_stmt)
            stats["total_jobs"] = len(total_result.scalars().all())
            
            # Jobs with scores
            scored_stmt = select(Job).where(Job.final_score.isnot(None))
            scored_result = await session.execute(scored_stmt)
            stats["jobs_with_scores"] = len(scored_result.scalars().all())
            
            # Jobs above/below threshold
            above_stmt = select(Job).where(Job.final_score >= self.minimum_quality_score)
            above_result = await session.execute(above_stmt)
            stats["jobs_above_threshold"] = len(above_result.scalars().all())
            
            below_stmt = select(Job).where(
                (Job.final_score < self.minimum_quality_score) |
                (Job.final_score.is_(None))
            )
            below_result = await session.execute(below_stmt)
            stats["jobs_below_threshold"] = len(below_result.scalars().all())
            
            # Stale jobs
            cutoff_date = datetime.utcnow() - timedelta(days=self.max_job_age_days)
            stale_stmt = select(Job).where(Job.posted_at < cutoff_date)
            stale_result = await session.execute(stale_stmt)
            stats["stale_jobs_count"] = len(stale_result.scalars().all())
            
            # Invalid URLs
            all_jobs = total_result.scalars().all()
            invalid_count = 0
            for job in all_jobs:
                if not repo.validate_job_url(job.job_url):
                    invalid_count += 1
            stats["invalid_urls_count"] = invalid_count
            
            # Duplicate URLs estimate
            urls = [job.job_url for job in all_jobs if job.job_url]
            unique_urls = set(urls)
            stats["duplicate_urls_estimate"] = len(urls) - len(unique_urls)
            
            # Age statistics
            if all_jobs:
                posted_dates = [job.posted_at for job in all_jobs if job.posted_at]
                if posted_dates:
                    now = datetime.utcnow()
                    oldest = min(posted_dates)
                    newest = max(posted_dates)
                    stats["oldest_job_days"] = (now - oldest).days
                    stats["newest_job_days"] = (now - newest).days
        
        return stats
