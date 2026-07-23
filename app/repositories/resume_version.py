"""ResumeVersion repository with resume version-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, desc, asc
from sqlalchemy.sql import func

from app.models import ResumeVersion
from app.core.logging import logger
from .base import BaseRepository


class ResumeVersionRepository(BaseRepository[ResumeVersion]):
    """Repository for resume version data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ResumeVersion, session)
    
    async def get_active_versions(self, limit: int = 50) -> List[ResumeVersion]:
        """Get active resume versions."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.is_active == True)
                .order_by(desc(self.model.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get active resume versions: {e}")
            return []
    
    async def get_primary_version(self) -> Optional[ResumeVersion]:
        """Get the primary resume version."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.is_primary == True)
                .order_by(desc(self.model.created_at))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get primary resume version: {e}")
            return None
    
    async def set_primary_version(self, version_id: UUID) -> Optional[ResumeVersion]:
        """Set a resume version as primary."""
        try:
            # First, unset any existing primary version
            await self.session.execute(
                update(self.model).where(self.model.is_primary == True).values(is_primary=False)
            )

            # Set new primary version
            db_obj = await self.get_by_id(version_id)
            if db_obj:
                db_obj.is_primary = True
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Set resume version {version_id} as primary")
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to set primary resume version: {e}")
            return None
    
    async def update_usage_stats(self, version_id: UUID, response_rate: float, interview_rate: float) -> Optional[ResumeVersion]:
        """Update usage statistics for a resume version."""
        try:
            db_obj = await self.get_by_id(version_id)
            if db_obj:
                db_obj.usage_count += 1
                db_obj.response_rate = response_rate
                db_obj.interview_rate = interview_rate
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Updated usage stats for resume version {version_id}")
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update usage stats: {e}")
            return None
