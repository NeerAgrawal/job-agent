"""Naukri browser fetcher as fallback for JS-rendered content."""

import asyncio
from typing import Dict, Any, List
from datetime import datetime

from app.core.logging import logger
from .base_browser_fetcher import BaseBrowserFetcher
from .browser_utils import BrowserUtils


class NaukriBrowserFetcher(BaseBrowserFetcher):
    """Naukri browser fetcher for JS-rendered job extraction."""
    
    def __init__(self):
        super().__init__(name="naukri_browser", base_url="https://www.naukri.com")
        self.utils = BrowserUtils()
        self.jobs_url = "https://www.naukri.com/product-manager-jobs"
        
    async def _login(self, page) -> bool:
        """Naukri doesn't require authentication for basic job search."""
        self.logger.info("Naukri browser fetcher - no authentication required")
        return True
    
    async def _navigate_to_jobs(self, page, filters: Dict[str, Any]) -> None:
        """Navigate to Naukri PM job listings."""
        try:
            self.logger.info("Navigating to Naukri PM jobs page")
            
            # Navigate to PM jobs page
            await page.goto(self.jobs_url, timeout=self.navigation_timeout)
            await self._wait_for_page_load(page)
            
            # Wait for job listings to load
            await asyncio.sleep(3)
            
            # Apply filters if provided
            if filters:
                await self._apply_filters(page, filters)
            
            self.logger.info("Successfully navigated to Naukri jobs page")
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to Naukri jobs page: {e}")
            raise
    
    async def _apply_filters(self, page, filters: Dict[str, Any]) -> None:
        """Apply search filters to Naukri job listings."""
        try:
            # Search for PM roles
            if 'keywords' in filters:
                search_input = await self._safe_wait_for_selector(page, 'input[placeholder*="search" i], input[name="keyword"]', timeout=5000)
                if search_input:
                    await search_input.clear()
                    await search_input.type(filters['keywords'])
                    await asyncio.sleep(1)
                    
                    # Click search button
                    search_button = await self._safe_wait_for_selector(page, 'button[type="submit"], .search-btn', timeout=3000)
                    if search_button:
                        await search_button.click()
                        await asyncio.sleep(2)
            
            # Filter by experience level
            if 'experience' in filters:
                exp_filter = await self._safe_wait_for_selector(page, 'select[name="experience"], .exp-filters', timeout=3000)
                if exp_filter:
                    await exp_filter.select_option(filters['experience'])
                    await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.debug(f"Failed to apply Naukri filters: {e}")
    
    async def _extract_jobs(self, page, limit: int) -> List[Dict[str, Any]]:
        """Extract job listings from Naukri page."""
        try:
            self.logger.info(f"Extracting up to {limit} jobs from Naukri")
            
            jobs = []
            
            # Wait for job listings to appear
            await self.utils.wait_for_content(page, timeout=10000)
            
            # Try multiple selectors for Naukri job listings
            job_selectors = [
                '.srp-jobtuple-wrapper',
                '.jobTuple',
                '.job-card',
                '.job-listing',
                'article.job',
                '[data-type="job"]',
                'div[class*="job"]'
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        job_elements = elements
                        break
                except:
                    continue
            
            if not job_elements:
                self.logger.warning("No Naukri job elements found on page")
                return jobs
            
            self.logger.info(f"Found {len(job_elements)} Naukri job elements")
            
            # Extract jobs from elements
            for i, element in enumerate(job_elements[:limit]):
                try:
                    job_data = await self._extract_job_from_element(element)
                    if job_data:
                        jobs.append(job_data)
                        self.logger.debug(f"Extracted Naukri job {i+1}: {job_data['title']}")
                except Exception as e:
                    self.logger.debug(f"Failed to extract Naukri job {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(jobs)} jobs from Naukri")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Failed to extract Naukri jobs: {e}")
            return []
    
    async def _extract_job_from_element(self, element) -> Dict[str, Any]:
        """Extract job data from a Naukri job element."""
        try:
            # Extract title - Naukri specific selectors
            title_selectors = [
                'a.title',
                'h2 a',
                '.job-title a',
                '[data-type="job-title"]'
            ]
            
            title = ""
            for selector in title_selectors:
                title_element = await element.query_selector(selector)
                if title_element:
                    title = await self._safe_extract_text(title_element)
                    if title:
                        break
            
            if not title:
                return None
            
            # Filter by PM role
            if not self.utils.is_pm_role(title) or self.utils.is_reject_role(title):
                return None
            
            # Extract company - Naukri specific
            company_selectors = [
                'a.comp-name',
                '.companyName',
                '.company-name',
                '.company',
                '[data-type="company-name"]',
                'span[class*="company"]'
            ]
            
            company = ""
            for selector in company_selectors:
                company_element = await element.query_selector(selector)
                if company_element:
                    company = await self._safe_extract_text(company_element)
                    if company:
                        break
            
            company = company or "Unknown"
            
            # Extract location - Naukri specific
            location_selectors = [
                '.location',
                '.job-location',
                '[data-type="location"]',
                'span[class*="location"]'
            ]
            
            location = ""
            for selector in location_selectors:
                location_element = await element.query_selector(selector)
                if location_element:
                    location = await self._safe_extract_text(location_element)
                    if location:
                        break
            
            location = location or "Not specified"
            
            # Extract salary - Naukri specific
            salary_selectors = [
                '.sal-wrap',
                '.sal',
                '.salary',
                '.salary-package',
                '[data-type="salary"]',
                'span[class*="salary"]'
            ]
            
            salary = ""
            for selector in salary_selectors:
                salary_element = await element.query_selector(selector)
                if salary_element:
                    salary = await self._safe_extract_text(salary_element)
                    if salary:
                        break
            
            salary = salary or "Not specified"
            salary = self.utils.normalize_salary(salary)
            
            # Extract description - Naukri specific
            desc_selectors = [
                '.job-description',
                '.description',
                '[data-type="description"]',
                'div[class*="description"]'
            ]
            
            description = ""
            for selector in desc_selectors:
                desc_element = await element.query_selector(selector)
                if desc_element:
                    description = await self._safe_extract_text(desc_element)
                    if description:
                        break
            
            # URL extraction
            url_selectors = [
                'a.title',
                'h2 a',
                '.job-title a',
                'a[href*="job"]'
            ]
            
            url = ""
            for selector in url_selectors:
                url_element = await element.query_selector(selector)
                if url_element:
                    url = await self._safe_extract_url(url_element)
                    if url:
                        break
            
            # Fallback: Extract company from URL slug if selectors failed
            if company == "Unknown" and url:
                company = self._extract_company_from_url(url, title) or "Unknown"
            
            # Normalize location
            location = self.utils.normalize_location(location)
            
            # Build job data
            job_data = {
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'job_url': url,
                'jd_text': description,
                'remote_status': self.utils.determine_remote_status(location, description, title),
                'source': 'naukri_browser',
                'posted_at': datetime.utcnow().isoformat(),
                'raw_metadata': {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'source': 'naukri_browser',
                    'extraction_method': 'browser'
                }
            }
            
            return job_data
            
        except Exception as e:
            self.logger.debug(f"Failed to extract Naukri job from element: {e}")
            return {}

    def _extract_company_from_url(self, url: str, title: str) -> str:
        """Fallback helper to extract company name from job url slug."""
        try:
            if not url or 'naukri.com' not in url:
                return ""
            
            path = url.split('/')[-1]
            if not path:
                return ""
                
            slug = path.lower()
            
            if 'job-listings-' in slug:
                slug = slug.replace('job-listings-', '')
            
            title_slug = str(title).lower().replace(' ', '-')
            if title_slug in slug:
                slug = slug.replace(title_slug, '')
            
            for term in ['product-manager', 'technical-product-manager', 'apm', 'program-manager', 'pm']:
                slug = slug.replace(term, '')
            
            import re
            exp_match = re.search(r'-\d+-to-\d+-years(-\d+)?$', slug)
            if exp_match:
                slug = slug[:exp_match.start()]
            else:
                slug = re.sub(r'-\d+$', '', slug)
                slug = re.sub(r'-\d+-to-\d+-years$', '', slug)
            
            common_cities = ['bengaluru', 'bangalore', 'hyderabad', 'noida', 'mumbai', 'pune', 'delhi', 'chennai', 'india', 'gurgaon']
            for city in common_cities:
                slug = re.sub(r'-' + city + r'$', '', slug)
            
            slug = slug.strip('-').replace('-', ' ')
            
            if slug:
                return ' '.join(word.capitalize() for word in slug.split())
        except Exception:
            pass
        return ""
    
    async def _safe_extract_text(self, element) -> str:
        """Safely extract text from element."""
        try:
            if element:
                text = await element.text_content()
                return self.utils.clean_text(text) if text else ""
        except Exception:
            pass
        return ""
    
    async def _safe_extract_url(self, element) -> str:
        """Safely extract URL from element."""
        try:
            if element:
                href = await element.get_attribute('href')
                return href or ""
        except Exception:
            pass
        return ""
