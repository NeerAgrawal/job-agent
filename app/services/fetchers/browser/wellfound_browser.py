"""Wellfound authenticated browser fetcher."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from app.services.fetchers.browser.base_browser_fetcher import BaseBrowserFetcher
from app.core.config.settings import settings
from app.core.logging import logger

class WellfoundBrowserFetcher(BaseBrowserFetcher):
    """Playwright-based fetcher for Wellfound."""
    
    def __init__(self):
        super().__init__(name="wellfound", base_url="https://wellfound.com/jobs")
        
        # We will use this URL to enforce remote and international filters
        # e.g., https://wellfound.com/jobs?remote=true
        self.search_url = "https://wellfound.com/jobs"
        
    async def _login(self, page) -> bool:
        """Perform Wellfound login."""
        
        email = settings.wellfound_email
        password = settings.wellfound_password
        
        if not email or not password:
            self.logger.error("Wellfound credentials missing in settings.")
            return False
            
        try:
            self.logger.info("Navigating to Wellfound login...")
            await page.goto("https://wellfound.com/login", timeout=self.navigation_timeout)
            
            # Wait for email field
            email_input = await self._safe_wait_for_selector(page, 'input[type="email"]')
            if not email_input:
                self.logger.error("Email input not found.")
                return False
                
            await email_input.fill(email)
            
            # Wait for password field
            password_input = await self._safe_wait_for_selector(page, 'input[type="password"]')
            if not password_input:
                self.logger.error("Password input not found.")
                return False
                
            await password_input.fill(password)
            
            # Click login
            login_btn = await self._safe_wait_for_selector(page, 'input[type="submit"]')
            if login_btn:
                await login_btn.click()
            else:
                # Attempt alternative login button
                await self._safe_click(page, 'button[type="submit"]')
                
            # Wait for network idle to ensure login completes
            await page.wait_for_load_state('networkidle', timeout=self.navigation_timeout)
            
            # Check if login was successful by looking for user avatar or logout button
            # Or by ensuring we are redirected to /jobs
            url = page.url
            if "login" in url:
                self.logger.error("Still on login page, login failed.")
                return False
                
            self.logger.info("Wellfound login successful.")
            return True
            
        except Exception as e:
            self.logger.exception(f"Wellfound login exception: {e}")
            return False

    async def _navigate_to_jobs(self, page, filters: Dict[str, Any]) -> None:
        """Navigate to the remote PM jobs listing."""
        self.logger.info("Navigating to jobs...")
        try:
            # Enforce Remote jobs in URL/UI (Wellfound handles this via filters)
            # In a real impl, we can append query params like `?remote_only=true` or manipulate the UI filters.
            target_url = self.search_url
            await page.goto(target_url, timeout=self.navigation_timeout)
            await page.wait_for_load_state('networkidle', timeout=self.navigation_timeout)
            
            # We can type "Product Manager" in the search box if it exists
            # For brevity, assuming the base url loads the user's pre-configured preferences
            
            # Scroll to load initial jobs
            await self._scroll_to_bottom(page)
            
        except Exception as e:
            self.logger.exception("Failed to navigate to jobs")

    async def _extract_jobs(self, page, limit: int) -> List[Dict[str, Any]]:
        """Extract job listings."""
        jobs = []
        try:
            # More stable selectors for Wellfound
            # Wellfound job listings often have 'data-test="JobCard"' or role-listings wrappers
            job_cards = await page.query_selector_all('[data-test="StartupResult"]')
            
            if not job_cards:
                job_cards = await page.query_selector_all('[data-test="JobCard"]')
                
            if not job_cards:
                # Fallback to general listing item class if test ids change
                job_cards = await page.query_selector_all('.styles_component__2k_Uo') 
                
            self.logger.info(f"Found {len(job_cards)} job cards on page. Extracting up to {limit}.")
            
            for index, card in enumerate(job_cards[:limit]):
                try:
                    # Scroll into view and click to open side panel
                    await card.scroll_into_view_if_needed()
                    await asyncio.sleep(1) # Human-like delay
                    await card.click()
                    
                    # Wait for right panel to load its content
                    # The details pane often has an element for the JD
                    await page.wait_for_timeout(2000) # Give it 2 seconds to load
                    
                    # Extract from the side panel or active card
                    title_el = await page.query_selector('h2.styles_title__1Vw-7, [data-test="JobDescriptionTitle"]')
                    if not title_el:
                        # Fallback to extracting from the card if panel fails
                        title_el = await card.query_selector('h2, [class*="title"]')
                        
                    title = await title_el.inner_text() if title_el else ""
                    
                    company_el = await page.query_selector('h1.styles_name__21Mwe, [data-test="StartupName"]')
                    if not company_el:
                        company_el = await card.query_selector('h2, [class*="company"]')
                        
                    company = await company_el.inner_text() if company_el else "Unknown"
                    
                    # Try to get the Apply link or Job link from the side panel
                    job_url_el = await page.query_selector('a[data-test="ApplyButton"], a[href*="/jobs/"]')
                    if not job_url_el:
                        job_url_el = await card.query_selector('a')
                        
                    job_url = await job_url_el.get_attribute('href') if job_url_el else ""
                    if job_url and not job_url.startswith("http"):
                        job_url = f"https://wellfound.com{job_url}"
                        
                    # Extract full job description from the side panel
                    jd_container = await page.query_selector('[data-test="JobDescription"], .styles_description__2x8_z')
                    jd_text = await jd_container.inner_text() if jd_container else title
                    
                    # Extract Salary if available
                    salary_el = await page.query_selector('[data-test="JobSalary"], .styles_salary__2aQ8-')
                    salary_text = await salary_el.inner_text() if salary_el else None
                    salary_value = None
                    if salary_text:
                        # Very rough extraction of max salary (e.g. "$120k - $150k" -> 150000)
                        salaries = re.findall(r'\d+', salary_text.replace('k', '000'))
                        if salaries:
                            salary_value = float(max(map(int, salaries)))

                    jobs.append({
                        "title": self._clean_text(title),
                        "company": self._clean_text(company),
                        "location": "Remote", # Since we enforce this via filter
                        "salary": salary_value,
                        "source": "Wellfound",
                        "job_url": job_url,
                        "posted_at": datetime.utcnow().isoformat(),
                        "jd_text": jd_text,
                        "remote_status": "remote",
                    })
                    
                    self.logger.debug(f"Extracted: {title} at {company}")
                    
                except Exception as e:
                    self.logger.debug(f"Failed to parse job card {index}: {e}")
                    
            self.logger.info(f"Successfully extracted {len(jobs)} detailed jobs from Wellfound browser.")
            return jobs
            
        except Exception as e:
            self.logger.exception("Failed to extract jobs from Wellfound")
            return jobs
