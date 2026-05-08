from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, JSON, Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import BaseModel


class Job(BaseModel):
    """Job entity model for storing job listings."""
    
    __tablename__ = "jobs"
    
    # Basic job information
    title = Column(String(500), nullable=False, index=True)
    company = Column(String(200), nullable=False, index=True)
    location = Column(String(200), nullable=True, index=True)
    salary = Column(Float, nullable=True)  # Annual salary
    applicant_count = Column(Integer, default=0, nullable=False)
    
    # Job source and tracking
    source = Column(String(50), nullable=False, index=True)  # LinkedIn, Indeed, etc.
    job_url = Column(String(1000), nullable=False, unique=True, index=True)
    posted_at = Column(DateTime, nullable=True, index=True)
    
    # Job details
    jd_text = Column(Text, nullable=False)  # Full job description
    
    # AI processing fields
    match_score = Column(Float, nullable=True, index=True)  # 0-100 match score
    transition_probability = Column(Float, nullable=True)  # 0-1 probability
    
    # Application tracking
    application_status = Column(String(50), default="not_applied", index=True)  # not_applied, applied, interviewing, rejected, offered
    remote_status = Column(String(50), index=True)  # remote, hybrid, onsite
    
    # Domain and classification
    domain_tags = Column(JSON, nullable=True)  # Array of domain tags
    
    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}')>"
    
    @property
    def salary_formatted(self):
        """Return formatted salary."""
        if self.salary:
            return f"${self.salary:,.0f}"
        return "Salary not specified"
