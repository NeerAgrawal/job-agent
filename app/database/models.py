"""Database models import."""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base

# Import models from the canonical location
from app.models import Base, BaseModel, Job, Application, Outreach, ResumeVersion, ScoringLog

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

