"""Database seed script for initial data."""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import engine
from app.database.session import get_db_session
from app.repositories import (
    JobRepository,
    ApplicationRepository,
    OutreachRepository,
    ResumeVersionRepository,
    ScoringLogRepository
)
from app.models import Job, Application, Outreach, ResumeVersion, ScoringLog
from app.core.logging import logger


async def create_sample_jobs() -> list[Job]:
    """Create sample job records."""
    jobs_data = [
        {
            "title": "Senior Product Manager",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "salary": 180000.0,
            "applicant_count": 45,
            "source": "LinkedIn",
            "job_url": "https://linkedin.com/jobs/view/12345",
            "posted_at": datetime.utcnow() - timedelta(days=3),
            "jd_text": "We are looking for an experienced Product Manager to lead our product strategy...",
            "match_score": 85.5,
            "transition_probability": 0.75,
            "application_status": "not_applied",
            "remote_status": "hybrid",
            "domain_tags": ["saas", "b2b", "product"]
        },
        {
            "title": "Product Manager, AI/ML",
            "company": "DataTech Inc",
            "location": "Remote",
            "salary": 160000.0,
            "applicant_count": 120,
            "source": "Indeed",
            "job_url": "https://indeed.com/jobs/view/67890",
            "posted_at": datetime.utcnow() - timedelta(days=1),
            "jd_text": "Join our AI/ML team as a Product Manager to drive machine learning products...",
            "match_score": 92.3,
            "transition_probability": 0.85,
            "application_status": "applied",
            "remote_status": "remote",
            "domain_tags": ["ai", "ml", "data"]
        },
        {
            "title": "Technical Product Manager",
            "company": "StartupXYZ",
            "location": "New York, NY",
            "salary": 140000.0,
            "applicant_count": 28,
            "source": "AngelList",
            "job_url": "https://angel.co/jobs/view/24680",
            "posted_at": datetime.utcnow() - timedelta(days=5),
            "jd_text": "Looking for a Technical Product Manager to help build our developer tools platform...",
            "match_score": 78.9,
            "transition_probability": 0.65,
            "application_status": "interviewing",
            "remote_status": "onsite",
            "domain_tags": ["developer-tools", "infrastructure", "startup"]
        }
    ]
    
    async with get_db_session() as session:
        job_repo = JobRepository(session)
        created_jobs = []
        
        for job_data in jobs_data:
            try:
                job = await job_repo.create(job_data)
                created_jobs.append(job)
                logger.info(f"Created sample job: {job.title}")
            except Exception as e:
                logger.error(f"Failed to create sample job: {e}")
        
        return created_jobs


async def create_sample_resume_versions() -> list[ResumeVersion]:
    """Create sample resume versions."""
    resumes_data = [
        {
            "name": "Product Manager Resume - SaaS Focus",
            "file_path": "/resumes/pm_saas_resume.pdf",
            "file_type": "pdf",
            "raw_text": "John Doe - Senior Product Manager with 8 years of experience in SaaS products...",
            "formatted_content": "<h1>John Doe</h1><p>Senior Product Manager</p>",
            "target_job_title": "Product Manager",
            "target_keywords": ["product management", "saas", "b2b"],
            "usage_count": 5,
            "response_rate": 0.4,
            "interview_rate": 0.2,
            "resume_score": 88.5,
            "skill_matches": {"product management": 0.95, "saas": 0.9, "b2b": 0.85},
            "experience_years": 8.0,
            "is_active": True,
            "is_primary": True,
            "notes": "Best resume for SaaS PM roles"
        },
        {
            "name": "Technical PM Resume - AI/ML Focus",
            "file_path": "/resumes/tech_pm_ai_resume.pdf",
            "file_type": "pdf",
            "raw_text": "John Doe - Technical Product Manager with AI/ML experience...",
            "formatted_content": "<h1>John Doe</h1><p>Technical Product Manager</p>",
            "target_job_title": "Technical Product Manager",
            "target_keywords": ["technical", "ai", "ml", "data"],
            "usage_count": 2,
            "response_rate": 0.5,
            "interview_rate": 0.25,
            "resume_score": 82.3,
            "skill_matches": {"technical": 0.85, "ai": 0.8, "ml": 0.75},
            "experience_years": 6.0,
            "is_active": True,
            "is_primary": False,
            "notes": "Good for technical PM roles"
        }
    ]
    
    async with get_db_session() as session:
        resume_repo = ResumeVersionRepository(session)
        created_resumes = []
        
        for resume_data in resumes_data:
            try:
                resume = await resume_repo.create(resume_data)
                created_resumes.append(resume)
                logger.info(f"Created sample resume: {resume.name}")
            except Exception as e:
                logger.error(f"Failed to create sample resume: {e}")
        
        return created_resumes


