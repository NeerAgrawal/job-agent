"""Cutshort browser fetcher as fallback for JS-rendered content."""

import asyncio
from typing import Dict, Any, List
from datetime import datetime

from app.core.logging import logger
from .base_browser_fetcher import BaseBrowserFetcher
from .browser_utils import BrowserUtils


class CutshortBrowserFetcher(BaseBrowserFetcher):
    """Cutshort browser fetcher for JS-rendered job extraction."""
    
    def __init__(self):
        super().__init__(name="cutshort_browser", base_url="https://cutshort.io")
        self.utils = BrowserUtils()
        self.jobs_url = "https://cutshort.io/product-manager-jobs"
        
    async def _login(self, page) -> bool:
        """Cutshort doesn't require authentication for basic job search."""
        self.logger.info("Cutshort browser fetcher - no authentication required")
        return True
    
    async def _navigate_to_jobs(self, page, filters: Dict[str, Any]) -> None:
        """Navigate to Cutshort PM job listings."""
        try:
            self.logger.info("Navigating to Cutshort PM jobs page")
            
            # Navigate to PM jobs page
            await page.goto(self.jobs_url, timeout=self.navigation_timeout)
            await self._wait_for_page_load(page)
            
            # Wait for job listings to load
            await asyncio.sleep(3)
            
            # Apply filters if provided
            if filters:
                await self._apply_filters(page, filters)
            
            self.logger.info("Successfully navigated to Cutshort jobs page")
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to Cutshort jobs page: {e}")
            raise
    
    async def _apply_filters(self, page, filters: Dict[str, Any]) -> None:
        """Apply search filters to Cutshort job listings."""
        try:
            # Search for PM roles
            if 'keywords' in filters:
                search_input = await self._safe_wait_for_selector(page, 'input[placeholder*="search" i], input[name="q"]', timeout=5000)
                if search_input:
                    await search_input.clear()
                    await search_input.type(filters['keywords'])
                    await asyncio.sleep(1)
                    
                    # Click search button
                    search_button = await self._safe_wait_for_selector(page, 'button[type="submit"], .search-btn', timeout=3000)
                    if search_button:
                        await search_button.click()
                        await asyncio.sleep(2)
            
            # Filter by location
            if 'location' in filters:
                location_filter = await self._safe_wait_for_selector(page, 'select[name="location"], .location-filter', timeout=3000)
                if location_filter:
                    await location_filter.select_option(filters['location'])
                    await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.debug(f"Failed to apply Cutshort filters: {e}")
    
    async def _extract_jobs(self, page, limit: int) -> List[Dict[str, Any]]:
        """Extract job listings from Cutshort page."""
        try:
            self.logger.info(f"Extracting up to {limit} jobs from Cutshort")
            
            jobs = []
            
            # Wait for job listings to appear
            await self.utils.wait_for_content(page, timeout=10000)
            
            # Try multiple selectors for Cutshort job listings
            job_selectors = [
                '[data-jobid]',
                '.job-card',
                '.job-listing',
                'article.job',
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
                self.logger.warning("No Cutshort job elements found on page")
                return jobs
            
            self.logger.info(f"Found {len(job_elements)} Cutshort job elements")
            
            # Extract jobs from elements
            for i, element in enumerate(job_elements[:limit]):
                try:
                    job_data = await self._extract_job_from_element(element)
                    if job_data:
                        jobs.append(job_data)
                        self.logger.debug(f"Extracted Cutshort job {i+1}: {job_data['title']}")
                except Exception as e:
                    self.logger.debug(f"Failed to extract Cutshort job {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(jobs)} jobs from Cutshort")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Failed to extract Cutshort jobs: {e}")
            return []
    
    async def _extract_job_from_element(self, element) -> Dict[str, Any]:
        """Extract job data from a Cutshort job element."""
        try:
            # Extract title - Cutshort specific selectors
            title_selectors = [
                'h2',
                'h3',
                '.title',
                '.job-title',
                '[data-field="title"]'
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
            
            # Extract company - Cutshort specific
            company_selectors = [
                '.company',
                '.company-name',
                '[data-field="company"]',
                'span[class*="company"]',
                'div[class*="company"]',
                'h3[class*="company"]',
                'p[class*="company"]',
                '[data-company]',
                'a[class*="company"]'
            ]
            
            company = ""
            for selector in company_selectors:
                company_element = await element.query_selector(selector)
                if company_element:
                    company = await self._safe_extract_text(company_element)
                    if company:
                        break
            
            company = company or "Unknown"
            
            # Extract location - Cutshort specific
            location_selectors = [
                '.location',
                '.job-location',
                '[data-field="location"]',
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
            
            # Extract salary - Cutshort specific
            salary_selectors = [
                '.salary',
                '.salary-package',
                '[data-field="salary"]',
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
            
            # Extract description - Cutshort specific
            desc_selectors = [
                '.description',
                '.job-description',
                '[data-field="description"]',
                'div[class*="description"]'
            ]
            
            description = ""
            for selector in desc_selectors:
                desc_element = await element.query_selector(selector)
                if desc_element:
                    description = await self._safe_extract_text(desc_element)
                    if description:
                        break
            
            # Extract URL - Cutshort specific
            url_selectors = [
                'a[href*="job"]',
                'a[href*="position"]',
                '[data-field="url"]'
            ]
            
            url = ""
            for selector in url_selectors:
                url_element = await element.query_selector(selector)
                if url_element:
                    url = await self._safe_extract_url(url_element)
                    if url:
                        break
            
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
                'source': 'cutshort_browser',
                'posted_at': datetime.utcnow().isoformat(),
                'raw_metadata': {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'source': 'cutshort_browser',
                    'extraction_method': 'browser'
                }
            }
            
            return job_data
            
        except Exception as e:
            self.logger.debug(f"Failed to extract Cutshort job from element: {e}")
            return {}
    
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
