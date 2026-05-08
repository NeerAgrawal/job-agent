"""Job repository with job-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.sql import func

from app.models.entities import Job
from app.core.logging import logger
from .base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Repository for job data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Job)
    
    async def get_by_company(self, company: str, limit: int = 50) -> List[Job]:
        """Get jobs by company name."""
        try:
            result = await self.session.execute(
                select(Job)
                .where(Job.company.ilike(f"%{company}%"))
                .order_by(desc(Job.posted_at))
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
                select(Job)
                .where(Job.location.ilike(f"%{location}%"))
                .order_by(desc(Job.posted_at))
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
                select(Job)
                .where(Job.source == source)
                .order_by(desc(Job.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by source {source}: {e}")
            return []
    
    async def get_by_status(self, application_status: str, limit: int = 50) -> List[Job]:
        """Get jobs by application status."""
        try:
            result = await self.session.execute(
                select(Job)
                .where(Job.application_status == application_status)
                .order_by(desc(Job.posted_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by status {application_status}: {e}")
            return []
    
    async def get_by_match_score(self, min_score: float = 0.0, max_score: float = 100.0, limit: int = 50) -> List[Job]:
        """Get jobs by match score range."""
        try:
            result = await self.session.execute(
                select(Job)
                .where(and_(
                    Job.match_score >= min_score,
                    Job.match_score <= max_score,
                    Job.match_score.isnot(None)
                ))
                .order_by(desc(Job.match_score))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get jobs by match score range {min_score}-{max_score}: {e}")
            return []
    
    async def search_jobs(
        self, 
        query: str = None, 
        company: str = None, 
        location: str = None,
        remote_status: str = None,
        min_salary: float = None,
        limit: int = 50
    ) -> List[Job]:
        """Search jobs with multiple filters."""
        try:
            db_query = select(Job)
            
            # Build filters
            filters = []
            
            if query:
                filters.append(or_(
                    Job.title.ilike(f"%{query}%"),
                    Job.jd_text.ilike(f"%{query}%")
                ))
            
            if company:
                filters.append(Job.company.ilike(f"%{company}%"))
            
            if location:
                filters.append(Job.location.ilike(f"%{location}%"))
            
            if remote_status:
                filters.append(Job.remote_status == remote_status)
            
            if min_salary:
                filters.append(Job.salary >= min_salary)
            
            # Apply filters
            if filters:
                db_query = db_query.where(and_(*filters))
            
            # Order and limit
            result = await self.session.execute(
                db_query.order_by(desc(Job.posted_at)).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to search jobs: {e}")
            return []
    
    async def get_top_matches(self, limit: int = 20) -> List[Job]:
        """Get jobs with highest match scores."""
        try:
            result = await self.session.execute(
                select(Job)
                .where(and_(
                    Job.match_score.isnot(None),
                    Job.application_status == "not_applied"
                ))
                .order_by(desc(Job.match_score))
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
                select(Job)
                .where(Job.posted_at >= datetime.utcnow() - timedelta(days=days))
                .order_by(desc(Job.posted_at))
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
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update application status: {e}")
            return None
    
    async def get_by_url(self, job_url: str) -> Optional[Job]:
        """Get job by URL (for duplicate checking)."""
        try:
            result = await self.session.execute(
                select(Job).where(Job.job_url == job_url)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get job by URL {job_url}: {e}")
            return None