async def create_sample_applications(jobs: list[Job], resumes: list[ResumeVersion]) -> list[Application]:
    """Create sample application records."""
    if not jobs or not resumes:
        return []
    
    applications_data = [
        {
            "job_id": jobs[1].id,  # DataTech Inc job
            "status": "submitted",
            "applied_at": datetime.utcnow() - timedelta(days=2),
            "cover_letter": "I'm excited about the opportunity to join DataTech's AI/ML team...",
            "resume_version_id": resumes[1].id,  # AI/ML resume
            "application_score": 85.0,
            "response_probability": 0.7,
            "notes": "Strong match for AI/ML role"
        },
        {
            "job_id": jobs[2].id,  # StartupXYZ job
            "status": "interviewing",
            "applied_at": datetime.utcnow() - timedelta(days=4),
            "cover_letter": "As a technical product manager with startup experience...",
            "resume_version_id": resumes[0].id,  # SaaS resume
            "application_score": 78.5,
            "response_probability": 0.6,
            "interview_stages": [
                {"stage": "Phone Screen", "date": (datetime.utcnow() - timedelta(days=2)).isoformat(), "status": "completed"},
                {"stage": "Technical Interview", "date": (datetime.utcnow() - timedelta(days=1)).isoformat(), "status": "completed"},
                {"stage": "Final Round", "date": (datetime.utcnow() + timedelta(days=1)).isoformat(), "status": "scheduled"}
            ],
            "next_interview_date": datetime.utcnow() + timedelta(days=1),
            "notes": "Good fit for startup environment"
        }
    ]
    
    async with get_db_session() as session:
        app_repo = ApplicationRepository(session)
        created_apps = []
        
        for app_data in applications_data:
            try:
                app = await app_repo.create(app_data)
                created_apps.append(app)
                logger.info(f"Created sample application for job: {app_data['job_id']}")
            except Exception as e:
                logger.error(f"Failed to create sample application: {e}")
        
        return created_apps


async def create_sample_outreach(jobs: list[Job]) -> list[Outreach]:
    """Create sample outreach records."""
    outreach_data = [
        {
            "job_id": jobs[0].id,  # TechCorp job
            "contact_name": "Sarah Johnson",
            "contact_email": "sarah.j@techcorp.com",
            "contact_company": "TechCorp",
            "contact_role": "Hiring Manager",
            "contact_linkedin": "https://linkedin.com/in/sarahjohnson",
            "outreach_type": "email",
            "subject": "Product Manager Opportunity",
            "message_content": "Hi Sarah, I came across the Senior Product Manager position at TechCorp...",
            "status": "sent",
            "sent_at": datetime.utcnow() - timedelta(days=1),
            "outreach_score": 82.0,
            "response_probability": 0.6,
            "notes": "Warm introduction through mutual connection"
        },
        {
            "contact_name": "Mike Chen",
            "contact_email": "mike.chen@startupxyz.com",
            "contact_company": "StartupXYZ",
            "contact_role": "CTO",
            "contact_linkedin": "https://linkedin.com/in/mikechen",
            "outreach_type": "linkedin",
            "subject": "Technical PM Role",
            "message_content": "Hi Mike, I noticed your company is looking for a Technical Product Manager...",
            "status": "replied",
            "sent_at": datetime.utcnow() - timedelta(days=3),
            "replied_at": datetime.utcnow() - timedelta(days=2),
            "response_content": "Thanks for reaching out! Let's schedule a call to discuss...",
            "response_sentiment": "positive",
            "outreach_score": 88.5,
            "response_probability": 0.8,
            "notes": "Positive response, interested in technical background"
        }
    ]
    
    async with get_db_session() as session:
        outreach_repo = OutreachRepository(session)
        created_outreach = []
        
        for outreach_data in outreach_data:
            try:
                outreach = await outreach_repo.create(outreach_data)
                created_outreach.append(outreach)
                logger.info(f"Created sample outreach to: {outreach_data['contact_name']}")
            except Exception as e:
                logger.error(f"Failed to create sample outreach: {e}")
        
        return created_outreach


