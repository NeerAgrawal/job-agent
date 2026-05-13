"""Browser utilities for safe automation and common tasks."""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.logging import logger


class BrowserUtils:
    """Utility functions for browser automation."""
    
    def __init__(self):
        self.logger = logger.bind(service="browser_utils")
        
        # Common selectors for job listings
        self.job_selectors = {
            'title': [
                'h1', 'h2', 'h3', 'h4',
                '.job-title', '.title', '.position',
                '[data-testid="job-title"]',
                '[data-job-title]'
            ],
            'company': [
                '.company', '.company-name', '.employer',
                '[data-testid="company-name"]',
                '[data-company]'
            ],
            'location': [
                '.location', '.job-location', '.place',
                '[data-testid="location"]',
                '[data-location]'
            ],
            'salary': [
                '.salary', '.compensation', '.pay',
                '[data-testid="salary"]',
                '[data-salary]'
            ],
            'description': [
                '.description', '.job-description', '.details',
                '[data-testid="job-description"]',
                '[data-description]'
            ],
            'url': [
                'a[href*="job"]', 'a[href*="position"]',
                '[data-href]', '[data-url]'
            ]
        }
        
        # PM role keywords for filtering
        self.pm_keywords = [
            'product manager', 'pm', 'associate product manager', 'apm',
            'technical product manager', 'tpm', 'senior product manager', 'spm',
            'principal product manager', 'group product manager', 'gpm',
            'ai product manager', 'platform product manager', 'growth product manager',
            'product owner', 'product lead', 'head of product', 'vp product'
        ]
        
        # Non-PM roles to reject
        self.reject_roles = [
            'account executive', 'sales', 'business development',
            'backend engineer', 'frontend engineer', 'software engineer',
            'marketing', 'customer success', 'support', 'recruiter',
            'analyst', 'operations', 'qa engineer'
        ]
    
    def extract_text_safely(self, element) -> str:
        """Safely extract text from element."""
        try:
            if element:
                text = element.text_content() or ""
                return self.clean_text(text)
        except Exception as e:
            self.logger.debug(f"Failed to extract text: {e}")
        
        return ""
    
    def extract_attribute_safely(self, element, attribute: str) -> str:
        """Safely extract attribute from element."""
        try:
            if element:
                return element.get_attribute(attribute) or ""
        except Exception as e:
            self.logger.debug(f"Failed to extract attribute {attribute}: {e}")
        
        return ""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common unwanted characters
        unwanted_chars = ['\t', '\n', '\r', '\xa0']
        for char in unwanted_chars:
            text = text.replace(char, ' ')
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_url_safely(self, element) -> str:
        """Safely extract URL from element."""
        try:
            if element:
                # Try href attribute
                href = element.get_attribute('href')
                if href:
                    return href
                
                # Try data attributes
                for attr in ['data-href', 'data-url', 'data-link']:
                    url = element.get_attribute(attr)
                    if url:
                        return url
                
                # Try to find link inside element
                link = element.query_selector('a[href]')
                if link:
                    return link.get_attribute('href') or ""
                    
        except Exception as e:
            self.logger.debug(f"Failed to extract URL: {e}")
        
        return ""
    
    def is_pm_role(self, title: str) -> bool:
        """Check if job title is a PM role."""
        title_lower = title.lower()
        
        # Check for PM keywords
        for keyword in self.pm_keywords:
            if keyword in title_lower:
                return True
        
        return False
    
    def is_reject_role(self, title: str) -> bool:
        """Check if job title should be rejected."""
        title_lower = title.lower()
        
        # Check for reject keywords
        for keyword in self.reject_roles:
            if keyword in title_lower:
                return True
        
        return False
    
    def extract_job_from_element(self, element, source: str = "unknown") -> Optional[Dict[str, Any]]:
        """Extract job data from element."""
        try:
            # Extract title
            title = self._extract_field(element, 'title')
            if not title:
                return None
            
            # Filter by PM role
            if not self.is_pm_role(title) or self.is_reject_role(title):
                return None
            
            # Extract other fields
            company = self._extract_field(element, 'company')
            location = self._extract_field(element, 'location')
            salary = self._extract_field(element, 'salary')
            description = self._extract_field(element, 'description')
            url = self._extract_field(element, 'url')
            
            # Build job data
            job_data = {
                'title': title,
                'company': company or "Unknown",
                'location': location or "Not specified",
                'salary': salary or "Not specified",
                'job_url': url or "",
                'jd_text': description or "",
                'source': source,
                'posted_at': datetime.utcnow().isoformat(),
                'raw_metadata': {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'source': source
                }
            }
            
            return job_data
            
        except Exception as e:
            self.logger.debug(f"Failed to extract job from element: {e}")
            return None
    
    def _extract_field(self, element, field_type: str) -> str:
        """Extract field using multiple selector strategies."""
        selectors = self.job_selectors.get(field_type, [])
        
        for selector in selectors:
            try:
                # Try direct selector
                found_element = element.query_selector(selector)
                if found_element:
                    if field_type == 'url':
                        return self.extract_url_safely(found_element)
                    else:
                        return self.extract_text_safely(found_element)
                
                # Try nested search
                found_element = element.query_selector(f'*:has({selector})')
                if found_element:
                    if field_type == 'url':
                        return self.extract_url_safely(found_element)
                    else:
                        return self.extract_text_safely(found_element)
                        
            except Exception:
                continue
        
        return ""
    
    def normalize_salary(self, salary_text: str) -> str:
        """Normalize salary text."""
        if not salary_text:
            return "Not specified"
        
        # Clean salary text
        salary_text = self.clean_text(salary_text)
        
        # Common salary patterns
        patterns = [
            r'(\d+(?:,\d{3})*)\s*-\s*(\d+(?:,\d{3})*)\s*lpa',
            r'(\d+(?:,\d{3})*)\s*lpa',
            r'(\d+(?:,\d{3})*)\s*-\s*(\d+(?:,\d{3})*)\s*per\s*year',
            r'(\d+(?:,\d{3})*)\s*per\s*year'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, salary_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Range found
                    min_salary = match.group(1).replace(',', '')
                    max_salary = match.group(2).replace(',', '')
                    return f"{min_salary}-{max_salary} LPA"
                else:
                    # Single value found
                    salary = match.group(1).replace(',', '')
                    return f"{salary} LPA"
        
        return salary_text
    
    def normalize_location(self, location_text: str) -> str:
        """Normalize location text."""
        if not location_text:
            return "Not specified"
        
        location_text = self.clean_text(location_text)
        
        # Common location normalizations
        location_mappings = {
            'bangalore': 'Bangalore',
            'bengaluru': 'Bangalore',
            'hyderabad': 'Hyderabad',
            'pune': 'Pune',
            'mumbai': 'Mumbai',
            'delhi': 'Delhi NCR',
            'gurugram': 'Gurugram',
            'gurgaon': 'Gurugram',
            'chennai': 'Chennai',
            'remote': 'Remote',
            'wfh': 'Remote',
            'work from home': 'Remote',
            'hybrid': 'Hybrid'
        }
        
        location_lower = location_text.lower()
        for key, value in location_mappings.items():
            if key in location_lower:
                return value
        
        return location_text
    
    def parse_relative_date(self, date_text: str) -> datetime:
        """Parse relative date text."""
        if not date_text:
            return datetime.utcnow()
        
        date_text = self.clean_text(date_text).lower()
        
        # Common relative date patterns
        if 'today' in date_text or 'just now' in date_text:
            return datetime.utcnow()
        elif 'yesterday' in date_text:
            return datetime.utcnow() - timedelta(days=1)
        elif 'ago' in date_text:
            # Extract number and unit
            match = re.search(r'(\d+)\s*(day|week|month)s?\s*ago', date_text)
            if match:
                number = int(match.group(1))
                unit = match.group(2)
                
                if unit == 'day':
                    return datetime.utcnow() - timedelta(days=number)
                elif unit == 'week':
                    return datetime.utcnow() - timedelta(weeks=number)
                elif unit == 'month':
                    return datetime.utcnow() - timedelta(days=number * 30)
        
        return datetime.utcnow()
    
    def get_safe_selector(self, selectors: List[str], fallback: str = None) -> str:
        """Get a safe selector from a list of options."""
        if selectors:
            return selectors[0]
        return fallback or "div"
    
    async def wait_for_content(self, page, timeout: int = 10000) -> bool:
        """Wait for page content to load."""
        try:
            # Wait for any content to appear
            content_selectors = [
                'body',
                'main',
                '.content',
                '#content',
                '*:has-text("")'
            ]
            
            for selector in content_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        return True
                except:
                    continue
            
            return False
            
        except Exception:
            return False
