from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, JSON, Integer
from sqlalchemy.sql import func
from sqlalchemy import Uuid as UUID
from .base import BaseModel


class ResumeVersion(BaseModel):
    """ResumeVersion entity model for tracking different resume versions."""
    
    __tablename__ = "resume_versions"
    
    # Resume details
    name = Column(String(200), nullable=False, index=True)  # Version name/description
    file_path = Column(String(500), nullable=False)  # Path to resume file
    file_type = Column(String(20), nullable=False)  # pdf, docx, etc.
    
    # Content
    raw_text = Column(Text, nullable=False)  # Extracted text from resume
    formatted_content = Column(Text, nullable=True)  # Formatted resume content
    
    # Target information
    target_job_title = Column(String(200), nullable=True, index=True)
    target_company = Column(String(200), nullable=True, index=True)
    target_keywords = Column(JSON, nullable=True)  # Keywords this resume is optimized for
    
    # Performance tracking
    usage_count = Column(Integer, default=0, nullable=False)  # How many times used
    response_rate = Column(Float, nullable=True)  # Response rate when this version used
    interview_rate = Column(Float, nullable=True)  # Interview rate when this version used
    
    # AI analysis
    resume_score = Column(Float, nullable=True, index=True)  # AI confidence in resume quality
    skill_matches = Column(JSON, nullable=True)  # AI-identified skills and their confidence
    experience_years = Column(Float, nullable=True)  # AI-calculated years of experience
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_primary = Column(Boolean, default=False, index=True)  # Primary/default resume
    
    # Metadata
    notes = Column(Text, nullable=True)  # User notes about this version
    tags = Column(JSON, nullable=True)  # User-defined tags
    
    def __repr__(self):
        return f"<ResumeVersion(id={self.id}, name='{self.name}', file_type='{self.file_type}')>"
