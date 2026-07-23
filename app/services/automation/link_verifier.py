"""Link liveness verification for jobs about to be delivered.

Before a shortlisted job is sent out, confirm its posting URL isn't already dead,
so an application is never wasted on a closed/expired link. This runs only on the
handful of jobs actually being delivered (not the whole fetch), to keep it cheap.

Safety principle: only DROP a job on a *positive* dead signal (HTTP 404/410, or an
explicit "no longer accepting applications"-style message on a 200 page). Any
ambiguous response -- a bot-block (403/429), a timeout, a server error, a network
failure -- is treated as "assume live" and kept, so we never suppress a genuinely
open role just because the site blocked an automated check.
"""

import asyncio
from typing import List, Dict, Any, Tuple

import httpx

from app.core.logging import logger

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Phrases that positively indicate a closed/expired posting on a 200 page.
_DEAD_MARKERS = [
    "no longer accepting applications",
    "no longer accepting application",
    "we are no longer accepting",
    "this job is no longer available",
    "this position is no longer available",
    "this position has been filled",
    "position has been filled",
    "this posting has expired",
    "job posting is no longer active",
    "this job is closed",
    "requisition is closed",
    "this role is no longer open",
    "applications are closed",
]

_log = logger.bind(service="link_verifier")


async def _check_one(client: httpx.AsyncClient, url: str) -> Tuple[str, str]:
    """Return (status, reason) where status is 'live' | 'dead' | 'unknown'."""
    if not url:
        return "unknown", "no_url"

    try:
        resp = await client.get(url, follow_redirects=True)
        code = resp.status_code

        if code in (404, 410):
            return "dead", f"http_{code}"
        if code == 200:
            text = resp.text.lower()
            for marker in _DEAD_MARKERS:
                if marker in text:
                    return "dead", "closed_text"
            return "live", "ok"

        # 403/429 (bot-blocked), 5xx (server error), redirects to login, etc.
        # -> can't confirm dead, so assume live.
        return "unknown", f"http_{code}"

    except Exception as e:
        return "unknown", f"error_{type(e).__name__}"


async def filter_live_jobs(
    jobs: List[Dict[str, Any]],
    concurrency: int = 5,
    timeout: float = 10.0,
) -> List[Dict[str, Any]]:
    """Return jobs that are not confirmed dead (keeps 'live' and 'unknown')."""
    if not jobs:
        return []

    semaphore = asyncio.Semaphore(concurrency)
    headers = {"User-Agent": _UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}

    async with httpx.AsyncClient(timeout=timeout, headers=headers, verify=False) as client:

        async def guarded(job: Dict[str, Any]):
            url = job.get("job_url", "") if isinstance(job, dict) else getattr(job, "job_url", "")
            async with semaphore:
                return await _check_one(client, url)

        results = await asyncio.gather(*[guarded(j) for j in jobs])

    live_jobs = []
    dead = 0
    for job, (status, reason) in zip(jobs, results):
        if status == "dead":
            dead += 1
            company = job.get("company", "?") if isinstance(job, dict) else "?"
            title = job.get("title", "?") if isinstance(job, dict) else "?"
            _log.info(f"Dropping dead link ({reason}): {title} @ {company}")
        else:
            live_jobs.append(job)

    _log.info(
        f"Link verification: {len(jobs)} checked, {len(live_jobs)} kept, "
        f"{dead} confirmed dead"
    )
    return live_jobs
