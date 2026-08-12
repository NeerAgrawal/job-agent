from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Uuid as UUID
from .base import BaseModel


class Outreach(BaseModel):
    """Outreach entity model for tracking networking and outreach activities."""
    
    __tablename__ = "outreach"
    
    # Foreign key to Job (optional - can be general outreach)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Contact information
    contact_name = Column(String(200), nullable=False, index=True)
    contact_email = Column(String(255), nullable=True, index=True)
    contact_company = Column(String(200), nullable=True, index=True)
    contact_role = Column(String(100), nullable=True)
    contact_linkedin = Column(String(500), nullable=True)
    
    # Outreach details
    outreach_type = Column(String(50), nullable=False, index=True)  # email, linkedin, referral, cold_call, etc.
    subject = Column(String(500), nullable=True)
    message_content = Column(Text, nullable=False)
    
    # Status tracking
    status = Column(String(50), default="draft", index=True)  # draft, sent, replied, interested, not_interested, follow_up
    sent_at = Column(DateTime, nullable=True, index=True)
    replied_at = Column(DateTime, nullable=True, index=True)
    
    # Response tracking
    response_content = Column(Text, nullable=True)
    response_sentiment = Column(String(50), nullable=True)  # positive, neutral, negative
    follow_up_scheduled = Column(DateTime, nullable=True, index=True)
    
    # AI analysis
    outreach_score = Column(Float, nullable=True, index=True)  # AI confidence in outreach quality
    response_probability = Column(Float, nullable=True)  # Predicted probability of response
    
    # Metadata
    notes = Column(Text, nullable=True)  # User notes about outreach
    tags = Column(JSON, nullable=True)  # User-defined tags
    template_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to template if used
    
    # Relationships
    job = relationship("Job", backref="outreach_activities")
    
    def __repr__(self):
        return f"<Outreach(id={self.id}, contact='{self.contact_name}', type='{self.outreach_type}')>"
