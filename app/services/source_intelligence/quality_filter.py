"""Job-quality heuristics: detect staffing-agency / recruiter reposts.

India job boards (Naukri, Cutshort) are heavy with staffing-agency reposts that
aren't the employer's own application channel -- applying to these is low-signal
and often a dead end. This module flags the clearest cases conservatively, so we
avoid dropping legitimate employers (consulting firms, product companies) by
mistake. The signals used are:

  * an explicit "our client" / "on behalf of our client" framing in the JD, which
    is the single clearest repost tell, and
  * placeholder / obviously-generic company names, and
  * company names built around staffing/recruitment keywords.
"""

import re
from typing import Optional, Tuple

# Strongest signal: the JD openly says it's hiring for someone else.
_CLIENT_JD_PATTERNS = [
    r"\bour client\b",
    r"\bon behalf of (our|a) client\b",
    r"\bfor (our|a) client\b",
    r"\bclient of\b",
    r"\bhiring for (a|our) client\b",
    r"\bclient is (a|an|looking)\b",
]

# Placeholder / non-employer company names.
_PLACEHOLDER_COMPANIES = {
    "", "unknown", "confidential", "not disclosed", "undisclosed",
    "company", "company name", "it / software", "it/software",
    "software", "client", "our client", "n/a", "na",
}

# Staffing / recruitment company-name keywords. Kept conservative: these read as
# agencies rather than product employers. (Deliberately excludes bare
# "consulting"/"consultancy" and "solutions", which many real employers use.)
_STAFFING_NAME_KEYWORDS = [
    "staffing", "staffnix", "recruit", "manpower", "placement", "placements",
    "hr services", "hr solutions", "hiring solutions", "talent solutions",
    "talent acquisition", "workforce", "hr consult", "job consultant",
    "job consultants", "resourcing", "stafftech", "skillstaffing",
    "hr consulting",
]

# Company fields that are really a JD description phrase leaked into the company
# name (common on Cutshort reposts, e.g. "this is a BFSI / FINTECH company",
# "AI-first marketing company") -- these aren't a real, verifiable employer.
_DESCRIPTION_AS_COMPANY_PREFIXES = (
    "this is a", "this is an", "we are a", "we are an", "a leading",
    "an leading", "our company is", "one of the", "leading ",
)
# Note: bare "consultancy"/"consulting"/"consultancy services" are intentionally
# NOT flagged -- many legitimate employers use them (e.g. Tata Consultancy
# Services, Capco). The keywords above target dedicated staffing/recruitment firms.


def is_recruiter_repost(company: Optional[str], jd_text: Optional[str] = "") -> Tuple[bool, str]:
    """Return (is_repost, reason). Conservative: only flags clear signals."""
    name = (company or "").strip().lower()
    jd = (jd_text or "").lower()

    # 1. Placeholder / non-employer company names
    if name in _PLACEHOLDER_COMPANIES:
        return True, f"placeholder_company:{name or 'empty'}"

    # 2. Explicit "our client" framing in the JD
    for pattern in _CLIENT_JD_PATTERNS:
        if re.search(pattern, jd):
            return True, "jd_client_framing"

    # 3. "... client of <Agency>" also frequently shows up in the company field
    if "client of" in name or name.startswith("client "):
        return True, "company_client_of"

    # 4. Staffing/recruitment keywords in the company name
    for keyword in _STAFFING_NAME_KEYWORDS:
        if keyword in name:
            return True, f"staffing_name:{keyword}"

    # 5. A JD description phrase sitting in the company field (no real employer)
    if name.startswith(_DESCRIPTION_AS_COMPANY_PREFIXES):
        return True, "description_as_company"

    return False, ""
