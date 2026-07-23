from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import uuid
from app.models.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class TargetCompany(Base):
    __tablename__ = "target_companies"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(200), index=True, nullable=False)
    domain = Column(String(200), unique=True, index=True, nullable=False)
    careers_url = Column(String(500), nullable=True)
    ats_provider = Column(String(50), nullable=True) # e.g. "greenhouse", "lever", "ashby", "workable"
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
