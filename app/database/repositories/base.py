"""Base repository class with common CRUD operations."""

from typing import List, Optional, Type, TypeVar, Generic
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from app.core.logging import logger

# Generic type for model classes
ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model
    
    async def create(self, obj_in: dict) -> ModelType:
        """Create a new record."""
        try:
            db_obj = self.model(**obj_in)
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
        """Get record by ID."""
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get {self.model.__name__} {id}: {e}")
            return None
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[ModelType]:
        """Get all records with pagination."""
        try:
            query = select(self.model)
            
            # Add ordering
            if hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                if order_desc:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))
            
            result = await self.session.execute(
                query.offset(skip).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get all {self.model.__name__}: {e}")
            return []
    
    async def update(self, id: UUID, obj_in: dict) -> Optional[ModelType]:
        """Update a record."""
        try:
            db_obj = await self.get_by_id(id)
            if not db_obj:
                return None
            
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            await self.session.commit()
            await self.session.refresh(db_obj)
            logger.info(f"Updated {self.model.__name__}: {id}")
            return db_obj
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update {self.model.__name__} {id}: {e}")
            raise
    
    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        try:
            db_obj = await self.get_by_id(id)
            if db_obj:
                await self.session.delete(db_obj)
                await self.session.commit()
                logger.info(f"Deleted {self.model.__name__}: {id}")
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete {self.model.__name__} {id}: {e}")
            return False
    
    async def count(self) -> int:
        """Count all records."""
        try:
            result = await self.session.execute(
                select(self.model).count()
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Failed to count {self.model.__name__}: {e}")
            return 0
