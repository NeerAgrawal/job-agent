"""ScoringLog repository with scoring log-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.sql import func

from app.models import ScoringLog
from app.core.logging import logger
from .base import BaseRepository


class ScoringLogRepository(BaseRepository[ScoringLog]):
    """Repository for scoring log data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ScoringLog, session)
    
    async def get_by_job_id(self, job_id: UUID, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs by job ID."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.job_id == job_id)
                .order_by(desc(self.model.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs by job ID {job_id}: {e}")
            return []
    
    async def get_by_scoring_type(self, scoring_type: str, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs by scoring type."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.scoring_type == scoring_type)
                .order_by(desc(self.model.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs by type {scoring_type}: {e}")
            return []
    
    async def get_by_model_version(self, model_version: str, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs by model version."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.model_version == model_version)
                .order_by(desc(self.model.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs by model version {model_version}: {e}")
            return []
    
    async def get_by_score_range(self, min_score: float, max_score: float, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs by score range."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(and_(
                    self.model.overall_score >= min_score,
                    self.model.overall_score <= max_score
                ))
                .order_by(desc(self.model.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs by score range: {e}")
            return []
    
    async def get_successful_logs(self, limit: int = 50) -> List[ScoringLog]:
        """Get successful scoring logs."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.is_successful == True)
                .order_by(desc(self.model.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get successful scoring logs: {e}")
            return []
    
    async def get_failed_logs(self, limit: int = 50) -> List[ScoringLog]:
        """Get failed scoring logs."""
        try:
            result = await self.session.execute(
                select(self.model)
                .where(self.model.is_successful == False)
                .order_by(desc(self.model.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get failed scoring logs: {e}")
            return []
