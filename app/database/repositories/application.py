"""Application repository with application-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.models.entities import Application, Job
from app.core.logging import logger
from .base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    """Repository for application data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Application)
    
    async def get_by_job_id(self, job_id: UUID) -> List[Application]:
        """Get applications for a specific job."""
        try:
            result = await self.session.execute(
                select(Application)
                .where(Application.job_id == job_id)
                .order_by(desc(Application.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get applications for job {job_id}: {e}")
            return []
    
    async def get_by_status(self, status: str, limit: int = 50) -> List[Application]:
        """Get applications by status."""
        try:
            result = await self.session.execute(
                select(Application)
                .where(Application.status == status)
                .order_by(desc(Application.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get applications by status {status}: {e}")
            return []
    
    async def get_with_job(self, application_id: UUID) -> Optional[Application]:
        """Get application with associated job data."""
        try:
            result = await self.session.execute(
                select(Application)
                .options(selectinload(Application.job))
                .where(Application.id == application_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get application with job {application_id}: {e}")
            return None
    
    async def get_active_applications(self, limit: int = 50) -> List[Application]:
        """Get applications that are still active (not rejected/withdrawn)."""
        try:
            result = await self.session.execute(
                select(Application)
                .where(Application.status.in_(["draft", "submitted", "viewed", "interviewing", "offered"]))
                .order_by(desc(Application.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get active applications: {e}")
            return []
    
    async def get_recent_applications(self, days: int = 7, limit: int = 50) -> List[Application]:
        """Get applications submitted in the last N days."""
        try:
            result = await self.session.execute(
                select(Application)
                .where(and_(
                    Application.applied_at.isnot(None),
                    Application.applied_at >= func.now() - func.interval(days)
                ))
                .order_by(desc(Application.applied_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get recent applications: {e}")
            return []
    
    async def get_upcoming_interviews(self, days: int = 7) -> List[Application]:
        """Get applications with upcoming interviews."""
        try:
            result = await self.session.execute(
                select(Application)
                .where(and_(
                    Application.next_interview_date.isnot(None),
                    Application.next_interview_date >= func.now(),
                    Application.next_interview_date <= func.now() + func.interval(days)
                ))
                .order_by(asc(Application.next_interview_date))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get upcoming interviews: {e}")
            return []
    
    async def get_offers(self, active_only: bool = True) -> List[Application]:
        """Get applications with offers."""
        try:
            query = select(Application).where(Application.status == "offered")
            
            if active_only:
                query = query.where(
                    or_(
                        Application.offer_expires_at.is_(None),
                        Application.offer_expires_at > func.now()
                    )
                )
            
            result = await self.session.execute(
                query.order_by(desc(Application.offer_expires_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get offers: {e}")
            return []
    
    async def update_status(self, application_id: UUID, status: str) -> Optional[Application]:
        """Update application status."""
        try:
            db_obj = await self.get_by_id(application_id)
            if db_obj:
                db_obj.status = status
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Updated application {application_id} status to {status}")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update application status: {e}")
            return None
    
    async def add_interview_stage(self, application_id: UUID, stage_data: dict) -> Optional[Application]:
        """Add interview stage to application."""
        try:
            db_obj = await self.get_by_id(application_id)
            if db_obj:
                if not db_obj.interview_stages:
                    db_obj.interview_stages = []
                
                db_obj.interview_stages.append(stage_data)
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Added interview stage to application {application_id}")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to add interview stage: {e}")
            return None
    
    async def get_statistics(self) -> dict:
        """Get application statistics."""
        try:
            # Total applications
            total_result = await self.session.execute(
                select(Application).count()
            )
            total = total_result.scalar()
            
            # Applications by status
            status_result = await self.session.execute(
                select(Application.status, func.count(Application.id))
                .group_by(Application.status)
            )
            status_counts = dict(status_result.all())
            
            # Response rate
            responded_result = await self.session.execute(
                select(Application).where(Application.company_response.isnot(None)).count()
            )
            responded = responded_result.scalar()
            
            response_rate = (responded / total * 100) if total > 0 else 0
            
            return {
                "total_applications": total,
                "status_breakdown": status_counts,
                "response_rate": response_rate,
                "responded_applications": responded
            }
        except Exception as e:
            logger.error(f"Failed to get application statistics: {e}")
            return {}
