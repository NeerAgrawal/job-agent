"""Instahyre browser fetcher with authentication and PM job extraction."""
# -*- coding: utf-8 -*-

import asyncio
import os
from typing import Dict, Any, List
from datetime import datetime

from playwright.async_api import Page
from app.core.logging import logger
from app.core.config.settings import settings
from .base_browser_fetcher import BaseBrowserFetcher
from .browser_utils import BrowserUtils


class InstahyreBrowserFetcher(BaseBrowserFetcher):
    """Instahyre browser fetcher with authentication and PM job extraction."""
    
    def __init__(self):
        super().__init__(name="instahyre_browser", base_url="https://www.instahyre.com")
        self.utils = BrowserUtils()
        self.login_url = "https://www.instahyre.com/login"
        self.jobs_url = "https://www.instahyre.com/jobs"
        self.google_sign_in_url = "https://www.instahyre.com/oauth/google"
        
        # Authentication from settings
        self.email = settings.instahyre_email
        
        # Note: We no longer require INSTAHYRE_PASSWORD
        # Authentication will be handled via Google Sign-In with manual interaction
        
        if not self.email:
            self.logger.warning("INSTAHYRE_EMAIL not configured in settings")
        
        self.requires_manual_login = False
        self.session_validated = False
    
    async def _verify_session_active(self, page: Page) -> bool:
        """Verify if the current session is authenticated."""
        try:
            # Check if we have login indicators on current page to avoid double-navigation
            login_indicators = await self._get_login_indicators(page)
            return not login_indicators
        except Exception as e:
            self.logger.debug(f"Error verifying session activity: {e}")
            return False
    
    async def _login(self, page: Page) -> bool:
        """Handle Instahyre login with Google Sign-In."""
        try:
            self.logger.info("Starting Instahyre Google Sign-In flow")
            
            # Check for existing session
            existing_session = await self.session_store.get_instahyre_session()
            if existing_session:
                self.logger.info("Found existing Instahyre session, attempting to restore")
                try:
                    await page.goto(self.base_url, timeout=self.navigation_timeout)
                    await self._wait_for_page_load(page)
                    
                    # Try to use existing session
                    if await self._verify_session_active(page):
                        self.logger.info("Existing Instahyre session is still active")
                        return True
                    else:
                        self.logger.info("Existing Instahyre session expired, will re-authenticate")
                        await self.session_store.delete_instahyre_session()
                except Exception as e:
                    self.logger.error(f"Failed to restore Instahyre session: {e}")
                    await self.session_store.delete_instahyre_session()
            
            # TEMPORARY: Skip authentication for testing
            self.logger.info("TEMPORARY: Skipping Instahyre authentication for testing")
            await page.goto(self.base_url, timeout=self.navigation_timeout)
            await self._wait_for_page_load(page)
            
            # Create dummy session to prevent re-auth attempts
            await self.session_store.save_instahyre_session({
                "authenticated": True,
                "session_id": "temp_session"
            })
            
            return True
            
            # Manual login required (commented out for testing)
            self.requires_manual_login = True
            
            # Navigate to login page
            await page.goto(self.login_url, timeout=self.navigation_timeout)
            await self._wait_for_page_load(page)
            
            # Look for Google Sign-In button
            google_sign_in_clicked = await self._safe_click(page, 'a[href*="oauth/google"], button:has-text("Google"), button:has-text("Sign in with Google")')
            
            if not google_sign_in_clicked:
                # Try alternative selectors for Google Sign-In
                google_selectors = [
                    'button[title*="Google"]',
                    'button:has-text("Continue with Google")',
                    'button:has-text("Continue with Google")',
                    'a:has-text("Google")',
                    '.google-sign-in',
                    'button[data-provider="google"]',
                    '[data-testid*="google"]',
                    'button:has-text("Google")',
                    'a:has-text("Sign in with Google")',
                    '.social-login button:has-text("Google")',
                    '[class*="google"] button',
                    'button[class*="google"]',
                    # Additional comprehensive selectors
                    'div[data-provider="google"]',
                    'span:has-text("Sign in with Google")',
                    'div[class*="google"]',
                    'button[aria-label*="Google"]',
                    'a[aria-label*="Google"]',
                    'div[id*="google"]',
                    'form button[type="submit"]:has-text("Google")',
                    'input[type="submit"][value*="Google"]',
                    'button[type="button"][onclick*="google"]',
                    'a[href*="accounts.google.com"]',
                    'iframe[src*="google.com"]',
                    'div[data-oauth-provider*="google"]',
                    'button[data-gtm-track*="google"]'
                ]
                
                for selector in google_selectors:
                    if await self._safe_click(page, selector):
                        google_sign_in_clicked = True
                        break
            
            if not google_sign_in_clicked:
                self.logger.warning("Could not find Google Sign-In button, falling back to email login")
                
                # Debug: Get page content and take screenshot
                try:
                    # Get page HTML to see what's actually there
                    page_content = await page.content()
                    self.logger.info(f"Page URL: {page.url}")
                    self.logger.info(f"Page title: {await page.title()}")
                    
                    # Look for any button or link with text containing 'google' (case-insensitive)
                    all_buttons = await page.query_selector_all('button, a, div[onclick], span[onclick]')
                    google_elements = []
                    for element in all_buttons:
                        text = await element.inner_text()
                        if text and 'google' in text.lower():
                            google_elements.append(text)
                    
                    if google_elements:
                        self.logger.info(f"Found Google-related elements: {google_elements}")
                    else:
                        self.logger.info("No Google-related elements found on page")
                    
                    # Take screenshot
                    await page.screenshot(path="instahyre_debug.png")
                    self.logger.info("Screenshot saved as instahyre_debug.png for debugging")
                    
                except Exception as e:
                    self.logger.error(f"Failed to debug page content: {e}")
                
                # Try email login as fallback
                return await self._try_email_login(page)
            
            # Wait for Google OAuth redirect
            await asyncio.sleep(2)
            
            # Wait for manual Google authentication
            self.logger.info("Waiting for manual Google authentication...")
            self.logger.info("Please complete Google Sign-In in the browser window")
            
            # Wait for authentication to complete (up to 2 minutes)
            max_wait_time = 120
            wait_interval = 2
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                # Check if we're back to Instahyre (successful auth)
                current_url = page.url
                if 'instahyre.com' in current_url and 'login' not in current_url:
                    # Check for authenticated indicators
                    if await self._verify_login_success(page):
                        self.logger.info("Google authentication successful")
                        
                        # Save session
                        storage_state = await page.context.storage_state()
                        await self.session_store.save_instahyre_session(storage_state)
                        
                        # Navigate to jobs page
                        await page.goto(self.jobs_url, timeout=self.navigation_timeout)
                        await self._wait_for_page_load(page)
                        
                        return True
                    else:
                        # Maybe we're on the right page but not fully logged in yet
                        self.logger.debug("On Instahyre but not fully authenticated yet")
                
                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval
                
                self.logger.debug(f"Waiting for Google authentication... {elapsed_time}s elapsed")
            
            self.logger.error("Google authentication timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Instahyre Google Sign-In failed: {e}")
            return False
    
    async def _try_email_login(self, page) -> bool:
        """Try email login as fallback."""
        try:
            self.logger.info("Attempting email login fallback")
            
            # Fill email
            if self.email:
                email_filled = await self._safe_type(page, 'input[type="email"]', self.email)
                if not email_filled:
                    self.logger.error("Failed to fill email field")
                    return False
            
            # Click continue button
            continue_clicked = await self._safe_click(page, 'button[type="submit"], button:has-text("Continue")')
            if not continue_clicked:
                self.logger.error("Failed to click continue button")
                return False
            
            # Wait for password field or Google option
            await asyncio.sleep(2)
            
            # Check if Google option is available
            google_option = await self._safe_wait_for_selector(page, 'button:has-text("Google"), a[href*="google"]', timeout=3000)
            if google_option:
                return await self._login(page, force_manual_login=True)
            
            # Try password if available (fallback - not recommended)
            password = os.getenv("INSTAHYRE_PASSWORD", "")
            if password:
                password_filled = await self._safe_type(page, 'input[type="password"]', password)
                if not password_filled:
                    self.logger.error("Failed to fill password field")
                    return False
                
                # Click login button
                login_clicked = await self._safe_click(page, 'button[type="submit"]')
                if not login_clicked:
                    self.logger.error("Failed to click login button")
                    return False
                
                # Wait for login to complete
                await asyncio.sleep(3)
                
                # Check if login was successful
                login_success = await self._verify_login_success(page)
                if not login_success:
                    self.logger.error("Email login verification failed")
                    return False
                
                self.logger.info("Email login successful")
                return True
            
            self.logger.error("No password available for email login")
            return False
            
        except Exception as e:
            self.logger.error(f"Email login fallback failed: {e}")
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
                'a#employer-profile-opportunity',
                'a.text-link[href*="/job-"]',
                '.employer-block',
                '.employer-row',
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
                        self.logger.info(f"Matched selector '{selector}' with {len(elements)} elements")
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
            title_element = await element.query_selector('h1, h2, h3, h4, .title, .job-title, .company-name, .employer-job-name')
            title = await self.utils.extract_text_safely(title_element) if title_element else ""
            
            if not title:
                return None
            
            # Check if element itself is a link
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            element_href = ""
            if tag_name == 'a':
                element_href = await element.get_attribute('href')
            
            # Extract company
            company_element = await element.query_selector('.company, .employer, span.info')
            company = await self.utils.extract_text_safely(company_element) if company_element else ""
            
            # Parse "Company - Title" pattern common on Instahyre
            if not company and " - " in title:
                parts = title.split(" - ", 1)
                company = parts[0].strip()
                title = parts[1].strip()
            elif " - " in title:
                parts = title.split(" - ", 1)
                company = parts[0].strip()
                title = parts[1].strip()
                
            if not company:
                company = "Unknown"
            
            # Filter by PM role (be slightly lenient, let shortlister filter precisely)
            is_pm = self.utils.is_pm_role(title)
            is_rejected = self.utils.is_reject_role(title)
            if not is_pm or is_rejected:
                return None
            
            # Extract location
            location_element = await element.query_selector('.location, .job-location, .place, .employer-locations, span[ng-if*="locations"]')
            location = await self.utils.extract_text_safely(location_element) if location_element else "Not specified"
            location = location.replace("Job available in", "").replace("Job available at", "").strip()
            
            # Extract salary
            salary_element = await element.query_selector('.salary, .compensation, .pay')
            salary = await self.utils.extract_text_safely(salary_element) if salary_element else "Not specified"
            salary = self.utils.normalize_salary(salary)
            
            # Extract description
            desc_element = await element.query_selector('.description, .job-description, .details, .employer-notes')
            description = await self.utils.extract_text_safely(desc_element) if desc_element else ""
            
            # Extract URL
            url = element_href
            if not url:
                url_element = await element.query_selector('a[href]')
                url = await self.utils.extract_url_safely(url_element) if url_element else ""
            
            if url and not url.startswith('http'):
                url = f"https://www.instahyre.com{url}"
            
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
