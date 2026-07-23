"""Daily shortlist generator for PM jobs."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.database.session import get_db_session
from app.models.job import Job
from app.repositories.job import JobRepository
from app.services.ai.title_filters import get_title_category
from app.core.config import settings
from app.core.logging import logger


class ShortlistGenerator:
    """Generates daily PM job shortlists."""

    def __init__(self):
        # Quality bar for "meaningful" jobs, driven by a single setting
        # (MIN_SCORE_THRESHOLD) so it can be tuned without code changes.
        self.minimum_final_score = settings.min_score_threshold
        self.max_shortlist_size = 100
        self.max_job_age_days = 7

    async def generate_daily_shortlist(
        self,
        resume_path: Optional[str] = None,
        limit: int = 100
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
            
            # Filter by PM relevance, URL validity, and recruiter-repost quality.
            # The repost check runs here too (not just at fetch time) so reposts
            # already saved from earlier runs are still kept out of delivery.
            from app.services.source_intelligence.quality_filter import is_recruiter_repost

            fresh_jobs = []
            for job in jobs:
                if not (self._is_pm_relevant(job) and repo.validate_job_url(job.job_url)):
                    continue
                is_repost, _ = is_recruiter_repost(job.company, job.jd_text)
                if is_repost:
                    continue
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
            from app.services.ai.resume_parser import ResumeParser
            from app.services.ai.profile_builder import ProfileBuilder
            from app.services.ai.embeddings import EmbeddingsEngine
            from app.services.ai.scorer import ScoringEngine

            # Parse resume and build a candidate profile
            resume_data = await ResumeParser().parse_resume(resume_path)
            if not resume_data:
                logger.error(f"Failed to parse resume at {resume_path}")
                return

            profile_obj = await ProfileBuilder().build_profile(resume_data)
            resume_profile = {
                "target_roles": profile_obj.target_roles,
                "qa_background": resume_data.get("qa_background", False),
                "technical_strength": profile_obj.technical_strength,
                "preferred_locations": profile_obj.preferred_locations,
                "salary_preferences": profile_obj.salary_preferences,
            }

            embeddings_engine = EmbeddingsEngine()
            await embeddings_engine.initialize()
            resume_embedding = await embeddings_engine.embed_resume(resume_data.get("raw_text", ""))

            job_texts = [job.jd_text or f"{job.title} at {job.company}" for job in jobs]
            job_embeddings = await embeddings_engine.embed_jobs_batch(job_texts)

            scorer = ScoringEngine()

            # Score jobs
            for idx, job in enumerate(jobs):
                try:
                    semantic_similarity = 0.5
                    if resume_embedding is not None and job_embeddings and idx < len(job_embeddings) and job_embeddings[idx] is not None:
                        semantic_similarity = await embeddings_engine.cosine_similarity(resume_embedding, job_embeddings[idx])

                    score_result = await scorer.score_job(job, resume_profile, semantic_similarity)
                    if not score_result:
                        continue

                    scores_dict = {
                        "semantic": score_result.semantic_score,
                        "final": score_result.final_score,
                        "salary": score_result.salary_score,
                        "transition": score_result.qa_to_pm_score,
                    }

                    # Update scores in database
                    async with get_db_session() as session:
                        repo = JobRepository(session)
                        await repo.update_ai_scores(job.id, scores_dict, score_result.relevance_reason)

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
