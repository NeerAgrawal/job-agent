"""Application repository with application-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.sql import func

from app.models import Application
from app.core.logging import logger
from .base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    """Repository for application data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Application, session)
    
    async def get_by_job_id(self, job_id: UUID) -> List[Application]:
        """Get applications by job ID."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.job_id == job_id)
                .order_by(desc(self.model.applied_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get applications by job ID {job_id}: {e}")
            return []
    
    async def get_by_status(self, status: str, limit: int = 50) -> List[Application]:
        """Get applications by status."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.status == status)
                .order_by(desc(self.model.applied_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get applications by status {status}: {e}")
            return []
    
    async def get_by_resume_version(self, resume_version_id: UUID) -> List[Application]:
        """Get applications by resume version."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.resume_version_id == resume_version_id)
                .order_by(desc(self.model.applied_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get applications by resume version {resume_version_id}: {e}")
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
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update application status: {e}")
            return None
