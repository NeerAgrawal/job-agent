"""Seniority detection and scoring for PM transition optimization."""

import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum

from app.core.logging import logger


# Maximum years of experience a posting may demand and still be a realistic
# target. The profile this system serves is a QA -> Product switcher with ~0
# years *in product*, so anything asking beyond this is screening for someone
# who is already a PM, regardless of how junior the title sounds. Titles alone
# cannot catch this: postings titled "Associate Product Manager" have been seen
# demanding 6 years.
MAX_YEARS_REQUIRED = 3

# "5+ years", "5 - 7 years", "minimum 4 to 5 years", "at least 6 yrs"
_YEARS_RANGE = re.compile(
    r"(\d{1,2})\s*(?:\+|plus)?\s*(?:-|–|to)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)\b",
    re.I,
)
_YEARS_SINGLE = re.compile(r"(\d{1,2})\s*(?:\+|plus)?\s*(?:years?|yrs?)\b", re.I)

# Contexts where a year count describes the company or the past, not a
# requirement on the candidate ("founded 10 years ago", "over the last 5 years").
_YEARS_NEGATIVE_CTX = re.compile(
    r"(years?\s+ago|past\s+\d+\s+years?|last\s+\d+\s+years?|founded|"
    r"over\s+the\s+years|\d+\s*years?\s+of\s+(?:growth|operation|history)|"
    r"in\s+business|since)",
    re.I,
)


def extract_required_years(text: str) -> Optional[int]:
    """Extract the effective years-of-experience bar a JD sets.

    Returns None when the posting states no requirement, which is common and is
    deliberately *not* treated as disqualifying -- unstated usually means
    flexible or junior-friendly.

    Two different rules apply, and conflating them badly understates the bar:

    * Within a single range ("9-14 years") the *floor* is what gates an
      applicant, so the lower bound is used.
    * Across separate mentions the *maximum* is the real bar, because smaller
      figures are almost always sub-requirements nested inside a larger one.
      A posting reading "Minimum of 9 yrs as Business Analyst, 2 yrs as Product
      Owner" demands nine years, not two; "5+ years as a product owner, 3+
      years with Agile" demands five, not three.

    Taking a global minimum instead lets one incidental small number wave
    through a posting that is far out of reach.
    """
    if not text:
        return None

    candidates = []

    for match in _YEARS_RANGE.finditer(text):
        window = text[max(0, match.start() - 60): match.end() + 20]
        if _YEARS_NEGATIVE_CTX.search(window):
            continue
        candidates.append(int(match.group(1)))

    consumed = [(m.start(), m.end()) for m in _YEARS_RANGE.finditer(text)]
    for match in _YEARS_SINGLE.finditer(text):
        if any(start <= match.start() < end for start, end in consumed):
            continue
        window = text[max(0, match.start() - 60): match.end() + 20]
        if _YEARS_NEGATIVE_CTX.search(window):
            continue
        candidates.append(int(match.group(1)))

    credible = [c for c in candidates if 0 < c <= 25]
    return max(credible) if credible else None


# Kept so existing imports keep working; the name understated what it returns.
extract_min_years_required = extract_required_years


def exceeds_experience_bar(
    jd_text: str,
    max_years: int = MAX_YEARS_REQUIRED,
) -> Tuple[bool, Optional[int]]:
    """Return (should_reject, years_required) for a job description.

    Postings with no stated requirement are kept.
    """
    years = extract_min_years_required(jd_text)
    if years is None:
        return False, None
    return years > max_years, years


