"""Cutshort job fetcher for India PM opportunities."""

import httpx
import json
import re
from typing import List, Dict, Any
from datetime import datetime

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

if BeautifulSoup is None:
    raise ImportError(
        "beautifulsoup4 is required for CutshortFetcher"
    )

from app.core.logging import logger
from .base_india_fetcher import BaseIndiaFetcher


class CutshortFetcher(BaseIndiaFetcher):
    """Cutshort job fetcher with async HTTP and BeautifulSoup."""

    def __init__(self):
        super().__init__(
            name="cutshort",
            base_url="https://cutshort.io"
        )
        # Cutshort routes role searches by slug. Only these two slugs reliably
        # return Cutshort's standard job-list JSON (associate-pm / tpm /
        # product-analyst slugs do not resolve to category pages on Cutshort).
        self.role_search_urls = [
            "https://cutshort.io/jobs/product-manager-jobs",
            "https://cutshort.io/jobs/product-owner-jobs",
        ]

    async def _fetch_from_source(
        self,
        client: httpx.AsyncClient,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch across the target-role search URLs, distributing the limit and
        de-duplicating by job URL."""
        all_jobs: List[Dict[str, Any]] = []
        seen = set()

        num_roles = len(self.role_search_urls)
        per_url = max(3, -(-limit // num_roles))  # ceil division, min 3 per role

        for url in self.role_search_urls:
            if len(all_jobs) >= limit:
                break
            role_jobs = await self._fetch_role_url(url, per_url)
            for job in role_jobs:
                key = job.get('job_url') or (job.get('title'), job.get('company'))
                if key in seen:
                    continue
                seen.add(key)
                all_jobs.append(job)
                if len(all_jobs) >= limit:
                    break

        self.logger.info(
            f"Cutshort multi-role fetch: {len(all_jobs)} unique jobs "
            f"across {num_roles} role searches"
        )
        return all_jobs

    async def _fetch_role_url(
        self,
        search_url: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch and parse a single Cutshort role-search URL."""

        try:

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
                "Connection": "keep-alive",
            }

            transport = httpx.AsyncHTTPTransport(
                retries=2
            )

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                verify=False,
                follow_redirects=True,
                headers=headers,
                transport=transport,
                http2=False,
            ) as secure_client:

                response = await secure_client.get(
                    search_url
                )

            self.logger.info(
                f"Cutshort response status: "
                f"{response.status_code} for {search_url}"
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            # 1. Try JSON State extraction first (highly precise & complete)
            script_tag = soup.find('script', id='__NEXT_DATA__')
            if not script_tag:
                for s in soup.find_all('script'):
                    if s.string and '{"props":' in s.string:
                        script_tag = s
                        break
            
            if script_tag and script_tag.string:
                try:
                    data = json.loads(script_tag.string)
                    self.logger.info("Found Cutshort Next.js state, attempting to extract jobs from JSON")
                    
                    props = data.get('props', {})
                    page_props = props.get('pageProps', {})
                    dehydrated = page_props.get('dehydratedState', {})
                    queries = dehydrated.get('queries', [])
                    
                    json_jobs = []
                    if queries and len(queries) > 0:
                        # Search across queries for pageData.jobs
                        for q in queries:
                            st = q.get('state', {})
                            in_data = st.get('data', {})
                            
                            # Case where inner structure varies slightly
                            c_data = in_data.get('data', {}) if isinstance(in_data, dict) else {}
                            p_data = c_data.get('pageData', {}) if isinstance(c_data, dict) else {}
                            j_list = p_data.get('jobs', []) if isinstance(p_data, dict) else []
                            
                            if j_list:
                                json_jobs = j_list
                                break
                                
                    if json_jobs:
                        self.logger.info(f"Successfully extracted {len(json_jobs)} jobs from Cutshort JSON state")
                        
                        parsed_jobs = []
                        for job in json_jobs[:limit]:
                            try:
                                headline = job.get('headline', '')
                                url = job.get('publicUrl', '')
                                
                                comp_details = job.get('companyDetails', {}) or {}
                                company_name = comp_details.get('name', '')
                                if not company_name:
                                    company_name = "Unknown"
                                
                                salary_text = job.get('salaryRangeText', '')
                                salary = self._parse_salary(salary_text)
                                
                                location = job.get('locationsText', '')
                                if not location:
                                    locs = job.get('locations', [])
                                    location = ", ".join(locs) if isinstance(locs, list) else str(locs)
                                    
                                desc_html = job.get('sanitizedComment', '')
                                desc_text = re.sub('<[^<]+?>', '', desc_html) if desc_html else ""
                                
                                remote_val = job.get('remoteType', '')
                                remote_status = self._determine_remote_status(remote_val, location, desc_text)
                                
                                domain_tags = self._extract_domain_tags(desc_text)
                                
                                job_data = {
                                    "title": headline,
                                    "company": company_name,
                                    "location": self._normalize_location(location),
                                    "salary": salary,
                                    "job_url": url,
                                    "posted_at": datetime.utcnow(),
                                    "jd_text": desc_text,
                                    "applicant_count": 0,
                                    "remote_status": remote_status,
                                    "domain_tags": domain_tags,
                                    "source": "Cutshort",
                                    "raw_metadata": {
                                        "job_id": job.get('_id'),
                                        "found_at": datetime.utcnow().isoformat(),
                                        "extraction_method": "json_state"
                                    }
                                }
                                
                                # Keep strict role filter only
                                if self._validate_job(job_data):
                                    parsed_jobs.append(job_data)
                                    
                            except Exception as e:
                                self.logger.error(f"Failed parsing single Cutshort JSON job: {e}")
                                continue
                                
                        if parsed_jobs:
                            self.logger.info(f"Successfully parsed {len(parsed_jobs)} valid PM jobs from Cutshort JSON")
                            return parsed_jobs
                            
                except Exception as json_err:
                    self.logger.warning(f"Failed to parse Cutshort JSON payload: {json_err}. Falling back to DOM scraper.")

            # 2. Fallback to DOM Scraper
            self.logger.info("Falling back to Cutshort DOM Scraping")
            jobs = []

            # Try multiple selector patterns for Cutshort job listings
            selectors = [
                "div[data-jobid]",
                "article.job-card", 
                "div.job-card",
                "div.job-tile",
                "div[data-testid*='job']",
                "div[class*='job']",
                "li.job-item",
                "div.job-listing",
                "div[data-job-id]",
                "div[class*='JobCard']",
                "div[class*='JobTile']"
            ]
            
            job_elements = []
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    break
            
            if not job_elements:
                # Fallback: look for any divs with job-related content
                all_divs = soup.find_all('div')
                job_elements = [div for div in all_divs if any(keyword in div.get_text().lower() for keyword in ['product manager', 'pm', 'manager', 'engineer', 'developer', 'salary', 'experience', 'location'])][:50]
                self.logger.info(f"Fallback: Found {len(job_elements)} potential job elements")

            self.logger.info(
                f"Found {len(job_elements)} Cutshort job elements"
            )

            for element in job_elements[:limit]:
                job_data = self._parse_job_element(element)
                if job_data and self._validate_job(job_data):
                    jobs.append(job_data)

            return jobs

        except Exception as e:

            self.logger.error(
                f"Cutshort parsing failed: {e}"
            )

            return []

    def _parse_job_element(
        self,
        element
    ) -> Dict[str, Any]:
        """Parse individual job element."""

        try:

            # Extract title
            title_elem = (
                element.select_one("h2")
                or element.select_one("h3")
                or element.select_one("a")
            )

            title = (
                title_elem.get_text(strip=True)
                if title_elem
                else "Unknown"
            )

            # Extract company
            company_elem = (
                element.select_one("[class*=company]")
                or element.select_one("span")
            )

            company = (
                company_elem.get_text(strip=True)
                if company_elem
                else "Unknown"
            )

            # Extract location
            location_elem = (
                element.select_one("[class*=location]")
            )

            location = (
                location_elem.get_text(strip=True)
                if location_elem
                else "Not specified"
            )

            # Extract salary
            salary_elem = (
                element.select_one("[class*=salary]")
            )

            salary_text = (
                salary_elem.get_text(strip=True)
                if salary_elem
                else ""
            )

            salary = self._parse_salary(
                salary_text
            )

            # Extract URL
            link_elem = element.find(
                "a",
                href=True
            )

            job_url = ""

            if link_elem:

                href = link_elem.get(
                    "href",
                    ""
                )

                if href.startswith("http"):

                    job_url = href

                else:

                    job_url = (
                        f"{self.base_url}{href}"
                    )

            # Extract description
            desc_elem = (
                element.select_one(
                    "[class*=description]"
                )
                or element.select_one("p")
            )

            description = (
                desc_elem.get_text(strip=True)
                if desc_elem
                else ""
            )

            # Extract posted date
            posted_elem = (
                element.select_one("time")
                or element.select_one(
                    "[class*=posted]"
                )
            )

            posted_text = (
                posted_elem.get_text(strip=True)
                if posted_elem
                else ""
            )

            posted_at = self._parse_datetime(
                posted_text
            )

            # Extract remote status
            remote_status = (
                self._determine_remote_status(
                    location,
                    description
                )
            )

            # Extract domain tags
            domain_tags = (
                self._extract_domain_tags(
                    description
                )
            )

            return {
                "title": title,
                "company": company,
                "location": self._normalize_location(
                    location
                ),
                "salary": salary,
                "job_url": job_url,
                "posted_at": posted_at,
                "jd_text": description,
                "applicant_count": 0,
                "remote_status": remote_status,
                "domain_tags": domain_tags,
                "source": "Cutshort",
                "raw_metadata": {
                    "found_at": (
                        datetime.utcnow()
                        .isoformat()
                    )
                }
            }

        except Exception as e:

            self.logger.error(
                f"Job element parsing failed: {e}"
            )

            return {}

    def _parse_datetime(
        self,
        date_text: str
    ) -> datetime:
        """Parse datetime safely."""

        if not date_text:
            return datetime.utcnow()

        try:

            if "ago" in date_text.lower():
                return datetime.utcnow()

            if "T" in date_text:
                return datetime.fromisoformat(
                    date_text.replace(
                        "Z",
                        "+00:00"
                    )
                )

            for fmt in [
                "%Y-%m-%d",
                "%d %b %Y",
                "%B %d, %Y",
            ]:

                try:
                    return datetime.strptime(
                        date_text,
                        fmt
                    )

                except ValueError:
                    continue

        except Exception:
            pass

        return datetime.utcnow()

    def _extract_domain_tags(
        self,
        description: str
    ) -> List[str]:
        """Extract domain tags."""

        if not description:
            return []

        description_lower = (
            description.lower()
        )

        domain_tags = []

        tech_domains = [
            "saas",
            "fintech",
            "healthcare",
            "education",
            "e-commerce",
            "banking",
            "ai",
            "platform",
            "api",
        ]

        for domain in tech_domains:

            if domain in description_lower:

                domain_tags.append(domain)

        return list(set(domain_tags))