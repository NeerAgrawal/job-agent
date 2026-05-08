"""Database models import."""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

__all__ = [
    "Base", 
    "metadata", 
    "BaseModel", 
    "Job", 
    "Application", 
    "Outreach", 
    "ResumeVersion", 
    "ScoringLog"
]

