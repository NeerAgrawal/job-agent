"""Base repository for all database operations."""

from typing import List, Optional, Dict, Any, Generic, TypeVar
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text

from app.models import BaseModel
from app.core.logging import logger

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
        self.logger = logger
    
    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        try:
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            logger.info(f"Created {self.model.__name__}: {db_obj.id}")
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get a record by ID."""
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} by ID: {e}")
            return None
    
    async def get_all(
    self,
    limit: int = 100,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get all records with optional filtering."""

        try:

            query = select(self.model)

            if filters:

                for key, value in filters.items():

                    if hasattr(self.model, key):

                        query = query.where(
                            getattr(self.model, key) == value
                        )

            query = query.offset(offset).limit(limit)

            result = await self.session.execute(query)

            records = result.scalars().all()

            return list(records)

        except Exception as e:

            logger.error(
                f"Failed to get all {self.model.__name__}: {e}"
            )

            return []
    
    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        try:
            db_obj = await self.get_by_id(id)
            if not db_obj:
                return False
            
            await self.session.delete(db_obj)
            await self.session.commit()
            logger.info(f"Deleted {self.model.__name__}: {id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete {self.model.__name__}: {e}")
            return False
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        try:
            query = select(func.count()).select_from(self.model)
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"Failed to count {self.model.__name__}: {e}")
            return 0
    
    async def exists(self, id: UUID) -> bool:
        """Check if a record exists by ID."""
        try:
            result = await self.session.execute(
                select(func.count()).select_from(self.model).where(self.model.id == id)
            )
            return result.scalar() > 0
        except Exception as e:
            logger.error(f"Failed to check if {self.model.__name__} exists: {e}")
            return False
