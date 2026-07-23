"""Career pages fetcher that reads from the TargetCompany database."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.fetchers.base import BaseFetcher
from app.schemas.job import JobCreate
from app.core.logging import logger
from app.database.session import get_db_session
from app.models.target_company import TargetCompany
from sqlalchemy.future import select

# We reuse existing ATS fetchers
from app.services.fetchers.greenhouse import GreenhouseFetcher
from app.services.fetchers.lever import LeverFetcher


class CareerPagesFetcher(BaseFetcher):
    """Fetches jobs from dynamically discovered career pages in DB."""
    
    def __init__(self):
        super().__init__("CareerPages")
        self.greenhouse = GreenhouseFetcher()
        self.lever = LeverFetcher()
        self.logger = logger.bind(service="career_pages_fetcher")
        
    async def validate_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        """Validate job data (pass-through for already validated jobs)."""
        if isinstance(job_data, JobCreate):
            return job_data
        try:
            return JobCreate(**job_data)
        except Exception:
            self.logger.debug("Validation failed in CareerPagesFetcher")
            return None
        
    async def fetch_jobs(
        self,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[JobCreate]:
        """Fetch jobs from target companies."""
        
        self.logger.info("Starting CareerPages fetch from DB targets")
        
        target_companies = await self._get_target_companies()
        if not target_companies:
            self.logger.warning("No target companies found in DB")
            return []
            
        all_jobs = []
        
        for company in target_companies:
            try:
                jobs = await self._fetch_from_company(company, filters)
                all_jobs.extend(jobs)
                
                # Update last scraped timestamp
                await self._update_last_scraped(company.id)
                
                if len(all_jobs) >= limit:
                    break
            except Exception as e:
                self.logger.error(f"Failed fetching from {company.name}: {e}")
                
        return all_jobs[:limit]
        
    async def _get_target_companies(self) -> List[TargetCompany]:
        """Get active target companies from DB."""
        async with get_db_session() as session:
            stmt = select(TargetCompany).where(TargetCompany.is_active == True)
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
    async def _update_last_scraped(self, company_id: str) -> None:
        """Update last_scraped_at for a company."""
        async with get_db_session() as session:
            stmt = select(TargetCompany).where(TargetCompany.id == company_id)
            result = await session.execute(stmt)
            company = result.scalars().first()
            if company:
                company.last_scraped_at = datetime.utcnow()
                await session.commit()
                
    async def _fetch_from_company(self, company: TargetCompany, filters: Dict[str, Any]) -> List[JobCreate]:
        """Route to appropriate ATS fetcher."""
        jobs = []
        
        # If the URL is explicitly an ATS link, we can extract the board token
        board_token = company.careers_url.rstrip('/').split('/')[-1] if company.careers_url else company.domain.split('.')[0]
        
        if company.ats_provider == "greenhouse":
            # Temporary override of greenhouse company_boards
            self.greenhouse.company_boards = [board_token]
            jobs = await self.greenhouse.fetch_jobs(limit=20, filters=filters)
            
        elif company.ats_provider == "lever":
            # Lever fetcher usually iterates known boards, we'd add this board
            self.lever.company_boards = [board_token]
            jobs = await self.lever.fetch_jobs(limit=20, filters=filters)
            
        else:
            self.logger.debug(f"Unsupported ATS provider {company.ats_provider} for {company.name}")
            
        # Ensure company name matches DB and enforce Remote
        for job in jobs:
            if hasattr(job, 'company'):
                job.company = company.name
                job.remote_status = "remote"
            elif isinstance(job, dict):
                job['company'] = company.name
                job['remote_status'] = "remote"
                
        return jobs
