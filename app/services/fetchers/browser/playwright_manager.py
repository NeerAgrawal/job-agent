"""Playwright manager for safe browser lifecycle management."""

import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from app.core.logging import logger
from app.core.config.settings import settings


class PlaywrightManager:
    """Singleton Playwright manager with safe lifecycle handling."""
    
    def __init__(self):
        self.logger = logger.bind(service="playwright_manager")
        self._playwright = None
        self._browser = None
        self._contexts = {}
        self._max_concurrent_contexts = 2
        self._context_semaphore = asyncio.Semaphore(self._max_concurrent_contexts)
        self._default_timeout = 30000  # 30 seconds
        self._is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize Playwright and browser instance."""
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.error("Playwright not available - install with: pip install playwright")
            return False
            
        if self._is_initialized:
            return True
            
        try:
            self.logger.info("Initializing Playwright manager")
            
            self._playwright = await async_playwright().start()
            
            # Launch browser with sensible defaults
            headless = settings.playwright_headless
            
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            self._is_initialized = True
            self.logger.info("Playwright manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright: {e}")
            return False
    
    async def get_context(self, context_id: str = "default") -> Optional[BrowserContext]:
        """Get or create a browser context with concurrency limiting."""
        if not self._is_initialized:
            await self.initialize()
            
        if not self._is_initialized:
            return None
            
        async with self._context_semaphore:
            try:
                if context_id not in self._contexts:
                    self.logger.debug(f"Creating new browser context: {context_id}")
                    
                    context = await self._browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                        ignore_https_errors=True
                    )
                    
                    # Set default timeout
                    context.set_default_timeout(self._default_timeout)
                    
                    self._contexts[context_id] = context
                    
                return self._contexts[context_id]
                
            except Exception as e:
                self.logger.error(f"Failed to get context {context_id}: {e}")
                return None
    
    async def create_page(self, context_id: str = "default") -> Optional[Page]:
        """Create a new page in the specified context."""
        context = await self.get_context(context_id)
        if not context:
            return None
            
        try:
            page = await context.new_page()
            
            # Set up page error handling
            page.on('error', lambda error: self.logger.error(f"Page error: {error}"))
            page.on('pageerror', lambda error: self.logger.error(f"Page error: {error}"))
            
            return page
            
        except Exception as e:
            self.logger.error(f"Failed to create page: {e}")
            return None
    
    @asynccontextmanager
    async def get_page_context(self, context_id: str = "default"):
        """Context manager for safe page handling."""
        page = None
        try:
            page = await self.create_page(context_id)
            yield page
        finally:
            if page:
                try:
                    await page.close()
                except Exception as e:
                    self.logger.error(f"Error closing page: {e}")
    
    async def close_context(self, context_id: str) -> None:
        """Close a specific browser context."""
        if context_id in self._contexts:
            try:
                await self._contexts[context_id].close()
                del self._contexts[context_id]
                self.logger.debug(f"Closed context: {context_id}")
            except Exception as e:
                self.logger.error(f"Error closing context {context_id}: {e}")
    
    async def cleanup(self) -> None:
        """Clean up all browser resources."""
        try:
            self.logger.info("Cleaning up Playwright manager")
            
            # Close all contexts
            for context_id in list(self._contexts.keys()):
                await self.close_context(context_id)
            
            # Close browser
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            # Stop Playwright
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            self._is_initialized = False
            self.logger.info("Playwright manager cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def is_available(self) -> bool:
        """Check if Playwright is available and initialized."""
        return PLAYWRIGHT_AVAILABLE and self._is_initialized
    
    def get_context_count(self) -> int:
        """Get current number of active contexts."""
        return len(self._contexts)
    
    async def get_browser_info(self) -> Dict[str, Any]:
        """Get browser information for health monitoring."""
        return {
            'playwright_available': PLAYWRIGHT_AVAILABLE,
            'is_initialized': self._is_initialized,
            'active_contexts': len(self._contexts),
            'max_concurrent_contexts': self._max_concurrent_contexts,
            'browser_running': self._browser is not None,
            'timestamp': datetime.utcnow().isoformat()
        }


# Global singleton instance
_playwright_manager = None


async def get_playwright_manager() -> PlaywrightManager:
    """Get the global Playwright manager instance."""
    global _playwright_manager
    if _playwright_manager is None:
        _playwright_manager = PlaywrightManager()
        await _playwright_manager.initialize()
    return _playwright_manager
