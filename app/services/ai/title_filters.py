"""Title filtering system for PM-relevant jobs."""

import re
from typing import Set, List

# Allowed target titles (lowercase for matching).
# Scoped for a QA -> Product transition: entry-level / IC product roles and
# adjacent product-related roles that leverage a technical/QA background, but
# not senior/leadership roles (see SENIORITY_REJECT_MARKERS below).
ALLOWED_PM_TITLES: Set[str] = {
    # Transition-friendly product titles (prioritized)
    "associate product manager",
    "technical product manager",
    "ai product manager",
    "platform product manager",
    "apm",
    "product owner",
    "junior product manager",

    # Traditional PM roles
    "product manager",
    "product operations manager",
    "product operations",
    "growth product manager",

    # Product-adjacent roles that fit a QA/technical transition
    "product analyst",
    "technical program manager",
}

# Hard reject for transition: roles too senior to be a realistic first product role.
TRANSITION_REJECT_TITLES: Set[str] = {
    "principal product manager",
    "lead product manager",
    "group product manager",
    "director of product",
    "vp of product",
    "head of product",
    "senior product manager",
}

# Standalone seniority markers that disqualify a role regardless of the product
# keyword it's attached to (e.g. "Senior Product Analyst", "Staff PM"). Checked
# as whitespace-delimited tokens so they don't match inside unrelated words.
SENIORITY_REJECT_MARKERS: Set[str] = {
    "senior",
    "sr",
    "principal",
    "staff",
    "lead",
    "director",
    "vp",
    "vice president",
    "head of",
    "group",
}

# Non-product job titles and functions, grouped by family.
#
# Scope note: this list contains *titles*, not skills or JD prose. Entries like
# "collaboration", "impact", or "growth mindset" were removed -- they never
# appear as a standalone job title, and matching them here only mislabels
# rejection stats. Keep additions to things that could plausibly be the whole
# title of a posting.
#
# Ordering note: `get_title_category` checks ALLOWED_PM_TITLES *before* this set,
# so overlapping substrings are safe by construction -- "technical program
# manager", "product analyst", "product operations manager" and "product owner"
# resolve as product roles even though "program manager", "analyst" and
# "operations manager" appear below.
REJECT_TITLES: Set[str] = {
    # --- Sales & business development ---
    "sales",
    "account executive",
    "account manager",
    "client partner",
    "business development",
    "business development representative",
    "sales development representative",
    "sales engineer",
    "inside sales",
    "territory manager",
    "lead generation specialist",

    # --- Marketing & communications ---
    "marketing",
    "marketing manager",
    "product marketing",
    "digital marketing",
    "content marketing",
    "content manager",
    "brand manager",
    "social media manager",
    "community manager",
    "search engine optimization",
    "public relations",
    "communications",
    "investor relations",

    # --- HR, recruiting & people ---
    "hr",
    "human resources",
    "hr business partner",
    "recruiter",
    "recruiting coordinator",
    "talent acquisition",
    "sourcing specialist",
    "headhunter",
    "executive search",
    "staffing",
    "payroll",
    "compensation",
    "learning and development",
    "training coordinator",

    # --- Finance, legal & compliance ---
    "finance",
    "accountant",
    "bookkeeper",
    "financial analyst",
    "financial advisor",
    "investment banker",
    "banker",
    "teller",
    "underwriting",
    "tax",
    "auditor",
    "internal audit",
    "attorney",
    "lawyer",
    "legal counsel",
    "paralegal",
    "compliance officer",
    "regulatory affairs",
    "insurance agent",
    "real estate agent",

    # --- Engineering & architecture ---
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "devops engineer",
    "site reliability engineer",
    "data engineer",
    "machine learning engineer",
    "security engineer",
    "network engineer",
    "automation engineer",
    "qa engineer",
    "quality assurance",
    "test engineer",
    "solutions architect",
    "technical architect",
    "cloud architect",
    "enterprise architect",

    # --- Design & research ---
    "designer",
    "product designer",
    "ux designer",
    "ui designer",
    "graphic designer",
    "ux researcher",

    # --- Data & analysis (non-product) ---
    "analyst",
    "data analyst",
    "business analyst",
    "data scientist",
    "systems analyst",
    "research analyst",
    "business intelligence",

    # --- Delivery & agile (distinct from Product Management) ---
    "project manager",
    "program manager",
    "delivery manager",
    "engagement manager",
    "scrum master",
    "agile coach",

    # --- Support, IT & operations ---
    "customer success",
    "customer success manager",
    "customer support",
    "customer service",
    "technical support",
    "it support",
    "help desk",
    "desktop support",
    "system administration",
    "network administration",
    "database administration",
    "operations manager",
    "office manager",
    "facility manager",
    "property manager",
    "call center",

    # --- Consulting & advisory ---
    "consultant",
    "solutions consultant",
    "implementation specialist",
    "advisor",
    "coach",
    "mentor",
    "trainer",
    "instructor",
    "teacher",
    "professor",

    # --- Supply chain & field operations ---
    "logistics",
    "supply chain",
    "procurement",
    "purchasing",
    "inventory",
    "warehouse",
    "driver",
    "delivery",
    "quality control",
    "inspection",

    # --- Healthcare ---
    "doctor",
    "nurse",
    "medical",
    "healthcare",

    # --- Administrative & facilities ---
    "administrative assistant",
    "executive assistant",
    "personal assistant",
    "receptionist",
    "cashier",
    "security guard",
    "loss prevention",
    "maintenance",

    # --- Non-permanent / early-career engagements ---
    "intern",
    "trainee",
    "apprentice",
    "freelance",
    "contractor",
}


