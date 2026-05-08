from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BaseSchema(BaseModel):
    """Base Pydantic schema with common fields."""
    
    class Config:
        from_attributes = True


class TimestampedSchema(BaseSchema):
    """Base schema with timestamp fields."""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResponseSchema(BaseSchema):
    """Standard API response schema."""
    success: bool = True
    message: str
    data: Optional[dict] = None


class PaginatedResponse(BaseSchema):
    """Paginated response schema."""
    items: list
    total: int
    page: int
    size: int
    pages: int
