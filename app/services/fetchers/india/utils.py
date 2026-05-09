"""Utility functions for India job fetchers."""

from typing import List, Dict, Any, Set
from urllib.parse import urlparse


class IndiaFetchUtils:
    """Utility class for India-specific job fetching."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate job URL."""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc and 
                      parsed.netloc not in ['localhost', 'example.com', 'test.com'])
        except Exception:
            return False
    
    @staticmethod
    def normalize_company_name(company: str) -> str:
        """Normalize company name."""
        if not company:
            return "Unknown"
        
        # Remove common suffixes
        company = company.strip()
        for suffix in [' Pvt Ltd', ' Private Limited', ' LLP', ' Inc.']:
            company = company.replace(suffix, '')
        
        return company.strip()
    
    @staticmethod
    def extract_salary_range(salary_text: str) -> Dict[str, Any]:
        """Extract salary range information."""
        if not salary_text:
            return {'min': None, 'max': None, 'currency': 'INR'}
        
        salary_text = salary_text.lower()
        
        # Look for LPA format
        if 'lpa' in salary_text:
            # Extract numbers
            import re
            numbers = re.findall(r'[\d,]+', salary_text)
            if numbers:
                return {
                    'min': int(numbers[0]) if len(numbers) > 0 else None,
                    'max': int(numbers[1]) if len(numbers) > 1 else None,
                    'currency': 'INR',
                    'type': 'LPA'
                }
        
        # Look for range format
        if '-' in salary_text:
            parts = salary_text.split('-')
            if len(parts) == 2:
                try:
                    min_salary = int(''.join(filter(str.isdigit, parts[0])))
                    max_salary = int(''.join(filter(str.isdigit, parts[1])))
                    return {
                        'min': min_salary,
                        'max': max_salary,
                        'currency': 'INR'
                    }
                except ValueError:
                    pass
        
        return {'min': None, 'max': None, 'currency': 'INR'}
    
    @staticmethod
    def clean_description(text: str) -> str:
        """Clean job description text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize quotes
        text = text.replace('"', "'").replace("'", "'")
        
        return text.strip()
    
    @staticmethod
    def detect_spam_keywords(text: str) -> bool:
        """Detect spam keywords in job description."""
        if not text:
            return False
        
        spam_keywords = [
            'urgent', 'immediate join', 'work from home', 'no experience required',
            'multi level marketing', 'investment opportunity', 'commission based',
            'pyramid scheme', 'referral program', 'data entry'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in spam_keywords)