def normalize_title(title: str) -> str:
    """Normalize job title for matching."""
    if not title:
        return ""

    # Convert to lowercase and strip
    normalized = title.lower().strip()

    # Remove common punctuation and extra spaces
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized


def _has_seniority_marker(normalized: str) -> bool:
    """True if the (already normalized) title contains a standalone seniority marker.

    Matching is token-based so, e.g., "senior" matches "senior product manager" but
    a marker like "lead" won't fire inside "leadership" or "leaderboard".
    """
    tokens = normalized.split()
    token_set = set(tokens)

    for marker in SENIORITY_REJECT_MARKERS:
        if " " in marker:
            # Multi-word marker (e.g. "head of", "vice president")
            if marker in normalized:
                return True
        elif marker in token_set:
            return True

    return False


def allow_title(title: str) -> bool:
    """Check if job title is allowed (a target product-transition role)."""
    if not title:
        return False

    normalized = normalize_title(title)

    # Seniority disqualifies regardless of the product keyword attached to it
    if _has_seniority_marker(normalized):
        return False

    for allowed_title in ALLOWED_PM_TITLES:
        if allowed_title in normalized:
            return True

    return False


def is_transition_friendly(title: str) -> bool:
    """Check if title is transition-friendly (a target role and not too senior)."""
    if not title:
        return False

    normalized = normalize_title(title)

    if _has_seniority_marker(normalized):
        return False

    for reject_title_entry in TRANSITION_REJECT_TITLES:
        if reject_title_entry in normalized:
            return False

    for allowed_title in ALLOWED_PM_TITLES:
        if allowed_title in normalized:
            return True

    return False


def is_transition_penalized(title: str) -> bool:
    """Deprecated: senior roles are now hard-rejected rather than soft-penalized.

    Retained for backward compatibility; always returns False.
    """
    return False


def reject_title(title: str) -> bool:
    """Check if job title should be rejected."""
    if not title:
        return True

    normalized = normalize_title(title)

    # Seniority markers (senior/principal/lead/staff/director/vp/head of/group)
    if _has_seniority_marker(normalized):
        return True

    # Check if any reject title is in the job title
    for reject_entry in REJECT_TITLES:
        if reject_entry in normalized:
            return True

    # Check if any transition reject title is in the job title
    for reject_entry in TRANSITION_REJECT_TITLES:
        if reject_entry in normalized:
            return True

    return False


def filter_pm_titles(titles: List[str]) -> List[str]:
    """Filter list of job titles to only target product-transition roles."""
    pm_titles = []

    for title in titles:
        if get_title_category(title) == "pm":
            pm_titles.append(title)

    return pm_titles


def get_title_category(title: str) -> str:
    """Get the category of a job title.

    Precedence is deliberate and staged:
      1. Seniority markers -> reject (so "Senior Product Manager" can't slip through
         on the allowed substring "product manager").
      2. Explicit too-senior product roles -> reject.
      3. Allowed target roles -> pm (must run BEFORE the generic reject list, since
         "technical program manager"/"product analyst" contain the generic reject
         substrings "program manager"/"analyst").
      4. Generic non-product reject list -> reject.
      5. Otherwise -> unknown.

    Note that callers treat "reject" and "unknown" identically (only "pm" is
    accepted anywhere in the pipeline); the distinction exists for rejection
    stats and reporting.
    """
    if not title:
        return "unknown"

    normalized = normalize_title(title)

    # 1. Seniority disqualifier
    if _has_seniority_marker(normalized):
        return "reject"

    # 2. Explicit too-senior product roles
    for reject_entry in TRANSITION_REJECT_TITLES:
        if reject_entry in normalized:
            return "reject"

    # 3. Allowed target product roles
    for allowed_title in ALLOWED_PM_TITLES:
        if allowed_title in normalized:
            return "pm"

    # 4. Generic non-product reject list
    for reject_entry in REJECT_TITLES:
        if reject_entry in normalized:
            return "reject"

    return "unknown"


def is_pm_role(title: str) -> bool:
    """Check if title is a PM role."""
    return get_title_category(title) == "pm"


def is_reject_role(title: str) -> bool:
    """Check if title should be rejected."""
    return get_title_category(title) == "reject"
