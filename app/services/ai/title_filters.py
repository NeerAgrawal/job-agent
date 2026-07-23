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

# Reject titles (lowercase for matching)
REJECT_TITLES: Set[str] = {
    "sales",
    "account executive",
    "client partner",
    "finance",
    "attorney",
    "recruiter",
    "analyst",
    "hr",
    "human resources",
    "marketing",
    "designer",
    "customer success",
    "customer support",
    "business development",
    "business analyst",
    "data analyst",
    "financial analyst",
    "operations manager",
    "project manager",  # Different from Product Manager
    "program manager",  # Different from Product Manager
    "scrum master",
    "agile coach",
    "product designer",
    "ux designer",
    "ui designer",
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "devops engineer",
    "site reliability engineer",
    "qa engineer",
    "quality assurance",
    "test engineer",
    "solutions architect",
    "technical architect",
    "sales engineer",
    "solutions consultant",
    "implementation specialist",
    "customer success manager",
    "account manager",
    "business development representative",
    "sales development representative",
    "lead generation specialist",
    "marketing manager",
    "brand manager",
    "content manager",
    "social media manager",
    "community manager",
    "event manager",
    "office manager",
    "administrative assistant",
    "executive assistant",
    "personal assistant",
    "receptionist",
    "intern",
    "trainee",
    "apprentice",
    "freelance",
    "contractor",
    "consultant",
    "advisor",
    "coach",
    "mentor",
    "trainer",
    "instructor",
    "teacher",
    "professor",
    "researcher",
    "scientist",
    "doctor",
    "nurse",
    "medical",
    "healthcare",
    "legal",
    "lawyer",
    "paralegal",
    "accountant",
    "bookkeeper",
    "cashier",
    "teller",
    "banker",
    "investment banker",
    "financial advisor",
    "insurance agent",
    "real estate agent",
    "property manager",
    "facility manager",
    "maintenance",
    "security",
    "driver",
    "delivery",
    "warehouse",
    "logistics",
    "supply chain",
    "procurement",
    "purchasing",
    "inventory",
    "quality control",
    "inspection",
    "testing",
    "validation",
    "compliance",
    "audit",
    "risk management",
    "internal audit",
    "external audit",
    "tax",
    "payroll",
    "benefits",
    "compensation",
    "hr business partner",
    "talent acquisition",
    "recruiting coordinator",
    "sourcing specialist",
    "talent scout",
    "headhunter",
    "executive search",
    "staffing",
    "workforce planning",
    "organizational development",
    "learning and development",
    "training coordinator",
    "performance management",
    "employee relations",
    "labor relations",
    "diversity and inclusion",
    "equal employment opportunity",
    "safety",
    "environmental health and safety",
    "occupational health and safety",
    "security guard",
    "loss prevention",
    "asset protection",
    "fraud investigator",
    "compliance officer",
    "regulatory affairs",
    "legal counsel",
    "corporate secretary",
    "board relations",
    "investor relations",
    "public relations",
    "communications",
    "media relations",
    "crisis management",
    "reputation management",
    "brand management",
    "product marketing",
    "digital marketing",
    "content marketing",
    "email marketing",
    "social media marketing",
    "search engine optimization",
    "search engine marketing",
    "pay per click",
    "display advertising",
    "programmatic advertising",
    "affiliate marketing",
    "influencer marketing",
    "viral marketing",
    "guerrilla marketing",
    "event marketing",
    "trade show marketing",
    "experiential marketing",
    "cause marketing",
    "corporate social responsibility",
    "sustainability",
    "environmental",
    "green",
    "eco friendly",
    "carbon neutral",
    "renewable energy",
    "clean tech",
    "green tech",
    "sustainable development",
    "circular economy",
    "zero waste",
    "carbon footprint",
    "carbon offset",
    "carbon credits",
    "renewable energy credits",
    "green bonds",
    "sustainable investing",
    "impact investing",
    "environmental social governance",
    "esg",
    "socially responsible investing",
    "ethical investing",
    "responsible investment",
    "green finance",
    "climate finance",
    "carbon finance",
    "sustainable finance",
    "green banking",
    "ethical banking",
    "responsible banking",
    "impact banking",
    "community banking",
    "development banking",
    "microfinance",
    "peer to peer lending",
    "crowdfunding",
    "venture capital",
    "private equity",
    "angel investing",
    "seed funding",
    "startup funding",
    "accelerator",
    "incubator",
    "venture studio",
    "startup studio",
    "corporate venture capital",
    "strategic investment",
    "mergers and acquisitions",
    "corporate development",
    "strategic planning",
    "business strategy",
    "corporate strategy",
    "growth strategy",
    "market strategy",
    "competitive strategy",
    "innovation strategy",
    "digital strategy",
    "technology strategy",
    "product strategy",
    "go to market strategy",
    "market entry strategy",
    "international expansion",
    "global strategy",
    "emerging markets",
    "developing markets",
    "frontier markets",
    "market research",
    "competitive intelligence",
    "market intelligence",
    "business intelligence",
    "data analytics",
    "business analytics",
    "predictive analytics",
    "prescriptive analytics",
    "descriptive analytics",
    "diagnostic analytics",
    "big data",
    "data science",
    "machine learning",
    "artificial intelligence",
    "deep learning",
    "neural networks",
    "natural language processing",
    "computer vision",
    "robotics",
    "automation",
    "robotic process automation",
    "intelligent automation",
    "cognitive automation",
    "digital transformation",
    "business process reengineering",
    "process improvement",
    "lean manufacturing",
    "six sigma",
    "total quality management",
    "continuous improvement",
    "kaizen",
    "just in time",
    "lean startup",
    "agile development",
    "scrum",
    "kanban",
    "extreme programming",
    "test driven development",
    "behavior driven development",
    "domain driven design",
    "microservices",
    "service oriented architecture",
    "enterprise architecture",
    "solution architecture",
    "technical architecture",
    "cloud architecture",
    "devops",
    "site reliability engineering",
    "platform engineering",
    "infrastructure engineering",
    "cloud engineering",
    "data engineering",
    "machine learning engineering",
    "ai engineering",
    "data science",
    "data analysis",
    "business analysis",
    "systems analysis",
    "requirements analysis",
    "functional analysis",
    "technical analysis",
    "financial analysis",
    "investment analysis",
    "risk analysis",
    "credit analysis",
    "underwriting",
    "claims processing",
    "policy administration",
    "customer service",
    "call center",
    "contact center",
    "help desk",
    "technical support",
    "it support",
    "desktop support",
    "network support",
    "system administration",
    "network administration",
    "database administration",
    "security administration",
    "compliance administration",
    "audit administration",
    "quality administration",
    "process administration",
    "workflow administration",
    "document management",
    "records management",
    "information management",
    "knowledge management",
    "content management",
    "digital asset management",
    "product information management",
    "master data management",
    "data governance",
    "data quality",
    "data lineage",
    "data catalog",
    "metadata management",
    "data warehousing",
    "data lakes",
    "data marts",
    "business intelligence",
    "reporting",
    "dashboards",
    "scorecards",
    "key performance indicators",
    "metrics",
    "analytics",
    "visualization",
    "data visualization",
    "infographics",
    "presentation",
    "storytelling",
    "communication",
    "collaboration",
    "teamwork",
    "leadership",
    "management",
    "supervision",
    "coaching",
    "mentoring",
    "training",
    "development",
    "learning",
    "education",
    "knowledge",
    "skills",
    "competencies",
    "capabilities",
    "talent",
    "potential",
    "performance",
    "productivity",
    "efficiency",
    "effectiveness",
    "quality",
    "excellence",
    "innovation",
    "creativity",
    "problem solving",
    "critical thinking",
    "analytical thinking",
    "strategic thinking",
    "systems thinking",
    "design thinking",
    "lean thinking",
    "agile thinking",
    "growth mindset",
    "learning mindset",
    "curiosity",
    "adaptability",
    "flexibility",
    "resilience",
    "persistence",
    "determination",
    "motivation",
    "engagement",
    "commitment",
    "dedication",
    "passion",
    "enthusiasm",
    "energy",
    "drive",
    "ambition",
    "goal orientation",
    "results orientation",
    "achievement orientation",
    "success orientation",
    "performance orientation",
    "outcome orientation",
    "value creation",
    "impact",
    "influence",
    "persuasion",
    "negotiation",
    "conflict resolution",
    "relationship building",
    "networking",
    "partnership",
    "collaboration",
    "teamwork",
    "cooperation",
    "coordination",
    "integration",
    "alignment",
    "synergy",
    "leverage",
    "optimization",
    "maximization",
    "efficiency",
    "effectiveness",
    "productivity",
    "quality",
    "excellence",
    "innovation",
    "creativity",
    "problem solving",
    "critical thinking",
    "analytical thinking",
    "strategic thinking",
    "systems thinking",
    "design thinking",
    "lean thinking",
    "agile thinking",
    "growth mindset",
    "learning mindset",
    "curiosity",
    "adaptability",
    "flexibility",
    "resilience",
    "persistence",
    "determination",
    "motivation",
    "engagement",
    "commitment",
    "dedication",
    "passion",
    "enthusiasm",
    "energy",
    "drive",
    "ambition",
    "goal orientation",
    "results orientation",
    "achievement orientation",
    "success orientation",
    "performance orientation",
    "outcome orientation",
    "value creation",
    "impact",
    "influence",
    "persuasion",
    "negotiation",
    "conflict resolution",
    "relationship building",
    "networking",
    "partnership",
    "collaboration",
    "teamwork",
    "cooperation",
    "coordination",
    "integration",
    "alignment",
    "synergy",
    "leverage",
    "optimization",
    "maximization",
    "efficiency",
    "effectiveness",
    "productivity",
    "quality",
    "excellence",
    "innovation",
    "creativity",
    "problem solving",
    "critical thinking",
    "analytical thinking",
    "strategic thinking",
    "systems thinking",
    "design thinking",
    "lean thinking",
    "agile thinking",
    "growth mindset",
    "learning mindset",
    "curiosity",
    "adaptability",
    "flexibility",
    "resilience",
    "persistence",
    "determination",
    "motivation",
    "engagement",
    "commitment",
    "dedication",
    "passion",
    "enthusiasm",
    "energy",
    "drive",
    "ambition",
    "goal orientation",
    "results orientation",
    "achievement orientation",
    "success orientation",
    "performance orientation",
    "outcome orientation",
    "value creation",
    "impact",
    "influence",
    "persuasion",
    "negotiation",
    "conflict resolution",
    "relationship building",
    "networking",
    "partnership",
    "collaboration",
    "teamwork",
    "cooperation",
    "coordination",
    "integration",
    "alignment",
    "synergy",
    "leverage",
    "optimization",
    "maximization"
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
