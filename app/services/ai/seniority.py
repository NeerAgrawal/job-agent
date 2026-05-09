"""Seniority detection and scoring for PM transition optimization."""

import re
from typing import Dict, Any, Optional
from enum import Enum

from app.core.logging import logger


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
        
        # Seniority penalties (negative scores)
        self.seniority_penalties = {
            SeniorityLevel.PRINCIPAL: -15.0,
            SeniorityLevel.LEAD: -12.0,
            SeniorityLevel.DIRECTOR: -20.0,
            SeniorityLevel.EXECUTIVE: -25.0,
            SeniorityLevel.HEAD_OF_PRODUCT: -18.0,  # Will be added dynamically
            SeniorityLevel.VP_PRODUCT: -22.0,      # Will be added dynamically
            SeniorityLevel.GROUP_PM: -16.0         # Will be added dynamically
        }
        
        # Experience fit bonuses
        self.experience_bonuses = {
            (2, 6): 8.0,    # Sweet spot for transition
            (0, 2): 4.0,    # Entry level friendly
            (6, 8): 2.0,    # Still acceptable
        }
        
        # Experience penalties
        self.experience_penalties = {
            (8, 15): -6.0,   # Too senior for transition
            (15, 25): -12.0,  # Definitely too senior
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
        if any(keyword in title_lower for keyword in keyword in [
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
