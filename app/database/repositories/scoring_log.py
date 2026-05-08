"""ScoringLog repository with scoring-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.models.entities import ScoringLog
from app.core.logging import logger
from .base import BaseRepository


class ScoringLogRepository(BaseRepository[ScoringLog]):
    """Repository for scoring log data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ScoringLog)
    
    async def get_by_job_id(self, job_id: UUID, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs for a specific job."""
        try:
            result = await self.session.execute(
                select(ScoringLog)
                .where(ScoringLog.job_id == job_id)
                .order_by(desc(ScoringLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs for job {job_id}: {e}")
            return []
    
    async def get_by_application_id(self, application_id: UUID, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs for a specific application."""
        try:
            result = await self.session.execute(
                select(ScoringLog)
                .where(ScoringLog.application_id == application_id)
                .order_by(desc(ScoringLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs for application {application_id}: {e}")
            return []
    
    async def get_by_resume_version_id(self, resume_version_id: UUID, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs for a specific resume version."""
        try:
            result = await self.session.execute(
                select(ScoringLog)
                .where(ScoringLog.resume_version_id == resume_version_id)
                .order_by(desc(ScoringLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs for resume version {resume_version_id}: {e}")
            return []
    
    async def get_by_scoring_type(self, scoring_type: str, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs by type."""
        try:
            result = await self.session.execute(
                select(ScoringLog)
                .where(ScoringLog.scoring_type == scoring_type)
                .order_by(desc(ScoringLog.created_at))
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
                select(ScoringLog)
                .where(ScoringLog.model_version == model_version)
                .order_by(desc(ScoringLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs by model version {model_version}: {e}")
            return []
    
    async def get_recent_logs(self, days: int = 7, limit: int = 100) -> List[ScoringLog]:
        """Get recent scoring logs."""
        try:
            result = await self.session.execute(
                select(ScoringLog)
                .where(ScoringLog.created_at >= func.now() - func.interval(days))
                .order_by(desc(ScoringLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get recent scoring logs: {e}")
            return []
    
    async def get_failed_logs(self, limit: int = 50) -> List[ScoringLog]:
        """Get failed scoring logs."""
        try:
            result = await self.session.execute(
                select(ScoringLog)
                .where(ScoringLog.is_successful == False)
                .order_by(desc(ScoringLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get failed scoring logs: {e}")
            return []
    
    async def get_by_score_range(self, min_score: float = 0.0, max_score: float = 100.0, scoring_type: str = None, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs by score range."""
        try:
            query = select(ScoringLog).where(and_(
                ScoringLog.overall_score >= min_score,
                ScoringLog.overall_score <= max_score
            ))
            
            if scoring_type:
                query = query.where(ScoringLog.scoring_type == scoring_type)
            
            result = await self.session.execute(
                query.order_by(desc(ScoringLog.created_at)).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs by score range: {e}")
            return []
    
    async def get_with_user_feedback(self, limit: int = 50) -> List[ScoringLog]:
        """Get scoring logs with user feedback."""
        try:
            result = await self.session.execute(
                select(ScoringLog)
                .where(ScoringLog.user_rating.isnot(None))
                .order_by(desc(ScoringLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get scoring logs with user feedback: {e}")
            return []
    
    async def get_average_score_by_type(self, scoring_type: str, days: int = 30) -> float:
        """Get average score for a scoring type in the last N days."""
        try:
            result = await self.session.execute(
                select(func.avg(ScoringLog.overall_score))
                .where(and_(
                    ScoringLog.scoring_type == scoring_type,
                    ScoringLog.created_at >= func.now() - func.interval(days),
                    ScoringLog.is_successful == True
                ))
            )
            return result.scalar() or 0.0
        except Exception as e:
            logger.error(f"Failed to get average score by type: {e}")
            return 0.0
    
    async def add_user_feedback(self, log_id: UUID, rating: int, feedback: str = None) -> Optional[ScoringLog]:
        """Add user feedback to a scoring log."""
        try:
            db_obj = await self.get_by_id(log_id)
            if db_obj:
                db_obj.user_rating = rating
                db_obj.user_feedback = feedback
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Added user feedback to scoring log {log_id}")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to add user feedback: {e}")
            return None
    
    async def get_performance_metrics(self, model_version: str = None, days: int = 30) -> dict:
        """Get performance metrics for scoring."""
        try:
            query = select(ScoringLog).where(and_(
                ScoringLog.created_at >= func.now() - func.interval(days),
                ScoringLog.is_successful == True
            ))
            
            if model_version:
                query = query.where(ScoringLog.model_version == model_version)
            
            # Total scorings
            total_result = await self.session.execute(query.count())
            total = total_result.scalar()
            
            # Average score
            avg_score_result = await self.session.execute(
                query.with_entities(func.avg(ScoringLog.overall_score))
            )
            avg_score = avg_score_result.scalar() or 0
            
            # Average processing time
            avg_time_result = await self.session.execute(
                query.with_entities(func.avg(ScoringLog.processing_time_ms))
            )
            avg_time = avg_time_result.scalar() or 0
            
            # Total token usage
            total_tokens_result = await self.session.execute(
                query.with_entities(func.sum(ScoringLog.token_usage))
            )
            total_tokens = total_tokens_result.scalar() or 0
            
            # Average user rating
            avg_rating_result = await self.session.execute(
                query.with_entities(func.avg(ScoringLog.user_rating))
                .where(ScoringLog.user_rating.isnot(None))
            )
            avg_rating = avg_rating_result.scalar() or 0
            
            return {
                "total_scorings": total,
                "average_score": float(avg_score),
                "average_processing_time_ms": float(avg_time),
                "total_token_usage": int(total_tokens),
                "average_user_rating": float(avg_rating)
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    async def get_statistics(self) -> dict:
        """Get scoring log statistics."""
        try:
            # Total logs
            total_result = await self.session.execute(
                select(ScoringLog).count()
            )
            total = total_result.scalar()
            
            # Logs by scoring type
            type_result = await self.session.execute(
                select(ScoringLog.scoring_type, func.count(ScoringLog.id))
                .group_by(ScoringLog.scoring_type)
            )
            type_counts = dict(type_result.all())
            
            # Success rate
            successful_result = await self.session.execute(
                select(ScoringLog).where(ScoringLog.is_successful == True).count()
            )
            successful = successful_result.scalar()
            
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # Average score
            avg_score_result = await self.session.execute(
                select(func.avg(ScoringLog.overall_score))
                .where(ScoringLog.is_successful == True)
            )
            avg_score = avg_score_result.scalar() or 0
            
            return {
                "total_logs": total,
                "type_breakdown": type_counts,
                "success_rate": success_rate,
                "successful_logs": successful,
                "average_score": float(avg_score)
            }
        except Exception as e:
            logger.error(f"Failed to get scoring log statistics: {e}")
            return {}