class SeniorityLevel(Enum):
    """Seniority levels for PM roles."""
    ENTRY = "entry"
    JUNIOR = "junior"
    ASSOCIATE = "associate"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class SeniorityDetector:
    """Detects and scores seniority levels for PM transition optimization."""
    
    def __init__(self):
        self.transition_target_years = 4.5  # Target experience for PM transition

        # Seniority penalties (negative scores).
        # Head-of-product / VP / group-PM titles are already classified as
        # DIRECTOR or EXECUTIVE by detect_seniority_level, so they need no
        # separate entries here. (They previously appeared as bare strings
        # assigned onto the enum, which could never match a SeniorityLevel
        # lookup and so were silently dead.)
        self.seniority_penalties = {
            SeniorityLevel.PRINCIPAL: -15.0,
            SeniorityLevel.LEAD: -12.0,
            SeniorityLevel.DIRECTOR: -20.0,
            SeniorityLevel.EXECUTIVE: -25.0,
        }

        # Experience fit bonuses, tuned for a career switcher with roughly zero
        # years *in product*. The previous bands treated a 2-6 year ask as the
        # "sweet spot" and only penalised past 8 years, which rewarded exactly
        # the postings that screen out a first-time PM.
        self.experience_bonuses = {
            (0, 1): 10.0,   # Genuinely entry level
            (2, 2): 8.0,    # Still realistic
            (3, 3): 5.0,    # Stretch, but reachable
        }

        # Experience penalties
        self.experience_penalties = {
            (4, 5): -8.0,    # Screening for an existing PM
            (6, 25): -15.0,  # Well outside a transition profile
        }
    
    def detect_seniority_level(self, title: str, description: str = "", years_required: Optional[int] = None) -> SeniorityLevel:
        """Detect seniority level from job data."""
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Principal level detection
        if any(keyword in title_lower for keyword in [
            'principal', 'staff', 'lead principal'
        ]):
            return SeniorityLevel.PRINCIPAL
        
        # Lead level detection
        if any(keyword in title_lower for keyword in [
            'lead', 'team lead', 'group lead', 'lead product'
        ]):
            return SeniorityLevel.LEAD
        
        # Director level detection
        if any(keyword in title_lower for keyword in [
            'director', 'head of', 'vp', 'vice president', 'c-level'
        ]):
            return SeniorityLevel.DIRECTOR
        
        # Executive level detection
        if any(keyword in title_lower for keyword in [
            'vp product', 'head of product', 'group pm'
        ]):
            return SeniorityLevel.EXECUTIVE
        
        # Senior level detection
        if any(keyword in title_lower for keyword in [
            'senior', 'sr.', 'sr ', 'principal'  # Already caught above
        ]):
            return SeniorityLevel.SENIOR
        
        # Associate level detection
        if any(keyword in title_lower for keyword in [
            'associate', 'apm', 'associate product'
        ]):
            return SeniorityLevel.ASSOCIATE
        
        # Junior level detection
        if any(keyword in title_lower for keyword in [
            'junior', 'jr.', 'jr ', 'entry'
        ]):
            return SeniorityLevel.JUNIOR
        
        # Mid level detection
        if any(keyword in title_lower for keyword in [
            'mid', 'mid-level', 'product manager', 'pm'
        ]):
            return SeniorityLevel.MID
        
        # Entry level detection
        if any(keyword in title_lower for keyword in [
            'entry', 'intern', 'coordinator', 'assistant'
        ]):
            return SeniorityLevel.ENTRY
        
        # Default to mid for plain PM titles
        return SeniorityLevel.MID
    
    def calculate_seniority_penalty(self, seniority_level: SeniorityLevel) -> float:
        """Calculate penalty based on seniority level."""
        return self.seniority_penalties.get(seniority_level, 0.0)
    
    def calculate_experience_fit_score(self, years_required: Optional[int] = None, years_offered: Optional[int] = None) -> Dict[str, Any]:
        """Calculate experience fit score for PM transition."""
        score_result = {
            "score": 0.0,
            "reason": "",
            "transition_friendly": False
        }
        
        if years_required is None:
            return score_result
        
        # Check if experience requirement is transition-friendly
        for (min_years, max_years), bonus in self.experience_bonuses.items():
            if min_years <= years_required <= max_years:
                score_result["score"] += bonus
                score_result["transition_friendly"] = True
                score_result["reason"] = f"Good experience fit ({min_years}-{max_years} years)"
                break
        else:
            # Apply penalties for too senior requirements
            for (min_years, max_years), penalty in self.experience_penalties.items():
                if min_years <= years_required <= max_years:
                    score_result["score"] += penalty
                    score_result["reason"] = f"Too senior for transition ({years_required}+ years)"
                    break
        
        return score_result
    
    def calculate_transition_friendliness_score(self, title: str, description: str, domain_tags: list = None) -> Dict[str, Any]:
        """Calculate transition friendliness score."""
        score = 0.0
        reasons = []
        
        title_lower = title.lower()
        desc_lower = description.lower()
        tags = domain_tags or []
        
        # Technical background boost
        technical_keywords = [
            'technical', 'api', 'platform', 'engineering', 'infrastructure',
            'saas', 'tooling', 'system', 'architecture', 'backend',
            'frontend', 'full-stack', 'devops', 'cloud'
        ]
        
        if any(keyword in title_lower for keyword in technical_keywords):
            score += 8.0
            reasons.append("Technical PM alignment")
        elif any(keyword in desc_lower for keyword in technical_keywords):
            score += 4.0
            reasons.append("Technical context in description")
        
        # Cross-functional collaboration boost
        collaboration_keywords = [
            'cross-functional', 'stakeholder', 'leadership', 'communication',
            'collaboration', 'partnership', 'integration'
        ]
        
        if any(keyword in desc_lower for keyword in collaboration_keywords):
            score += 3.0
            reasons.append("Cross-functional collaboration")
        
        # Startup/lean environment boost
        startup_keywords = [
            'startup', 'fast-paced', 'lean', 'agile', 'scrappy',
            'build', 'scale', 'growth', 'entrepreneurial'
        ]
        
        if any(keyword in desc_lower for keyword in startup_keywords):
            score += 5.0
            reasons.append("Startup-friendly environment")
        
        # Domain tag boosts
        if tags:
            if any(tag in tags for tag in ['api', 'platform', 'infrastructure']):
                score += 4.0
                reasons.append("API/Platform focus")
            
            if any(tag in tags for tag in ['saas', 'b2b', 'product-led']):
                score += 3.0
                reasons.append("SaaS/Product-led company")
        
        return {
            "score": score,
            "reasons": reasons,
            "transition_friendly": score > 5.0
        }
    
    def calculate_startup_friendliness_score(self, company: str, description: str, domain_tags: list = None) -> Dict[str, Any]:
        """Calculate startup friendliness score."""
        score = 0.0
        reasons = []
        
        company_lower = company.lower()
        desc_lower = description.lower()
        tags = domain_tags or []
        
        # Known startup indicators
        startup_indicators = [
            'series a', 'series b', 'series c', 'seed', 'venture',
            'startup', 'founded', 'early stage', 'growth stage'
        ]
        
        if any(indicator in desc_lower for indicator in startup_indicators):
            score += 6.0
            reasons.append("Startup environment indicators")
        
        # Lean PM organization indicators
        lean_indicators = [
            'lean', 'agile', 'small team', 'fast-paced',
            'builder', 'owner', 'autonomous'
        ]
        
        if any(indicator in desc_lower for indicator in lean_indicators):
            score += 4.0
            reasons.append("Lean PM organization")
        
        # Product-led SaaS indicators
        saas_indicators = [
            'saas', 'product-led', 'b2b', 'subscription',
            'platform', 'api-first'
        ]
        
        if any(indicator in desc_lower for indicator in saas_indicators):
            score += 3.0
            reasons.append("Product-led SaaS")
        
        # Avoid enterprise hierarchies
        enterprise_indicators = [
            'enterprise', 'fortune 500', 'large corporation',
            'bureaucracy', 'matrix organization', 'corporate ladder'
        ]
        
        if any(indicator in desc_lower for indicator in enterprise_indicators):
            score -= 5.0
            reasons.append("Enterprise hierarchy (penalty)")
        
        return {
            "score": score,
            "reasons": reasons,
            "startup_friendly": score > 3.0
        }
    
    def get_comprehensive_seniority_analysis(
        self,
        title: str,
        description: str = "",
        company: str = "",
        domain_tags: list = None,
        years_required: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive seniority analysis for PM transition."""
        
        # Detect seniority level
        seniority_level = self.detect_seniority_level(title, description, years_required)
        
        # Calculate scores
        seniority_penalty = self.calculate_seniority_penalty(seniority_level)
        experience_fit = self.calculate_experience_fit_score(years_required)
        transition_friendliness = self.calculate_transition_friendliness_score(title, description, domain_tags)
        startup_friendliness = self.calculate_startup_friendliness_score(company, description, domain_tags)
        
        # Calculate total score
        total_score = (
            seniority_penalty +
            experience_fit["score"] +
            transition_friendliness["score"] +
            startup_friendliness["score"]
        )
        
        # Generate comprehensive reason
        all_reasons = []
        if experience_fit["reason"]:
            all_reasons.append(experience_fit["reason"])
        if transition_friendliness["reasons"]:
            all_reasons.extend(transition_friendliness["reasons"])
        if startup_friendliness["reasons"]:
            all_reasons.extend(startup_friendliness["reasons"])
        
        reason = "; ".join(all_reasons) if all_reasons else "PM role alignment"
        
        return {
            "seniority_level": seniority_level.value,
            "seniority_penalty": seniority_penalty,
            "experience_fit_score": experience_fit["score"],
            "transition_friendliness_score": transition_friendliness["score"],
            "startup_friendliness_score": startup_friendliness["score"],
            "total_score": total_score,
            "reason": reason,
            "transition_friendly": (
                experience_fit["transition_friendly"] and
                transition_friendliness["transition_friendly"] and
                startup_friendliness["startup_friendly"]
            ),
            "details": {
                "seniority_level": seniority_level.value,
                "penalties_applied": {
                    "seniority": seniority_penalty,
                    "experience": experience_fit["score"],
                    "transition": transition_friendliness["score"],
                    "startup": startup_friendliness["score"]
                },
                "recommendations": self._get_recommendations(seniority_level, total_score)
            }
        }
    
    def _get_recommendations(self, seniority_level: SeniorityLevel, total_score: float) -> list:
        """Get recommendations based on seniority analysis."""
        recommendations = []
        
        if seniority_level in [SeniorityLevel.PRINCIPAL, SeniorityLevel.DIRECTOR, SeniorityLevel.EXECUTIVE]:
            recommendations.append("❌ Too senior for PM transition")
            recommendations.append("👥 Look for Associate/Technical PM roles")
        
        if total_score < -10:
            recommendations.append("⚠️ Consider more junior PM roles")
        
        if total_score > 5:
            recommendations.append("✅ Good PM transition fit")
        
        return recommendations


# Add missing enum values dynamically
SeniorityLevel.HEAD_OF_PRODUCT = "head_of_product"
SeniorityLevel.VP_PRODUCT = "vp_product"
SeniorityLevel.GROUP_PM = "group_pm"
