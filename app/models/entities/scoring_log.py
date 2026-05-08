from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import BaseModel


class ScoringLog(BaseModel):
    """ScoringLog entity model for tracking AI scoring and analysis activities."""
    
    __tablename__ = "scoring_logs"
    
    # Foreign keys
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    resume_version_id = Column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Scoring details
    scoring_type = Column(String(50), nullable=False, index=True)  # job_match, resume_quality, outreach_success, etc.
    model_version = Column(String(50), nullable=False)  # AI model version used
    
    # Scores
    overall_score = Column(Float, nullable=False, index=True)  # 0-100 overall score
    sub_scores = Column(JSON, nullable=True)  # Detailed sub-scores breakdown
    
    # Input data
    input_data = Column(JSON, nullable=True)  # Input data used for scoring (hash or reference)
    features = Column(JSON, nullable=True)  # Extracted features used for scoring
    
    # Output and reasoning
    reasoning = Column(Text, nullable=True)  # AI reasoning for the score
    recommendations = Column(JSON, nullable=True)  # AI recommendations
    confidence = Column(Float, nullable=True)  # Model confidence in the score
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to process
    token_usage = Column(Integer, nullable=True)  # Tokens used for API calls
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # User rating of score quality (1-5)
    user_feedback = Column(Text, nullable=True)  # User feedback comments
    
    # Status
    is_successful = Column(Boolean, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    job = relationship("Job", backref="scoring_logs")
    application = relationship("Application", backref="scoring_logs")
    resume_version = relationship("ResumeVersion", backref="scoring_logs")
    
    def __repr__(self):
        return f"<ScoringLog(id={self.id}, type='{self.scoring_type}', score={self.overall_score})>"
