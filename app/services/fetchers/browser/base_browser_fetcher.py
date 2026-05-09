"""Base browser fetcher with async safety and error handling."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from app.core.logging import logger
from .playwright_manager import get_playwright_manager
from .session_store import SessionStore


class BaseBrowserFetcher(ABC):
    """Base class for browser-based job fetchers with safety features."""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.logger = logger.bind(service=f"browser_{name}")
        self.session_store = SessionStore()
        self.max_retries = 3
        self.retry_delay = 2.0
        self.page_timeout = 30000
        self.navigation_timeout = 60000
        self.wait_timeout = 10000
        
    async def fetch_jobs(self, limit: int = 50, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fetch jobs using browser automation with safety."""
        try:
            self.logger.info(f"Starting browser fetch from {self.name} with limit={limit}")
            
            # Get Playwright manager
            playwright_manager = await get_playwright_manager()
            if not playwright_manager.is_available():
                self.logger.error("Playwright not available for browser fetch")
                return []
            
            # Use context manager for safe page handling
            async with playwright_manager.get_page_context(self.name) as page:
                if not page:
                    self.logger.error("Failed to create browser page")
                    return []
                
                # Perform authenticated fetch if needed
                jobs = await self._authenticated_fetch(page, limit, filters)
                
                self.logger.info(f"Browser fetch completed: {len(jobs)} jobs from {self.name}")
                return jobs
                
        except Exception as e:
            self.logger.error(f"Browser fetch failed for {self.name}: {e}")
            return []
    
    async def _authenticated_fetch(self, page, limit: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform authenticated job fetch."""
        try:
            # Check if we have a valid session
            session_valid = await self._is_session_valid(page)
            
            if not session_valid:
                # Perform login
                login_success = await self._login(page)
                if not login_success:
                    self.logger.error(f"Login failed for {self.name}")
                    return []
                
                # Save session after successful login
                await self._save_session(page)
            
            # Navigate to job listings
            await self._navigate_to_jobs(page, filters)
            
            # Extract jobs
            jobs = await self._extract_jobs(page, limit)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Authenticated fetch failed: {e}")
            return []
    
    @abstractmethod
    async def _login(self, page) -> bool:
        """Perform login flow. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _navigate_to_jobs(self, page, filters: Dict[str, Any]) -> None:
        """Navigate to job listings. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def _extract_jobs(self, page, limit: int) -> List[Dict[str, Any]]:
        """Extract job listings. Must be implemented by subclasses."""
        pass
    
    async def _is_session_valid(self, page) -> bool:
        """Check if current session is valid."""
        try:
            # Try to navigate to a protected page
            await page.goto(self.base_url, timeout=self.navigation_timeout)
            
            # Check for login indicators
            login_indicators = await self._get_login_indicators(page)
            
            # If no login indicators found, session is valid
            return not login_indicators
            
        except Exception as e:
            self.logger.debug(f"Session validation failed: {e}")
            return False
    
    async def _get_login_indicators(self, page) -> List[str]:
        """Get indicators that user needs to login."""
        indicators = []
        
        # Common login indicators
        login_selectors = [
            'input[type="email"]',
            'input[type="password"]',
            'button[type="submit"]',
            '.login',
            '.signin',
            'a[href*="login"]',
            'a[href*="signin"]'
        ]
        
        for selector in login_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=2000)
                if element:
                    indicators.append(selector)
            except:
                continue
        
        return indicators
    
    async def _save_session(self, page) -> None:
        """Save browser session for reuse."""
        try:
            # Get storage state
            storage_state = await page.context.storage_state()
            
            # Save to session store
            await self.session_store.save_session(self.name, storage_state)
            
            self.logger.info(f"Session saved for {self.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
    
    async def _load_session(self, page) -> bool:
        """Load saved browser session."""
        try:
            # Get stored session
            storage_state = await self.session_store.get_session(self.name)
            if not storage_state:
                return False
            
            # Apply stored session
            await page.context.add_cookies(storage_state.get('cookies', []))
            
            self.logger.info(f"Session loaded for {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            return False
    
    async def _safe_wait_for_selector(self, page, selector: str, timeout: int = None) -> Optional[Any]:
        """Safely wait for selector with timeout."""
        try:
            timeout = timeout or self.wait_timeout
            element = await page.wait_for_selector(selector, timeout=timeout)
            return element
        except Exception as e:
            self.logger.debug(f"Selector not found: {selector} - {e}")
            return None
    
    async def _safe_click(self, page, selector: str, timeout: int = None) -> bool:
        """Safely click element with retry."""
        timeout = timeout or self.wait_timeout
        
        for attempt in range(self.max_retries):
            try:
                element = await self._safe_wait_for_selector(page, selector, timeout)
                if element:
                    await element.click()
                    return True
            except Exception as e:
                self.logger.debug(f"Click attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        return False
    
    async def _safe_type(self, page, selector: str, text: str, timeout: int = None) -> bool:
        """Safely type text into element."""
        timeout = timeout or self.wait_timeout
        
        try:
            element = await self._safe_wait_for_selector(page, selector, timeout)
            if element:
                await element.clear()
                await element.type(text)
                return True
        except Exception as e:
            self.logger.debug(f"Type failed: {e}")
        
        return False
    
    async def _wait_for_page_load(self, page, timeout: int = None) -> bool:
        """Wait for page to fully load."""
        timeout = timeout or self.navigation_timeout
        
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
            return True
        except Exception as e:
            self.logger.debug(f"Page load wait failed: {e}")
            return False
    
    async def _scroll_to_bottom(self, page) -> None:
        """Scroll to bottom of page."""
        try:
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)  # Wait for content to load
        except Exception as e:
            self.logger.debug(f"Scroll failed: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common unwanted characters
        unwanted_chars = ['\t', '\n', '\r']
        for char in unwanted_chars:
            text = text.replace(char, ' ')
        
        return text.strip()
    
    def _extract_job_url(self, element) -> str:
        """Extract job URL from element."""
        try:
            # Try href attribute
            href = element.get_attribute('href')
            if href:
                return href
            
            # Try click to get URL
            return element.get_attribute('data-href') or ""
            
        except Exception:
            return ""
