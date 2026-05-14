"""Daily shortlist generator for PM jobs."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.database.session import get_db_session
from app.models.job import Job
from app.repositories.job import JobRepository
from app.services.ai.title_filters import get_title_category
from app.core.logging import logger


class ShortlistGenerator:
    """Generates daily PM job shortlists."""
    
    def __init__(self):
        self.minimum_final_score = 45.0
        self.max_shortlist_size = 10
        self.max_job_age_days = 7
        
    async def generate_daily_shortlist(
        self,
        resume_path: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Generate daily PM job shortlist.
        
        Args:
            resume_path: Path to resume file for AI matching
            limit: Maximum number of jobs in shortlist
            
        Returns:
            Dict containing shortlist jobs and statistics
        """
        logger.info("Starting daily shortlist generation")
        
        # Get fresh jobs from database
        fresh_jobs = await self._get_fresh_jobs()
        
        if not fresh_jobs:
            logger.warning("No fresh jobs found for shortlist")
            return {
                "jobs": [],
                "stats": {
                    "total_jobs_analyzed": 0,
                    "jobs_filtered_out": 0,
                    "shortlist_count": 0,
                    "top_average_score": 0.0,
                    "pm_category_distribution": {},
                    "newest_job_age_days": 0
                }
            }
        
        # Run AI matching if resume provided
        if resume_path:
            await self._run_ai_matching(resume_path, fresh_jobs)
        
        # Generate shortlist
        shortlist_jobs = await self._generate_shortlist(fresh_jobs, limit)
        
        # Calculate statistics
        stats = self._calculate_stats(fresh_jobs, shortlist_jobs)
        
        logger.info(
            f"Shortlist generated: {len(shortlist_jobs)} jobs "
            f"from {len(fresh_jobs)} fresh jobs"
        )
        
        return {
            "jobs": shortlist_jobs,
            "stats": stats
        }
    
    async def _get_fresh_jobs(self) -> List[Job]:
        """Get fresh jobs from database."""
        async with get_db_session() as session:
            repo = JobRepository(session)
            
            # Get jobs posted within last 30 days (more flexible for testing)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            stmt = (
                select(Job)
                .where(Job.posted_at >= cutoff_date)
                .where(Job.final_score.isnot(None))
                .where(Job.final_score >= self.minimum_final_score)
                .order_by(desc(Job.final_score))
            )
            
            result = await session.execute(stmt)
            jobs = result.scalars().all()
            
            # Filter by PM relevance and URL validity
            fresh_jobs = []
            for job in jobs:
                if self._is_pm_relevant(job) and repo.validate_job_url(job.job_url):
                    fresh_jobs.append(job)
            
            logger.info(f"Found {len(fresh_jobs)} fresh PM jobs")
            return fresh_jobs
    
    def _is_pm_relevant(self, job: Job) -> bool:
        """Check if job is PM-relevant."""
        pm_category = get_title_category(job.title)
        return pm_category == "pm"
    
    async def _run_ai_matching(self, resume_path: str, jobs: List[Job]):
        """Run AI matching on fresh jobs."""
        try:
            from app.services.ai.matcher import MatchingEngine
            from app.services.ai.scorer import ScoringEngine
            
            matcher = MatchingEngine()
            scorer = ScoringEngine()
            
            # Parse resume
            profile = await matcher.parse_resume(resume_path)
            
            # Score jobs
            for job in jobs:
                try:
                    score_result = await scorer.score_job(job, profile)
                    
                    # Update scores in database
                    async with get_db_session() as session:
                        repo = JobRepository(session)
                        await repo.update_ai_scores(
                            job_id=job.id,
                            semantic_score=score_result.get("semantic_score"),
                            final_score=score_result.get("final_score"),
                            salary_score=score_result.get("salary_score"),
                            transition_score=score_result.get("transition_score"),
                            relevance_reason=score_result.get("relevance_reason")
                        )
                        
                except Exception as e:
                    logger.error(f"Failed to score job {job.id}: {e}")
                    
        except Exception as e:
            logger.error(f"AI matching failed: {e}")
    
    async def _generate_shortlist(self, jobs: List[Job], limit: int) -> List[Dict[str, Any]]:
        """Generate shortlist from jobs."""
        # Sort by final score descending
        sorted_jobs = sorted(jobs, key=lambda j: j.final_score or 0, reverse=True)
        
        # Take top jobs
        shortlist_jobs = sorted_jobs[:limit]
        
        # Format jobs for output
        formatted_jobs = []
        for rank, job in enumerate(shortlist_jobs, start=1):
            formatted_job = {
                "rank": rank,
                "id": str(job.id),
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "final_score": round(job.final_score or 0, 2),
                "semantic_score": round(job.semantic_score or 0, 2),
                "transition_score": round(job.transition_score or 0, 2),
                "salary_score": round(job.salary_score or 0, 2),
                "pm_category": get_title_category(job.title),
                "source": job.source,
                "posted_at": job.posted_at.isoformat() if job.posted_at else None,
                "job_url": job.job_url,
                "relevance_reason": job.relevance_reason or "No reason provided",
                "domain_tags": job.domain_tags or [],
                "salary": job.salary,
                "remote_status": job.remote_status
            }
            formatted_jobs.append(formatted_job)
        
        return formatted_jobs
    
    def _calculate_stats(self, all_jobs: List[Job], shortlist_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate shortlist statistics."""
        if not shortlist_jobs:
            return {
                "total_jobs_analyzed": len(all_jobs),
                "jobs_filtered_out": len(all_jobs),
                "shortlist_count": 0,
                "top_average_score": 0.0,
                "pm_category_distribution": {},
                "newest_job_age_days": 0
            }
        
        # Calculate average score
        total_score = sum(job["final_score"] for job in shortlist_jobs)
        avg_score = total_score / len(shortlist_jobs)
        
        # PM category distribution
        category_dist = {}
        for job in shortlist_jobs:
            category = job["pm_category"]
            category_dist[category] = category_dist.get(category, 0) + 1
        
        # Newest job age
        now = datetime.utcnow()
        newest_age = max(
            (now - datetime.fromisoformat(job["posted_at"].replace('Z', '+00:00'))).days
            for job in shortlist_jobs
            if job["posted_at"]
        )
        
        return {
            "total_jobs_analyzed": len(all_jobs),
            "jobs_filtered_out": len(all_jobs) - len(shortlist_jobs),
            "shortlist_count": len(shortlist_jobs),
            "top_average_score": round(avg_score, 2),
            "pm_category_distribution": category_dist,
            "newest_job_age_days": newest_age
        }
