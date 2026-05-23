"""Application workflow coordinator for persistence and tracking."""

import json
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Application, ResumeVersion
from app.repositories.application import ApplicationRepository
from app.repositories.resume_version import ResumeVersionRepository
from app.core.logging import logger


class ApplicationWorkflow:
    """Directs pipeline interactions saving states, storing variants, and moving statuses."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.app_repo = ApplicationRepository(session)
        self.resume_repo = ResumeVersionRepository(session)
        self.logger = logger.bind(service="application_workflow")

    async def record_master_resume(self, parsed_data: Dict[str, Any], file_path: str) -> Optional[ResumeVersion]:
        """Register parsed master resume in persistence schema."""
        try:
            # Format experience as primary readable structure
            formatted = ""
            sections = parsed_data.get("sections", {})
            for s_title, s_content in sections.items():
                formatted += f"--- {s_title.upper()} ---\n{s_content}\n\n"
                
            version_data = {
                "name": "Master Resume",
                "file_path": file_path,
                "file_type": file_path.split(".")[-1] if "." in file_path else "txt",
                "raw_text": parsed_data.get("raw_text", ""),
                "formatted_content": formatted,
                "is_primary": True,
                "is_active": True,
                "experience_years": float(parsed_data.get("years_experience") or 3.0),
                "skill_matches": parsed_data.get("skills", []),
                "notes": "Extracted via ingestion layer."
            }
            
            added = await self.resume_repo.create(version_data)
            
            self.logger.info("Successfully persisted Master Resume version.")
            return added
            
        except Exception as e:
            self.logger.error(f"Failed recording master resume: {e}")
            return None

    async def initialize_application(self, job_id: UUID, resume_id: Optional[UUID] = None) -> Optional[Application]:
        """Stage an opportunity in the 'draft' tracking status."""
        try:
            # Check if application for this job already exists
            existing = await self.app_repo.get_by_job_id(job_id)
            if existing:
                self.logger.info(f"Application record already exists for job {job_id}")
                return existing[0]
                
            app_data = {
                "job_id": job_id,
                "status": "draft",
                "resume_version_id": resume_id,
                "tags": ["saved"]
            }
            
            added = await self.app_repo.create(app_data)
            return added
            
        except Exception as e:
            self.logger.error(f"Failed initializing application: {e}")
            return None

    async def transition_status(self, app_id: UUID, new_status: str, notes: Optional[str] = None) -> Optional[Application]:
        """Move tracking token across valid status pipeline states."""
        valid_states = ["draft", "applied", "recruiter_reached", "interview", "rejected", "ghosted", "offered"]
        
        if new_status not in valid_states:
            self.logger.error(f"Invalid status transition target: {new_status}")
            return None
            
        try:
            app = await self.app_repo.get_by_id(app_id)
            if not app:
                return None
                
            app.status = new_status
            
            if new_status == "applied" and not app.applied_at:
                app.applied_at = datetime.utcnow()
                
            if notes:
                existing_notes = app.notes or ""
                app.notes = f"{existing_notes}\n[{datetime.utcnow().strftime('%Y-%m-%d')}] status update to {new_status}: {notes}"
                
            await self.session.commit()
            await self.session.refresh(app)
            return app
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Transition crash: {e}")
            return None
            
    async def get_pipeline_summary(self) -> Dict[str, int]:
        """Provide count matrices across current application funnels."""
        summary = {}
        states = ["draft", "applied", "recruiter_reached", "interview", "rejected", "ghosted"]
        for state in states:
            recs = await self.app_repo.get_by_status(state)
            summary[state] = len(recs)
        return summary
