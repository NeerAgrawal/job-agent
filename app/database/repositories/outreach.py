"""Outreach repository with outreach-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.models.entities import Outreach, Job
from app.core.logging import logger
from .base import BaseRepository


class OutreachRepository(BaseRepository[Outreach]):
    """Repository for outreach data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Outreach)
    
    async def get_by_job_id(self, job_id: UUID) -> List[Outreach]:
        """Get outreach activities for a specific job."""
        try:
            result = await self.session.execute(
                select(Outreach)
                .where(Outreach.job_id == job_id)
                .order_by(desc(Outreach.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get outreach for job {job_id}: {e}")
            return []
    
    async def get_by_contact(self, contact_name: str = None, contact_email: str = None) -> List[Outreach]:
        """Get outreach activities by contact."""
        try:
            query = select(Outreach)
            
            if contact_name:
                query = query.where(Outreach.contact_name.ilike(f"%{contact_name}%"))
            
            if contact_email:
                query = query.where(Outreach.contact_email == contact_email)
            
            result = await self.session.execute(
                query.order_by(desc(Outreach.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get outreach by contact: {e}")
            return []
    
    async def get_by_type(self, outreach_type: str, limit: int = 50) -> List[Outreach]:
        """Get outreach activities by type."""
        try:
            result = await self.session.execute(
                select(Outreach)
                .where(Outreach.outreach_type == outreach_type)
                .order_by(desc(Outreach.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get outreach by type {outreach_type}: {e}")
            return []
    
    async def get_by_status(self, status: str, limit: int = 50) -> List[Outreach]:
        """Get outreach activities by status."""
        try:
            result = await self.session.execute(
                select(Outreach)
                .where(Outreach.status == status)
                .order_by(desc(Outreach.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get outreach by status {status}: {e}")
            return []
    
    async def get_sent_outreach(self, days: int = 30, limit: int = 50) -> List[Outreach]:
        """Get outreach activities sent in the last N days."""
        try:
            result = await self.session.execute(
                select(Outreach)
                .where(and_(
                    Outreach.sent_at.isnot(None),
                    Outreach.sent_at >= func.now() - func.interval(days)
                ))
                .order_by(desc(Outreach.sent_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get sent outreach: {e}")
            return []
    
    async def get_pending_followups(self, days: int = 7) -> List[Outreach]:
        """Get outreach activities that need follow-up."""
        try:
            result = await self.session.execute(
                select(Outreach)
                .where(and_(
                    Outreach.follow_up_scheduled.isnot(None),
                    Outreach.follow_up_scheduled >= func.now(),
                    Outreach.follow_up_scheduled <= func.now() + func.interval(days)
                ))
                .order_by(asc(Outreach.follow_up_scheduled))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get pending follow-ups: {e}")
            return []
    
    async def get_with_job(self, outreach_id: UUID) -> Optional[Outreach]:
        """Get outreach with associated job data."""
        try:
            result = await self.session.execute(
                select(Outreach)
                .options(selectinload(Outreach.job))
                .where(Outreach.id == outreach_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get outreach with job {outreach_id}: {e}")
            return None
    
    async def update_status(self, outreach_id: UUID, status: str) -> Optional[Outreach]:
        """Update outreach status."""
        try:
            db_obj = await self.get_by_id(outreach_id)
            if db_obj:
                db_obj.status = status
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Updated outreach {outreach_id} status to {status}")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update outreach status: {e}")
            return None
    
    async def mark_as_sent(self, outreach_id: UUID) -> Optional[Outreach]:
        """Mark outreach as sent."""
        try:
            db_obj = await self.get_by_id(outreach_id)
            if db_obj:
                db_obj.status = "sent"
                db_obj.sent_at = func.now()
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Marked outreach {outreach_id} as sent")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to mark outreach as sent: {e}")
            return None
    
    async def add_response(self, outreach_id: UUID, response_content: str, sentiment: str = None) -> Optional[Outreach]:
        """Add response to outreach."""
        try:
            db_obj = await self.get_by_id(outreach_id)
            if db_obj:
                db_obj.response_content = response_content
                db_obj.response_sentiment = sentiment
                db_obj.replied_at = func.now()
                db_obj.status = "replied"
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Added response to outreach {outreach_id}")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to add response to outreach: {e}")
            return None
    
    async def schedule_followup(self, outreach_id: UUID, followup_date) -> Optional[Outreach]:
        """Schedule follow-up for outreach."""
        try:
            db_obj = await self.get_by_id(outreach_id)
            if db_obj:
                db_obj.follow_up_scheduled = followup_date
                db_obj.status = "follow_up"
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Scheduled follow-up for outreach {outreach_id}")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to schedule follow-up: {e}")
            return None
    
    async def get_statistics(self) -> dict:
        """Get outreach statistics."""
        try:
            # Total outreach
            total_result = await self.session.execute(
                select(Outreach).count()
            )
            total = total_result.scalar()
            
            # Outreach by type
            type_result = await self.session.execute(
                select(Outreach.outreach_type, func.count(Outreach.id))
                .group_by(Outreach.outreach_type)
            )
            type_counts = dict(type_result.all())
            
            # Outreach by status
            status_result = await self.session.execute(
                select(Outreach.status, func.count(Outreach.id))
                .group_by(Outreach.status)
            )
            status_counts = dict(status_result.all())
            
            # Response rate
            responded_result = await self.session.execute(
                select(Outreach).where(Outreach.response_content.isnot(None)).count()
            )
            responded = responded_result.scalar()
            
            response_rate = (responded / total * 100) if total > 0 else 0
            
            return {
                "total_outreach": total,
                "type_breakdown": type_counts,
                "status_breakdown": status_counts,
                "response_rate": response_rate,
                "responded_outreach": responded
            }
        except Exception as e:
            logger.error(f"Failed to get outreach statistics: {e}")
            return {}
