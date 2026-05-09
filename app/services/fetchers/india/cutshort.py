"""Cutshort job fetcher for India PM opportunities."""

import httpx
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

    async def _fetch_from_source(
        self,
        client: httpx.AsyncClient,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch jobs from Cutshort."""

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

            search_url = (
                "https://cutshort.io/jobs/product-manager-jobs"
            )

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
                f"{response.status_code}"
            )

            response.raise_for_status()
            with open("cutshort_debug.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            jobs = []

            job_elements = soup.select(
                "div[data-jobid], article, div.job-card"
            )

            self.logger.info(
                f"Found {len(job_elements)} "
                f"Cutshort job elements"
            )

            for element in job_elements[:limit]:

                job_data = self._parse_job_element(
                    element
                )

                if (
                    job_data
                    and self._validate_job(job_data)
                ):

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

    def _determine_remote_status(
        self,
        location: str,
        description: str
    ) -> str:
        """Determine remote status."""

        combined = (
            f"{location} {description}"
        ).lower()

        remote_keywords = [
            "remote",
            "work from home",
            "hybrid",
            "wfh"
        ]

        if any(
            keyword in combined
            for keyword in remote_keywords
        ):
            return "Remote"

        return "On-site"

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