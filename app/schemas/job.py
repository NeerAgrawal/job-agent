"""Job Pydantic schemas for API request/response models."""

from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


class JobBase(BaseModel):
    """Base schema for all job-related schemas."""
    
    class Config:
        from_attributes = True


class JobCreate(JobBase):
    """Schema for creating a new job."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Job title")
    company: str = Field(..., min_length=1, max_length=200, description="Company name")
    location: Optional[str] = Field(None, max_length=200, description="Job location")
    salary: Optional[float] = Field(None, ge=0, description="Annual salary")
    applicant_count: Optional[int] = Field(0, ge=0, description="Number of applicants")
    source: str = Field(..., min_length=1, max_length=50, description="Job source (LinkedIn, Indeed, etc.)")
    job_url: str = Field(..., min_length=1, max_length=1000, description="Job posting URL")
    posted_at: Optional[datetime] = Field(None, description="When job was posted")
    jd_text: str = Field(..., min_length=1, description="Full job description")
    match_score: Optional[float] = Field(None, ge=0, le=100, description="AI match score (0-100)")
    transition_probability: Optional[float] = Field(None, ge=0, le=1, description="Transition probability (0-1)")
    application_status: str = Field("not_applied", description="Application status")
    remote_status: Optional[str] = Field(None, max_length=50, description="Remote status (remote, hybrid, onsite)")
    domain_tags: Optional[List[str]] = Field(None, description="Domain tags")
    
    @validator('title')
    def normalize_title(cls, v):
        """Normalize job title."""
        if not v:
            return None
        return v.strip().title()
    
    @validator('company')
    def normalize_company(cls, v):
        """Normalize company name."""
        if not v:
            return None
        return v.strip().title()
    
    @validator('location')
    def normalize_location(cls, v):
        """Normalize location."""
        if not v:
            return None
        return v.strip().title()
    
    @validator('salary')
    def validate_salary(cls, v):
        """Validate salary is reasonable."""
        if v is not None and (v < 0 or v > 10000000):
            raise ValueError("Salary must be between 0 and 10,000,000")
        return v


class JobUpdate(JobBase):
    """Schema for updating an existing job."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    salary: Optional[float] = Field(None, ge=0, le=10000000)
    applicant_count: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, min_length=1, max_length=50)
    job_url: Optional[str] = Field(None, min_length=1, max_length=1000)
    posted_at: Optional[datetime] = Field(None)
    jd_text: Optional[str] = Field(None, min_length=1)
    match_score: Optional[float] = Field(None, ge=0, le=100)
    transition_probability: Optional[float] = Field(None, ge=0, le=1)
    application_status: Optional[str] = Field(None, max_length=50)
    remote_status: Optional[str] = Field(None, max_length=50)
    domain_tags: Optional[List[str]] = Field(None)
    
    @validator('salary')
    def validate_salary(cls, v):
        """Validate salary is reasonable."""
        if v is not None and (v < 0 or v > 10000000):
            raise ValueError("Salary must be between 0 and 10,000,000")
        return v


class JobResponse(JobBase):
    """Schema for job response."""
    
    id: UUID
    title: str
    company: str
    location: Optional[str]
    salary: Optional[float]
    applicant_count: int
    source: str
    job_url: str
    posted_at: Optional[datetime]
    jd_text: str
    match_score: Optional[float]
    transition_probability: Optional[float]
    application_status: str
    remote_status: Optional[str]
    domain_tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for job list response."""
    
    jobs: List[JobResponse]
    total: int
    page: int
    size: int
    has_more: bool


class JobFilter(BaseModel):
    """Schema for job filtering."""
    
    search: Optional[str] = Field(None, min_length=1, max_length=200, description="Search term")
    company: Optional[str] = Field(None, min_length=1, max_length=200, description="Company filter")
    location: Optional[str] = Field(None, min_length=1, max_length=200, description="Location filter")
    remote_status: Optional[str] = Field(None, enum=["remote", "hybrid", "onsite"], description="Remote status filter")
    min_salary: Optional[float] = Field(None, ge=0, description="Minimum salary filter")
    max_salary: Optional[float] = Field(None, ge=0, description="Maximum salary filter")
    posted_after: Optional[datetime] = Field(None, description="Posted after date")
    posted_before: Optional[datetime] = Field(None, description="Posted before date")
    application_status: Optional[str] = Field(None, enum=["not_applied", "applied", "interviewing", "rejected", "offered", "withdrawn"], description="Application status filter")
    min_match_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum match score filter")
    max_match_score: Optional[float] = Field(None, ge=0, le=100, description="Maximum match score filter")
    limit: int = Field(50, ge=1, le=1000, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class JobStatistics(BaseModel):
    """Schema for job statistics."""
    
    total_jobs: int
    not_applied: int
    applied: int
    interviewing: int
    rejected: int
    offered: int
    withdrawn: int
    by_source: Dict[str, int]
    by_location: Dict[str, int]
    by_remote_status: Dict[str, int]
    average_match_score: Optional[float]
    average_salary: Optional[float]
    recent_postings: int  # Jobs posted in last 7 days
    created_at: datetime
    updated_at: datetime
