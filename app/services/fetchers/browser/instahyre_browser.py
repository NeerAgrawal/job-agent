"""Instahyre browser fetcher with authentication support."""

import asyncio
import os
from typing import Dict, Any, List
from datetime import datetime

from app.core.logging import logger
from .base_browser_fetcher import BaseBrowserFetcher
from .browser_utils import BrowserUtils


class InstahyreBrowserFetcher(BaseBrowserFetcher):
    """Instahyre browser fetcher with authentication and PM job extraction."""
    
    def __init__(self):
        super().__init__(name="instahyre_browser", base_url="https://www.instahyre.com")
        self.utils = BrowserUtils()
        self.login_url = "https://www.instahyre.com/login"
        self.jobs_url = "https://www.instahyre.com/jobs"
        
        # Environment variables for authentication
        self.email = os.getenv("INSTAHYRE_EMAIL", "")
        self.password = os.getenv("INSTAHYRE_PASSWORD", "")
        
        if not self.email or not self.password:
            self.logger.warning("Instahyre credentials not found in environment variables")
    
    async def _login(self, page) -> bool:
        """Perform login flow for Instahyre."""
        try:
            if not self.email or not self.password:
                self.logger.error("Instahyre credentials not configured")
                return False
            
            self.logger.info("Starting Instahyre login flow")
            
            # Navigate to login page
            await page.goto(self.login_url, timeout=self.navigation_timeout)
            await self._wait_for_page_load(page)
            
            # Fill email
            email_filled = await self._safe_type(page, 'input[type="email"]', self.email)
            if not email_filled:
                self.logger.error("Failed to fill email field")
                return False
            
            # Fill password
            password_filled = await self._safe_type(page, 'input[type="password"]', self.password)
            if not password_filled:
                self.logger.error("Failed to fill password field")
                return False
            
            # Click login button
            login_clicked = await self._safe_click(page, 'button[type="submit"]')
            if not login_clicked:
                # Try alternative login button
                login_clicked = await self._safe_click(page, 'input[type="submit"]')
            
            if not login_clicked:
                self.logger.error("Failed to click login button")
                return False
            
            # Wait for login to complete
            await asyncio.sleep(3)
            
            # Check if login was successful
            login_success = await self._verify_login_success(page)
            if not login_success:
                self.logger.error("Login verification failed")
                return False
            
            self.logger.info("Instahyre login successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Instahyre login failed: {e}")
            return False
    
    async def _verify_login_success(self, page) -> bool:
        """Verify that login was successful."""
        try:
            # Check for login success indicators
            success_indicators = [
                '.dashboard',
                '.user-profile',
                '[data-testid="user-menu"]',
                'a[href*="logout"]',
                'a[href*="profile"]'
            ]
            
            for indicator in success_indicators:
                element = await self._safe_wait_for_selector(page, indicator, timeout=5000)
                if element:
                    return True
            
            # Check if we're still on login page
            current_url = page.url
            if 'login' in current_url.lower():
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Login verification failed: {e}")
            return False
    
    async def _navigate_to_jobs(self, page, filters: Dict[str, Any]) -> None:
        """Navigate to job listings page."""
        try:
            self.logger.info("Navigating to Instahyre jobs page")
            
            # Navigate to jobs page
            await page.goto(self.jobs_url, timeout=self.navigation_timeout)
            await self._wait_for_page_load(page)
            
            # Wait for job listings to load
            await asyncio.sleep(2)
            
            # Apply filters if provided
            if filters:
                await self._apply_filters(page, filters)
            
            self.logger.info("Successfully navigated to jobs page")
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to jobs page: {e}")
            raise
    
    async def _apply_filters(self, page, filters: Dict[str, Any]) -> None:
        """Apply search filters to job listings."""
        try:
            # Search for PM roles
            if 'keywords' in filters:
                search_input = await self._safe_wait_for_selector(page, 'input[placeholder*="search" i]', timeout=5000)
                if search_input:
                    await search_input.clear()
                    await search_input.type(filters['keywords'])
                    await asyncio.sleep(1)
                    
                    # Click search button
                    search_button = await self._safe_wait_for_selector(page, 'button[type="submit"], button:has-text("Search")', timeout=3000)
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
            self.logger.debug(f"Failed to apply filters: {e}")
    
    async def _extract_jobs(self, page, limit: int) -> List[Dict[str, Any]]:
        """Extract job listings from the page."""
        try:
            self.logger.info(f"Extracting up to {limit} jobs from Instahyre")
            
            jobs = []
            
            # Wait for job listings to appear
            await self.utils.wait_for_content(page, timeout=10000)
            
            # Try multiple selectors for job listings
            job_selectors = [
                '.job-card',
                '.job-listing',
                '.job-item',
                'article.job',
                '[data-testid="job-card"]',
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
                self.logger.warning("No job elements found on page")
                return jobs
            
            self.logger.info(f"Found {len(job_elements)} job elements")
            
            # Extract jobs from elements
            for i, element in enumerate(job_elements[:limit]):
                try:
                    job_data = await self._extract_job_from_element(element)
                    if job_data:
                        jobs.append(job_data)
                        self.logger.debug(f"Extracted job {i+1}: {job_data['title']}")
                except Exception as e:
                    self.logger.debug(f"Failed to extract job {i+1}: {e}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(jobs)} jobs from Instahyre")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Failed to extract jobs: {e}")
            return []
    
    async def _extract_job_from_element(self, element) -> Dict[str, Any]:
        """Extract job data from a job element."""
        try:
            # Extract title
            title_element = await element.query_selector('h1, h2, h3, h4, .title, .job-title')
            title = await self.utils.extract_text_safely(title_element) if title_element else ""
            
            if not title:
                return None
            
            # Filter by PM role
            if not self.utils.is_pm_role(title) or self.utils.is_reject_role(title):
                return None
            
            # Extract company
            company_element = await element.query_selector('.company, .company-name, .employer')
            company = await self.utils.extract_text_safely(company_element) if company_element else "Unknown"
            
            # Extract location
            location_element = await element.query_selector('.location, .job-location, .place')
            location = await self.utils.extract_text_safely(location_element) if location_element else "Not specified"
            
            # Extract salary
            salary_element = await element.query_selector('.salary, .compensation, .pay')
            salary = await self.utils.extract_text_safely(salary_element) if salary_element else "Not specified"
            salary = self.utils.normalize_salary(salary)
            
            # Extract description
            desc_element = await element.query_selector('.description, .job-description, .details')
            description = await self.utils.extract_text_safely(desc_element) if desc_element else ""
            
            # Extract URL
            url_element = await element.query_selector('a[href]')
            url = await self.utils.extract_url_safely(url_element) if url_element else ""
            
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
                'source': 'instahyre_browser',
                'posted_at': datetime.utcnow().isoformat(),
                'raw_metadata': {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'source': 'instahyre_browser',
                    'extraction_method': 'browser'
                }
            }
            
            return job_data
            
        except Exception as e:
            self.logger.debug(f"Failed to extract job from element: {e}")
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
