"""Job repository with job-specific operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.sql import func

from app.models import Job
from app.core.logging import logger
from .base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Repository for job data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Job, session)
    
    async def get_by_company(self, company: str, limit: int = 50) -> List[Job]:
        """Get jobs by company name."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.company.ilike(f"%{company}%"))
                .order_by(desc(self.model.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by company {company}: {e}")
            return []
    
    async def get_by_location(self, location: str, limit: int = 50) -> List[Job]:
        """Get jobs by location."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.location.ilike(f"%{location}%"))
                .order_by(desc(self.model.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by location {location}: {e}")
            return []
    
    async def get_by_source(self, source: str, limit: int = 50) -> List[Job]:
        """Get jobs by source."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.source == source)
                .order_by(desc(self.model.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by source {source}: {e}")
            return []
    
    async def get_by_match_score(self, min_score: float = 0.0, max_score: float = 100.0, limit: int = 50) -> List[Job]:
        """Get jobs by match score range."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(and_(
                    self.model.match_score >= min_score,
                    self.model.match_score <= max_score,
                    self.model.match_score.isnot(None)
                ))
                .order_by(desc(self.model.match_score))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by match score range: {e}")
            return []
    
    async def get_by_application_status(self, status: str, limit: int = 50) -> List[Job]:
        """Get jobs by application status."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.application_status == status)
                .order_by(desc(self.model.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by application status {status}: {e}")
            return []
    
    async def get_by_remote_status(self, remote_status: str, limit: int = 50) -> List[Job]:
        """Get jobs by remote status."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.remote_status == remote_status)
                .order_by(desc(self.model.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by remote status {remote_status}: {e}")
            return []
    
    async def get_by_salary_range(self, min_salary: float, max_salary: float, limit: int = 50) -> List[Job]:
        """Get jobs by salary range."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(and_(
                    self.model.salary >= min_salary,
                    self.model.salary <= max_salary,
                    self.model.salary.isnot(None)
                ))
                .order_by(desc(self.model.salary))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by salary range: {e}")
            return []
    
    async def search_jobs(self, query: str, limit: int = 50) -> List[Job]:
        """Search jobs by title, company, or description."""
        try:
            search_term = f"%{query}%"
            result = await self.session.execute(
                select(self.model)
                .where(or_(
                    self.model.title.ilike(search_term),
                    self.model.company.ilike(search_term),
                    self.model.jd_text.ilike(search_term)
                ))
                .order_by(desc(self.model.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to search jobs with query '{query}': {e}")
            return []
    
    async def get_top_matches(self, limit: int = 50) -> List[Job]:
        """Get jobs with highest match scores."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(and_(
                    self.model.match_score.isnot(None),
                    self.model.application_status == "not_applied"
                ))
                .order_by(desc(self.model.match_score))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get top matches: {e}")
            return []
    
    async def get_recent_jobs(self, days: int = 7, limit: int = 50) -> List[Job]:
        """Get jobs posted in the last N days."""
        try:
            from datetime import datetime, timedelta
            result = await self.session.execute(
                select(self.model)
                .where(self.model.posted_at >= datetime.utcnow() - timedelta(days=days))
                .order_by(desc(self.model.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get recent jobs: {e}")
            return []
    
    async def update_application_status(self, job_id: UUID, status: str) -> Optional[Job]:
        """Update job application status."""
        try:
            db_obj = await self.get_by_id(job_id)
            if db_obj:
                db_obj.application_status = status
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Updated job {job_id} application status to {status}")
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update job application status: {e}")
            return None
    
    async def update_match_score(self, job_id: UUID, score: float) -> Optional[Job]:
        """Update job match score."""
        try:
            db_obj = await self.get_by_id(job_id)
            if db_obj:
                db_obj.match_score = score
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Updated job {job_id} match score to {score}")
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update job match score: {e}")
            return None
    
    async def update_ai_scores(self, job_id: UUID, scores: Dict[str, float], relevance_reason: str) -> Optional[Job]:
        """Update AI matching scores for a job."""
        try:
            db_obj = await self.get_by_id(job_id)
            if db_obj:
                db_obj.semantic_score = scores.get("semantic")
                db_obj.final_score = scores.get("final")
                db_obj.salary_score = scores.get("salary")
                db_obj.transition_score = scores.get("transition")
                db_obj.relevance_reason = relevance_reason
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Updated AI scores for job {job_id}")
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update AI scores: {e}")
            return None
    
    def validate_job_url(self, job_url: str) -> bool:
        """Validate job URL format and accessibility."""
        if not job_url:
            return False
        
        try:
            parsed = urlparse(job_url)
            
            # Check basic URL structure
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Reject fake/placeholder URLs
            fake_indicators = [
                "example.com",
                "test.com",
                "localhost",
                "127.0.0.1",
                "jobs/tpm-2",
                "jobs/apm-1"
            ]
            
            if any(indicator in job_url.lower() for indicator in fake_indicators):
                return False
            
            # Must be HTTPS
            if parsed.scheme != "https":
                return False
            
            return True
            
        except Exception:
            return False
    
    async def get_by_job_url(self, job_url: str) -> Optional[Job]:
        """Get job by URL (for duplicate detection)."""
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.job_url == job_url)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get job by URL: {e}")
            return None
