"""Lever job fetcher implementation."""

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


class LeverFetcher(BaseFetcher):
    """Lever job board fetcher."""
    
    def __init__(self):
        super().__init__("Lever")
        self.base_url = "https://api.lever.co/v0/postings"
        self.session = None
        self.rate_limiter = asyncio.Semaphore(10)  # 10 concurrent requests
        
    async def fetch_jobs(
        self, 
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[JobResponse]:
        """Fetch jobs from Lever."""
        self._log_info("Starting Lever job fetch", limit=limit, filters=filters)
        
        try:
            await self._ensure_session()
            
            # Get all postings (Lever doesn't have public search API)
            postings = await self._get_all_postings()
            
            if not postings:
                self._log_error("No postings found from Lever")
                return []
            
            # Parse and normalize jobs
            jobs = []
            for posting in postings:
                normalized_job = await self.validate_job(posting)
                if normalized_job:
                    jobs.append(normalized_job)
                else:
                    self._log_warning(f"Skipping invalid job: {posting}")
            
            # Apply filters
            filtered_jobs = self._apply_filters(jobs, filters)
            
            # Limit results
            limited_jobs = filtered_jobs[:limit]
            
            # Save to database
            if limited_jobs:
                await self._save_jobs(limited_jobs)
                self._log_info(f"Saved {len(limited_jobs)} jobs to database")
            else:
                self._log_warning("No valid jobs to save")
            
            # Get statistics
            stats = await self.get_fetch_statistics()
            self._log_info(f"Fetch statistics: {stats}")
            
            return [JobResponse(**job.__dict__) for job in limited_jobs]
            
        except Exception as e:
            self._log_error(f"Lever fetch failed: {e}")
            return []
    
    async def _get_all_postings(self) -> List[Dict[str, Any]]:
        """Get all postings from Lever companies."""
        # Common Lever company URLs (PM-focused)
        companies = [
            "https://jobs.lever.co/airbnb",
            "https://jobs.lever.co/spotify", 
            "https://jobs.lever.co/uber",
            "https://jobs.lever.co/lyft",
            "https://jobs.lever.co/coinbase",
            "https://jobs.lever.co/stripe",
            "https://jobs.lever.co/figma",
            "https://jobs.lever.co/notion",
            "https://jobs.lever.co/segment",
            "https://jobs.lever.co/carta",
            "https://jobs.lever.co/robinhood"
        ]
        
        all_postings = []
        
        for company_url in companies:
            postings = await self._fetch_company_postings(company_url)
            all_postings.extend(postings)
        
        return all_postings
    
    async def _fetch_company_postings(self, company_url: str) -> List[Dict[str, Any]]:
        """Fetch postings from a specific Lever company."""
        headers = {
            "User-Agent": "JobAI-Agent/1.0",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                async with self.rate_limiter:
                    response = await client.get(
                        company_url,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("data", [])
                    else:
                        self._log_error(f"API request failed: {response.status_code}", response=response.text)
                        return []
        
        except httpx.TimeoutException:
            self._log_error("Request timeout")
            return []
        except Exception as e:
            self._log_error(f"Request error: {e}")
            return []
    
    def _apply_filters(self, jobs: List[Dict[str, Any]], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply filters to job list."""
        if not filters:
            return jobs
        
        filtered_jobs = jobs
        
        # Search filter
        if filters.get("search"):
            search_term = filters["search"].lower()
            filtered_jobs = [
                job for job in filtered_jobs
                if search_term in job.get("title", "").lower() or 
                   search_term in job.get("company", "").lower() or
                   search_term in job.get("jd_text", "").lower()
            ]
        
        # Company filter
        if filters.get("company"):
            company_filter = filters["company"].lower()
            filtered_jobs = [
                job for job in filtered_jobs
                if company_filter in job.get("company", "").lower()
            ]
        
        # Location filter
        if filters.get("location"):
            location_filter = filters["location"].lower()
            filtered_jobs = [
                job for job in filtered_jobs
                if location_filter in job.get("location", "").lower()
            ]
        
        # Remote status filter
        if filters.get("remote_status"):
            remote_filter = filters["remote_status"].lower()
            filtered_jobs = [
                job for job in filtered_jobs
                if job.get("remote_status", "").lower() == remote_filter
            ]
        
        # Salary filter
        if filters.get("min_salary"):
            min_salary = filters["min_salary"]
            filtered_jobs = [
                job for job in filtered_jobs
                if job.get("salary", 0) >= min_salary
            ]
        
        if filters.get("max_salary"):
            max_salary = filters["max_salary"]
            filtered_jobs = [
                job for job in filtered_jobs
                if job.get("salary", float('inf')) <= max_salary
            ]
        
        # Posted date filter
        if filters.get("posted_after"):
            posted_after = filters["posted_after"]
            filtered_jobs = [
                job for job in filtered_jobs
                if job.get("posted_at") and job.get("posted_at") >= posted_after
            ]
        
        return filtered_jobs
    
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
        """Get fetch statistics for Lever."""
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
            # Extract basic job information
            title = job_data.get("text", "").split("\n")[0].strip()  # First line is usually title
            company = self._extract_company_from_url(job_data.get("applyUrl", ""))
            location = job_data.get("categories", {}).get("location", "")
            salary = self._parse_salary_from_text(job_data.get("description", ""))
            
            # Create job dictionary
            job_dict = {
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "source": "Lever",
                "job_url": job_data.get("applyUrl", ""),
                "posted_at": self._parse_datetime(job_data.get("createdAt", "")),
                "jd_text": job_data.get("description", ""),
                "applicant_count": 0,
                "remote_status": self._determine_remote_status(job_data),
                "domain_tags": self._extract_domain_tags(job_data.get("description", "")),
                "raw_metadata": job_data
            }
            
            # Validate with Pydantic
            job = JobCreate(**job_dict)
            return job
            
        except Exception as e:
            self._log_error(f"Job validation failed: {e}")
            return None
    
    def _extract_company_from_url(self, apply_url: str) -> str:
        """Extract company name from apply URL."""
        if not apply_url:
            return ""
        
        # Parse URL to get company name
        parsed = urlparse(apply_url)
        path_parts = parsed.path.split('/')
        
        # Look for company name in path
        for part in path_parts:
            if part and part != "postings" and len(part) > 2:
                return part.replace("-", " ").title()
        
        return ""
    
    def _parse_salary_from_text(self, description: str) -> Optional[float]:
        """Parse salary from job description text."""
        if not description:
            return None
        
        description_lower = description.lower()
        
        # Look for salary patterns
        import re
        
        # $X - $Y patterns
        salary_pattern = r'\$(\d+(?:,\d{3})*)\s*[-–—]\s*\$(\d+(?:,\d{3})*)'
        match = re.search(salary_pattern, description_lower)
        
        if match:
            try:
                min_salary = float(match.group(1).replace(',', ''))
                max_salary = float(match.group(2).replace(',', '')) if match.group(2) else None
                return min_salary  # Return minimum salary
            except ValueError:
                pass
        
        return None
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not date_str:
            return None
        
        try:
            # Handle different datetime formats
            if date_str.endswith('Z'):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(date_str)
        except ValueError:
            self._log_warning(f"Invalid datetime format: {date_str}")
            return None
    
    def _determine_remote_status(self, job_data: Dict[str, Any]) -> str:
        """Determine remote status from job data."""
        description = job_data.get("description", "").lower()
        location = job_data.get("categories", {}).get("location", "").lower()
        
        if "remote" in location or "work from home" in description or "remote-friendly" in description:
            return "remote"
        elif "hybrid" in location or "hybrid-friendly" in description:
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
