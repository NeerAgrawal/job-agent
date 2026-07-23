"""Startup discoverer to dynamically find AI companies and add them to the database."""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from app.core.logging import logger
from app.database.session import get_db_session
from app.models.target_company import TargetCompany
from app.services.fetchers.browser.wellfound_browser import WellfoundBrowserFetcher
from sqlalchemy.future import select

class StartupDiscoverer:
    """Discovers AI startups and adds them to TargetCompany DB."""
    
    def __init__(self):
        self.logger = logger.bind(service="startup_discoverer")
        # Reuse wellfound browser fetcher to scrape companies
        self.wellfound_fetcher = WellfoundBrowserFetcher()
        self.wellfound_fetcher.search_url = "https://wellfound.com/companies?keywords=AI"

    async def run_discovery(self, limit: int = 20) -> int:
        """Run the discovery process."""
        self.logger.info("Starting AI startup discovery...")
        
        try:
            # Note: For MVP, we mock the company extraction since Wellfound structure for companies
            # is different from jobs. In a real impl, we would use the authenticated page context
            # to scrape https://wellfound.com/companies?keywords=AI
            
            companies_discovered = await self._discover_companies(limit)
            
            saved_count = await self._save_companies(companies_discovered)
            
            self.logger.info(f"Discovery complete. Saved {saved_count} new companies.")
            return saved_count
            
        except Exception as e:
            self.logger.exception("Startup discovery failed")
            return 0
            
    async def _discover_companies(self, limit: int) -> List[Dict[str, Any]]:
        """Discover AI startups using Playwright."""
        companies = []
        try:
            from app.services.fetchers.browser.playwright_manager import get_playwright_manager
            
            playwright_manager = await get_playwright_manager()
            if not playwright_manager.is_available():
                await playwright_manager.initialize()
                
            if not playwright_manager.is_available():
                self.logger.error("Playwright not available for startup discovery.")
                return companies
                
            async with playwright_manager.get_page_context("startup_discoverer") as page:
                if not page:
                    return companies
                    
                # We can attempt a login if needed, or just scrape public data
                # Let's use the wellfound login logic to get an authenticated session
                login_success = await self.wellfound_fetcher._login(page)
                if not login_success:
                    self.logger.warning("Proceeding with unauthenticated session for discovery.")
                    
                await page.goto(self.wellfound_fetcher.search_url, timeout=60000)
                await page.wait_for_load_state('networkidle')
                
                # Scroll to load
                for _ in range(3):
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(2)
                    
                # Extract companies
                company_cards = await page.query_selector_all('[data-test="StartupResult"]')
                if not company_cards:
                    company_cards = await page.query_selector_all('.styles_component__2k_Uo')
                    
                for card in company_cards[:limit]:
                    try:
                        name_el = await card.query_selector('h1, h2, [data-test="StartupName"]')
                        name = await name_el.inner_text() if name_el else "Unknown"
                        
                        # Guess domain from name (Simplistic fallback)
                        domain = name.lower().replace(" ", "") + ".com"
                        
                        # Wellfound might not list ATS links directly on the search page
                        # We store the company and let an enrichment process find the ATS
                        companies.append({
                            "name": name,
                            "domain": domain,
                            "careers_url": f"https://wellfound.com/company/{name.lower().replace(' ', '-')}",
                            "ats_provider": "unknown"
                        })
                    except Exception as e:
                        self.logger.debug(f"Failed to parse company card: {e}")
                        
            return companies
            
        except Exception as e:
            self.logger.exception(f"Error during discovery: {e}")
            return companies

    async def _save_companies(self, companies: List[Dict[str, Any]]) -> int:
        """Save discovered companies to database."""
        saved_count = 0
        
        async with get_db_session() as session:
            for comp_data in companies:
                try:
                    # Check if exists
                    stmt = select(TargetCompany).where(TargetCompany.name == comp_data["name"])
                    result = await session.execute(stmt)
                    existing = result.scalars().first()
                    
                    if not existing:
                        new_comp = TargetCompany(
                            name=comp_data["name"],
                            domain=comp_data["domain"],
                            careers_url=comp_data["careers_url"],
                            ats_provider=comp_data["ats_provider"]
                        )
                        session.add(new_comp)
                        saved_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to save company {comp_data.get('name')}: {e}")
                    
            await session.commit()
            
        return saved_count
