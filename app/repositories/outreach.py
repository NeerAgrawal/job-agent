"""Outreach repository with outreach-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.sql import func

from app.models import Outreach
from app.core.logging import logger
from .base import BaseRepository


class OutreachRepository(BaseRepository[Outreach]):
    """Repository for outreach data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Outreach, session)
    
    async def get_by_job_id(self, job_id: UUID) -> List[Outreach]:
        """Get outreach activities by job ID."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.job_id == job_id)
                .order_by(desc(self.model.sent_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get outreach by job ID {job_id}: {e}")
            return []
    
    async def get_by_contact(self, contact_email: str) -> List[Outreach]:
        """Get outreach activities by contact email."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.contact_email == contact_email)
                .order_by(desc(self.model.sent_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get outreach by contact {contact_email}: {e}")
            return []
    
    async def get_by_type(self, outreach_type: str, limit: int = 50) -> List[Outreach]:
        """Get outreach activities by type."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.outreach_type == outreach_type)
                .order_by(desc(self.model.sent_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get outreach by type {outreach_type}: {e}")
            return []
    
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
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update outreach status: {e}")
            return None