async def create_sample_scoring_logs(jobs: list[Job], applications: list[Application], resumes: list[ResumeVersion]) -> list[ScoringLog]:
    """Create sample scoring logs."""
    if not jobs or not resumes:
        return []
    
    scoring_data = [
        {
            "job_id": jobs[0].id,
            "scoring_type": "job_match",
            "model_version": "v1.2.0",
            "overall_score": 85.5,
            "sub_scores": {"skills_match": 90.0, "experience_match": 85.0, "location_match": 80.0},
            "features": {"years_experience": 8, "relevant_skills": 15, "industry_match": True},
            "reasoning": "Strong match due to 8 years of PM experience and SaaS background",
            "confidence": 0.92,
            "processing_time_ms": 1250,
            "token_usage": 450,
            "is_successful": True
        },
        {
            "resume_version_id": resumes[0].id,
            "scoring_type": "resume_quality",
            "model_version": "v1.2.0",
            "overall_score": 88.5,
            "sub_scores": {"structure": 90.0, "content": 88.0, "keywords": 87.0},
            "features": {"word_count": 450, "sections": 6, "action_verbs": 25},
            "reasoning": "Well-structured resume with strong action verbs and relevant keywords",
            "confidence": 0.95,
            "processing_time_ms": 890,
            "token_usage": 320,
            "is_successful": True
        },
        {
            "application_id": applications[0].id if applications else None,
            "scoring_type": "application_success",
            "model_version": "v1.2.0",
            "overall_score": 85.0,
            "sub_scores": {"resume_match": 88.0, "cover_letter": 82.0, "timing": 85.0},
            "features": {"resume_score": 88.5, "cover_letter_length": 150, "days_since_posted": 2},
            "reasoning": "Good match with strong resume and timely application",
            "confidence": 0.88,
            "processing_time_ms": 670,
            "token_usage": 280,
            "is_successful": True,
            "user_rating": 4,
            "user_feedback": "Accurate assessment of my qualifications"
        }
    ]
    
    async with get_db_session() as session:
        scoring_repo = ScoringLogRepository(session)
        created_logs = []
        
        for score_data in scoring_data:
            try:
                log = await scoring_repo.create(score_data)
                created_logs.append(log)
                logger.info(f"Created sample scoring log: {score_data['scoring_type']}")
            except Exception as e:
                logger.error(f"Failed to create sample scoring log: {e}")
        
        return created_logs


async def seed_database():
    """Seed the database with sample data."""
    try:
        logger.info("Starting database seeding...")
        
        # Create sample data in order
        jobs = await create_sample_jobs()
        resumes = await create_sample_resume_versions()
        applications = await create_sample_applications(jobs, resumes)
        outreach = await create_sample_outreach(jobs)
        scoring_logs = await create_sample_scoring_logs(jobs, applications, resumes)
        
        logger.info(f"Database seeding completed:")
        logger.info(f"- Created {len(jobs)} jobs")
        logger.info(f"- Created {len(resumes)} resume versions")
        logger.info(f"- Created {len(applications)} applications")
        logger.info(f"- Created {len(outreach)} outreach activities")
        logger.info(f"- Created {len(scoring_logs)} scoring logs")
        
        return {
            "jobs": len(jobs),
            "resumes": len(resumes),
            "applications": len(applications),
            "outreach": len(outreach),
            "scoring_logs": len(scoring_logs)
        }
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise


async def clear_database():
    """Clear all data from database (use with caution)."""
    try:
        logger.warning("Clearing database...")
        
        async with get_db_session() as session:
            # Delete in order of dependencies
            await session.execute(text("DELETE FROM scoring_logs"))
            await session.execute(text("DELETE FROM outreach"))
            await session.execute(text("DELETE FROM applications"))
            await session.execute(text("DELETE FROM resume_versions"))
            await session.execute(text("DELETE FROM jobs"))
            await session.commit()
        
        logger.info("Database cleared successfully")
    except Exception as e:
        logger.error(f"Failed to clear database: {e}")
        raise


if __name__ == "__main__":
    """Run seed script directly."""
    import asyncio
    
    async def main():
        await seed_database()
    
    asyncio.run(main())
