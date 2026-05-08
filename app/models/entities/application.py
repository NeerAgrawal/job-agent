from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import BaseModel


class Application(BaseModel):
    """Application entity model for tracking job applications."""
    
    __tablename__ = "applications"
    
    # Foreign key to Job
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Application details
    status = Column(String(50), default="draft", index=True)  # draft, submitted, viewed, interviewing, rejected, offered, withdrawn
    applied_at = Column(DateTime, nullable=True, index=True)  # When application was submitted
    last_contact_at = Column(DateTime, nullable=True, index=True)  # Last communication
    
    # Application content
    cover_letter = Column(Text, nullable=True)
    resume_version_id = Column(UUID(as_uuid=True), ForeignKey("resume_versions.id"), nullable=True)
    
    # Company response tracking
    company_response = Column(Text, nullable=True)  # Company's response message
    response_received_at = Column(DateTime, nullable=True)
    
    # Interview tracking
    interview_stages = Column(JSON, nullable=True)  # Array of interview stages with dates
    next_interview_date = Column(DateTime, nullable=True, index=True)
    
    # Offer details
    offer_salary = Column(Float, nullable=True)
    offer_bonus = Column(Float, nullable=True)
    offer_equity = Column(Float, nullable=True)
    offer_expires_at = Column(DateTime, nullable=True)
    
    # AI scoring
    application_score = Column(Float, nullable=True, index=True)  # AI confidence in application quality
    response_probability = Column(Float, nullable=True)  # Predicted probability of response
    
    # Metadata
    notes = Column(Text, nullable=True)  # User notes about application
    tags = Column(JSON, nullable=True)  # User-defined tags
    
    # Relationships
    job = relationship("Job", backref="applications")
    resume_version = relationship("ResumeVersion", backref="applications")
    
    def __repr__(self):
        return f"<Application(id={self.id}, job_id={self.job_id}, status='{self.status}')>"
