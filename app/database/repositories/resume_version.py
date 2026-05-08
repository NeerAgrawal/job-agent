"""ResumeVersion repository with resume-specific operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.sql import func

from app.models.entities import ResumeVersion
from app.core.logging import logger
from .base import BaseRepository


class ResumeVersionRepository(BaseRepository[ResumeVersion]):
    """Repository for resume version data operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ResumeVersion)
    
    async def get_active_versions(self, limit: int = 20) -> List[ResumeVersion]:
        """Get active resume versions."""
        try:
            result = await self.session.execute(
                select(ResumeVersion)
                .where(ResumeVersion.is_active == True)
                .order_by(desc(ResumeVersion.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get active resume versions: {e}")
            return []
    
    async def get_primary_version(self) -> Optional[ResumeVersion]:
        """Get the primary/default resume version."""
        try:
            result = await self.session.execute(
                select(ResumeVersion)
                .where(ResumeVersion.is_primary == True)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get primary resume version: {e}")
            return None
    
    async def set_primary_version(self, version_id: UUID) -> Optional[ResumeVersion]:
        """Set a resume version as primary (unsets others)."""
        try:
            # Unset all current primary versions
            await self.session.execute(
                select(ResumeVersion).where(ResumeVersion.is_primary == True)
            )
            
            # Set new primary
            db_obj = await self.get_by_id(version_id)
            if db_obj:
                # First, unset all primary flags
                await self.session.execute(
                    select(ResumeVersion).where(ResumeVersion.is_primary == True)
                )
                all_versions = await self.session.execute(
                    select(ResumeVersion).where(ResumeVersion.is_primary == True)
                )
                for version in all_versions.scalars().all():
                    version.is_primary = False
                
                # Set new primary
                db_obj.is_primary = True
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Set resume version {version_id} as primary")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to set primary resume version: {e}")
            return None
    
    async def get_by_target(self, job_title: str = None, company: str = None) -> List[ResumeVersion]:
        """Get resume versions by target job/company."""
        try:
            query = select(ResumeVersion)
            
            if job_title:
                query = query.where(ResumeVersion.target_job_title.ilike(f"%{job_title}%"))
            
            if company:
                query = query.where(ResumeVersion.target_company.ilike(f"%{company}%"))
            
            result = await self.session.execute(
                query.order_by(desc(ResumeVersion.created_at))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get resume versions by target: {e}")
            return []
    
    async def get_most_used(self, limit: int = 10) -> List[ResumeVersion]:
        """Get most used resume versions."""
        try:
            result = await self.session.execute(
                select(ResumeVersion)
                .where(ResumeVersion.usage_count > 0)
                .order_by(desc(ResumeVersion.usage_count))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get most used resume versions: {e}")
            return []
    
    async def get_by_score(self, min_score: float = 0.0, max_score: float = 100.0, limit: int = 20) -> List[ResumeVersion]:
        """Get resume versions by score range."""
        try:
            result = await self.session.execute(
                select(ResumeVersion)
                .where(and_(
                    ResumeVersion.resume_score >= min_score,
                    ResumeVersion.resume_score <= max_score,
                    ResumeVersion.resume_score.isnot(None)
                ))
                .order_by(desc(ResumeVersion.resume_score))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get resume versions by score range: {e}")
            return []
    
    async def increment_usage(self, version_id: UUID) -> Optional[ResumeVersion]:
        """Increment usage count for a resume version."""
        try:
            db_obj = await self.get_by_id(version_id)
            if db_obj:
                db_obj.usage_count += 1
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Incremented usage for resume version {version_id}")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to increment usage: {e}")
            return None
    
    async def update_performance_metrics(self, version_id: UUID, response_rate: float = None, interview_rate: float = None) -> Optional[ResumeVersion]:
        """Update performance metrics for a resume version."""
        try:
            db_obj = await self.get_by_id(version_id)
            if db_obj:
                if response_rate is not None:
                    db_obj.response_rate = response_rate
                if interview_rate is not None:
                    db_obj.interview_rate = interview_rate
                
                await self.session.commit()
                await self.session.refresh(db_obj)
                logger.info(f"Updated performance metrics for resume version {version_id}")
                return db_obj
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update performance metrics: {e}")
            return None
    
    async def search_by_content(self, query: str, limit: int = 20) -> List[ResumeVersion]:
        """Search resume versions by content."""
        try:
            result = await self.session.execute(
                select(ResumeVersion)
                .where(or_(
                    ResumeVersion.name.ilike(f"%{query}%"),
                    ResumeVersion.raw_text.ilike(f"%{query}%"),
                    ResumeVersion.target_job_title.ilike(f"%{query}%"),
                    ResumeVersion.target_company.ilike(f"%{query}%")
                ))
                .order_by(desc(ResumeVersion.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to search resume versions by content: {e}")
            return []
    
    async def get_statistics(self) -> dict:
        """Get resume version statistics."""
        try:
            # Total versions
            total_result = await self.session.execute(
                select(ResumeVersion).count()
            )
            total = total_result.scalar()
            
            # Active versions
            active_result = await self.session.execute(
                select(ResumeVersion).where(ResumeVersion.is_active == True).count()
            )
            active = active_result.scalar()
            
            # Average usage
            usage_result = await self.session.execute(
                select(func.avg(ResumeVersion.usage_count))
                .where(ResumeVersion.usage_count > 0)
            )
            avg_usage = usage_result.scalar() or 0
            
            # Total usage
            total_usage_result = await self.session.execute(
                select(func.sum(ResumeVersion.usage_count))
            )
            total_usage = total_usage_result.scalar() or 0
            
            # Average score
            score_result = await self.session.execute(
                select(func.avg(ResumeVersion.resume_score))
                .where(ResumeVersion.resume_score.isnot(None))
            )
            avg_score = score_result.scalar() or 0
            
            return {
                "total_versions": total,
                "active_versions": active,
                "average_usage": float(avg_usage),
                "total_usage": int(total_usage),
                "average_score": float(avg_score)
            }
        except Exception as e:
            logger.error(f"Failed to get resume version statistics: {e}")
            return {}
