"""Greenhouse job fetcher implementation."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import httpx

from app.services.fetchers.base import BaseFetcher
from app.schemas.job import JobCreate, JobResponse
from app.database.repositories import JobRepository
from app.database.session import get_db_session
from app.core.logging import logger


class GreenhouseFetcher(BaseFetcher):
    """Greenhouse job board fetcher."""
    
    def __init__(self):
        super().__init__("Greenhouse")
        self.base_url = "https://boards.greenhouse.io"
        self.api_url = f"{self.base_url}/workable-jobs/v1"
        self.session = None
        self.rate_limiter = asyncio.Semaphore(10)  # 10 concurrent requests
        
    async def fetch_jobs(
        self, 
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0
    ) -> List[JobResponse]:
        """Fetch jobs from Greenhouse."""
        self._log_info("Starting Greenhouse job fetch", limit=limit, filters=filters)
        
        try:
            await self._ensure_session()
            
            # Build API request
            params = self._build_api_params(filters, limit)
            
            # Make API request
            jobs_data = await self._make_request(params)
            
            if not jobs_data:
                self._log_error("No jobs data received from Greenhouse", params=params)
                return []
            
            # Parse and normalize jobs
            jobs = self._parse_jobs_response(jobs_data)
            normalized_jobs = []
            
            for job_data in jobs:
                normalized_job = await self.validate_job(job_data)
                if normalized_job:
                    normalized_jobs.append(normalized_job)
                else:
                    self._log_warning(f"Skipping invalid job: {job_data}")
            
            # Save to database
            if normalized_jobs:
                await self._save_jobs(normalized_jobs)
                self._log_info(f"Saved {len(normalized_jobs)} jobs to database")
            else:
                self._log_warning("No valid jobs to save")
            
            # Get statistics
            stats = await self.get_fetch_statistics()
            self._log_info(f"Fetch statistics: {stats}")
            
            return [JobResponse(**job.__dict__) for job in normalized_jobs]
            
        except Exception as e:
            self._log_error(f"Greenhouse fetch failed: {e}")
            return []
    
    def _build_api_params(self, filters: Optional[Dict[str, Any]], limit: int) -> Dict[str, Any]:
        """Build API parameters for Greenhouse API."""
        params = {
            "limit": min(limit, 100),
            "return": "id,title,company,location,salary,posted_at"
        }
        
        # Add filters
        if filters:
            if filters.get("search"):
                params["query"] = filters["search"]
            
            if filters.get("company"):
                params["company"] = filters["company"]
            
            if filters.get("location"):
                params["location"] = filters["location"]
            
            # Add PM-specific filters
            if filters.get("pm_roles"):
                params["job_types"] = "product,program,project"
            
            if filters.get("remote_only"):
                params["remote"] = True
        
        return params
    
    async def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Greenhouse API."""
        headers = {
            "User-Agent": "JobAI-Agent/1.0",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                async with self.rate_limiter:
                    response = await client.get(
                        self.api_url,
                        params=params,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        self._log_error(f"API request failed: {response.status_code}", response=response.text)
                        return None
        
        except httpx.TimeoutException:
            self._log_error("Request timeout")
            return None
        except Exception as e:
            self._log_error(f"Request error: {e}")
            return None
    
    def _parse_jobs_response(self, jobs_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Greenhouse API response."""
        if not jobs_data or "jobs" not in jobs_data:
            return []
        
        jobs = []
        
        for job in jobs_data.get("jobs", []):
            # Extract basic job information
            job_dict = {
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "salary": self._parse_salary(job.get("compensation", {})),
                "source": "Greenhouse",
                "job_url": job.get("absolute_url", ""),
                "posted_at": self._parse_datetime(job.get("published_at", "")),
                "jd_text": job.get("description", ""),
                "applicant_count": job.get("stats", {}).get("applicant_count", 0),
                "remote_status": self._determine_remote_status(job),
                "domain_tags": self._extract_domain_tags(job.get("description", "")),
                "raw_metadata": job
            }
            
            jobs.append(job_dict)
        
        return jobs
    
    def _parse_salary(self, compensation: Dict[str, Any]) -> Optional[float]:
        """Parse salary from compensation object."""
        if not compensation:
            return None
        
        # Extract salary information
        min_salary = compensation.get("min", {}).get("amount", 0)
        max_salary = compensation.get("max", {}).get("amount", 0)
        currency = compensation.get("currency", {}).get("code", "USD")
        
        if currency == "USD" and min_salary:
            return min_salary
        
        return None
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not date_str:
            return None
        
        try:
            # Handle different datetime formats
            if "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                return datetime.fromisoformat(date_str)
        except ValueError:
            self._log_warning(f"Invalid datetime format: {date_str}")
            return None
    
    def _determine_remote_status(self, job: Dict[str, Any]) -> str:
        """Determine remote status from job data."""
        location = job.get("location", "").lower()
        description = job.get("description", "").lower()
        
        if "remote" in location or "remote" in description or "work from home" in description:
            return "remote"
        elif "hybrid" in location or "hybrid" in description:
            return "hybrid"
        else:
            return "onsite"
    
    def _extract_domain_tags(self, description: str) -> List[str]:
        """Extract domain tags from job description."""
        if not description:
            return []
        
        # Common PM domains
        pm_domains = [
            "product management", "saas", "b2b", "analytics", "marketing",
            "technical", "engineering", "development", "api", "platform",
            "ai", "machine learning", "data", "infrastructure", "devops",
            "strategy", "operations", "finance", "business", "growth"
        ]
        
        # Extract tags based on keywords
        tags = []
        description_lower = description.lower()
        
        for domain in pm_domains:
            if any(keyword in description_lower for keyword in domain.split()):
                tags.append(domain)
        
        # Remove duplicates
        return list(set(tags))
    
    async def _ensure_session(self):
        """Ensure database session is available."""
        if not self.session:
            self.session = await get_db_session()
    
    async def _save_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """Save jobs to database."""
        if not jobs:
            return 0
        
        await self._ensure_session()
        job_repo = JobRepository(self.session)
        
        saved_count = 0
        for job_data in jobs:
            try:
                job_create = JobCreate(**job_data)
                job = await job_repo.create(job_create.dict())
                saved_count += 1
                self._log_debug(f"Saved job: {job.title}")
            except Exception as e:
                self._log_error(f"Failed to save job: {e}")
        
        return saved_count
    
    async def get_fetch_statistics(self) -> Dict[str, Any]:
        """Get fetch statistics for Greenhouse."""
        await self._ensure_session()
        job_repo = JobRepository(self.session)
        
        try:
            total_jobs = await job_repo.count()
            recent_jobs = await job_repo.get_recent_jobs(days=7)
            
            return {
                "total_fetched": total_jobs,
                "recent_jobs": len(recent_jobs),
                "last_fetch": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self._log_error(f"Failed to get statistics: {e}")
            return {}
    
    async def validate_job(self, job_data: Dict[str, Any]) -> Optional[JobCreate]:
        """Validate and normalize job data."""
        try:
            # Create Pydantic model for validation
            job = JobCreate(**job_data)
            
            # Validate required fields
            if not job.title or not job.company:
                raise ValueError("Title and company are required")
            
            # Normalize data
            job.title = self._normalize_title(job.title)
            job.company = self._normalize_company(job.company)
            job.location = self._normalize_location(job.location)
            
            return job
        except Exception as e:
            self._log_error(f"Job validation failed: {e}")
            return None
