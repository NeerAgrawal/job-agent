"""Naukri job fetcher for India PM opportunities."""

import asyncio
import httpx
from typing import List, Dict, Any
from datetime import datetime

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from app.core.logging import logger
from .base_india_fetcher import BaseIndiaFetcher


class NaukriFetcher(BaseIndiaFetcher):
    """Naukri job fetcher with async HTTP and BeautifulSoup."""
    
    def __init__(self):
        super().__init__(
            name="naukri",
            base_url="https://www.naukri.com"
        )
    
    async def _fetch_from_source(
        self,
        client: httpx.AsyncClient,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Naukri."""

        try:

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
            }

            search_url = (
                "https://www.naukri.com/"
                "product-manager-jobs"
            )

            response = await client.get(
                search_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )

            response.raise_for_status()
            with open("naukri_debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            jobs = []

            # Try multiple selector patterns for Naukri job listings
            selectors = [
                "article.jobTuple",
                "div.jobTuple",
                "div.job-card",
                "article.job-card",
                "div.job-tuple",
                "div[class*='jobTuple']",
                "div[class*='job-card']",
                "li.job-item",
                "div.job-listing",
                "div[data-job-id]",
                "article[data-job-id]",
                "div[class*='JobCard']",
                "div[class*='JobTuple']"
            ]
            
            job_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found {len(elements)} Naukri elements with selector: {selector}")
                    break
            
            if not job_elements:
                # Fallback: look for any divs with job-related content
                all_divs = soup.find_all('div')
                job_elements = [div for div in all_divs if any(keyword in div.get_text().lower() for keyword in ['product manager', 'pm', 'manager', 'engineer', 'developer', 'salary', 'experience', 'location', 'years'])][:50]
                self.logger.info(f"Fallback: Found {len(job_elements)} potential Naukri job elements")

            for element in job_elements[:limit]:

                job_data = self._parse_job_element(element)

                if job_data and self._validate_job(job_data):

                    jobs.append(job_data)

            return jobs

        except Exception as e:

            self.logger.error(
                f"Naukri parsing failed: {e}"
            )

            return []
    
    def _parse_job_element(self, element) -> Dict[str, Any]:
        """Parse individual job element."""
        try:
            # Extract title
            title_elem = (
                element.select_one("a.title")
                or element.select_one("h2 a")
            )
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # Extract company
            company_elem = element.find(['span', 'div'], class_=lambda x: x and 'company' in x.get('class', '').lower())
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Extract location
            location_elem = element.find(['span', 'div'], class_=lambda x: x and 'location' in x.get('class', '').lower())
            location = location_elem.get_text(strip=True) if location_elem else "Not specified"
            
            # Extract salary
            salary_elem = element.find(['span', 'div'], class_=lambda x: x and 'salary' in x.get('class', '').lower())
            salary_text = salary_elem.get_text(strip=True) if salary_elem else ""
            salary = self._parse_salary(salary_text)
            
            # Extract URL
            link_elem = element.find('a', href=True)
            job_url = link_elem.get('href') if link_elem else ""
            
            # Extract description
            desc_elem = element.find(['p', 'div'], class_=lambda x: x and 'description' in x.get('class', '').lower())
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract posted date
            posted_elem = element.find(['time', 'span'], class_=lambda x: x and 'posted' in x.get('class', '').lower())
            posted_text = posted_elem.get_text(strip=True) if posted_elem else ""
            posted_at = self._parse_datetime(posted_text)
            
            # Extract remote status
            remote_status = self._determine_remote_status(location, description)
            
            # Extract domain tags
            domain_tags = self._extract_domain_tags(description)
            
            return {
                'title': title,
                'company': company,
                'location': self._normalize_location(location),
                'salary': salary,
                'job_url': job_url,
                'posted_at': posted_at,
                'jd_text': description,
                'applicant_count': 0,
                'remote_status': remote_status,
                'domain_tags': domain_tags,
                'source': 'Naukri',
                'raw_metadata': {
                    'element': str(element),
                    'found_at': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Job element parsing failed: {e}")
            return {}
    
    def _parse_datetime(self, date_text: str) -> datetime:
        """Parse posted datetime."""
        if not date_text:
            return datetime.utcnow()
        
        # Handle common date formats
        try:
            # Try ISO format first
            if 'T' in date_text:
                return datetime.fromisoformat(date_text.replace('Z', '+00:00'))
            
            # Try relative dates
            if 'ago' in date_text.lower():
                return datetime.utcnow()  # Assume recent
            
            # Try common formats
            for fmt in ['%Y-%m-%d', '%d %b %Y', '%B %d, %Y']:
                try:
                    return datetime.strptime(date_text, fmt)
                except ValueError:
                    continue
                    
        except Exception:
            return datetime.utcnow()
    
    def _extract_domain_tags(self, description: str) -> List[str]:
        """Extract domain tags from job description."""
        if not description:
            return []
        
        description_lower = description.lower()
        domain_tags = []
        
        # Tech domains
        tech_domains = ['saas', 'fintech', 'healthcare', 'education', 'e-commerce', 'banking']
        for domain in tech_domains:
            if domain in description_lower:
                domain_tags.append(domain)
        
        return list(set(domain_tags))
