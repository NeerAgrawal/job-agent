"""Base model for SQLAlchemy entities."""

import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID


# Single authoritative Base for all models
Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields."""
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4, 
        index=True,
        nullable=False
    )
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, index=True)
