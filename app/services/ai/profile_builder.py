"""Candidate profile builder for creating structured candidate profiles."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.core.logging import logger


@dataclass
class CandidateProfile:
    """Structured candidate profile."""
    target_roles: List[str]
    skills: List[str]
    domains: List[str]
    preferred_locations: List[str]
    salary_preferences: Dict[str, Any]
    years_experience: Optional[int]
    technical_strength: str
    pm_transition_score: float
    ai_interest_score: float


class ProfileBuilder:
    """Convert parsed resume data into candidate profile."""
    
    def __init__(self):
        self.logger = logger.bind(service="profile_builder")
    
    async def build_profile(self, resume_data: Dict[str, Any]) -> CandidateProfile:
        """Build candidate profile from parsed resume data."""
        try:
            self.logger.info("Building candidate profile from resume data")
            
            # Determine target roles based on PM keywords
            target_roles = self._determine_target_roles(resume_data.get("pm_keywords", []))
            
            # Extract and normalize skills
            skills = self._normalize_skills(resume_data.get("skills", []))
            
            # Determine domain expertise
            domains = self._determine_domain_expertise(resume_data.get("domains", []))
            
            # Set preferred locations (could be configurable later)
            preferred_locations = ["Remote", "Bengaluru", "San Francisco", "New York"]
            
            # Calculate salary preferences based on experience and skills
            salary_preferences = self._calculate_salary_preferences(resume_data)
            
            # Extract years of experience
            years_experience = resume_data.get("years_experience")
            
            # Assess technical strength
            technical_strength = resume_data.get("technical_strength", "basic")
            
            # Calculate PM transition score
            pm_transition_score = self._calculate_pm_transition_score(resume_data)
            
            # Calculate AI interest score
            ai_interest_score = self._calculate_ai_interest_score(resume_data)
            
            return CandidateProfile(
                target_roles=target_roles,
                skills=skills,
                domains=domains,
                preferred_locations=preferred_locations,
                salary_preferences=salary_preferences,
                years_experience=years_experience,
                technical_strength=technical_strength,
                pm_transition_score=pm_transition_score,
                ai_interest_score=ai_interest_score
            )
            
        except Exception as e:
            self.logger.exception("Failed to build candidate profile")
            raise
    
    def _determine_target_roles(self, pm_keywords: List[str]) -> List[str]:
        """Determine target PM roles based on keywords."""
        role_mapping = {
            "product manager": ["Product Manager", "Senior Product Manager", "Principal Product Manager"],
            "program manager": ["Program Manager", "Senior Program Manager", "Technical Program Manager"],
            "project manager": ["Project Manager", "Senior Project Manager", "Program Manager"],
            "product owner": ["Product Owner", "Senior Product Owner", "Principal Product Owner"],
            "scrum master": ["Scrum Master", "Agile Coach"],
            "project coordinator": ["Project Coordinator", "Program Coordinator"]
        }
        
        target_roles = []
        for keyword in pm_keywords:
            keyword_lower = keyword.lower()
            for mapped_keyword, roles in role_mapping.items():
                if keyword_lower in mapped_keyword:
                    target_roles.extend(roles)
        
        return list(set(target_roles))
    
    def _normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize and categorize skills."""
        if not skills:
            return []
        
        # Skill categorization and normalization
        skill_categories = {
            "programming": ["python", "java", "javascript", "typescript", "sql"],
            "frontend": ["react", "vue", "angular", "html", "css"],
            "backend": ["django", "flask", "fastapi", "node", "express"],
            "devops": ["docker", "kubernetes", "jenkins", "ci/cd"],
            "cloud": ["aws", "gcp", "azure", "heroku"],
            "databases": ["postgresql", "mysql", "mongodb", "redis"],
            "pm_tools": ["jira", "confluence", "slack", "microsoft teams"]
        }
        
        normalized_skills = []
        for skill in skills:
            skill_lower = skill.lower().strip()
            
            # Categorize skill
            for category, category_skills in skill_categories.items():
                if any(cat_skill in skill_lower for cat_skill in category_skills):
                    normalized_skills.append(f"{category}:{skill}")
                    break
        
        return list(set(normalized_skills))
    
    def _determine_domain_expertise(self, domains: List[str]) -> List[str]:
        """Determine primary domain expertise."""
        if not domains:
            return []
        
        # Domain scoring based on PM relevance
        domain_scores = {
            "saas": 10, "fintech": 9, "healthcare": 8, "ecommerce": 7,
            "b2b": 9, "analytics": 8, "technology": 7, "education": 6,
            "media": 5, "retail": 6, "manufacturing": 5, "logistics": 6,
            "finance": 8, "insurance": 7, "banking": 7, "energy": 5,
            "transportation": 5, "real estate": 6
        }
        
        # Score domains based on presence and relevance
        scored_domains = []
        for domain in domains:
            domain_lower = domain.lower()
            score = domain_scores.get(domain_lower, 0)
            scored_domains.append((domain, score))
        
        # Sort by score and return top domains
        scored_domains.sort(key=lambda x: x[1], reverse=True)
        return [domain for domain, score in scored_domains[:5]]
    
    def _calculate_salary_preferences(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate salary preferences based on experience and skills."""
        years_exp = resume_data.get("years_experience", 0)
        technical_strength = resume_data.get("technical_strength", "basic")
        
        # Base salary calculation
        base_salary = 80000  # Base salary for 0 experience
        
        # Experience multiplier
        if years_exp:
            if years_exp >= 10:
                exp_multiplier = 2.0
            elif years_exp >= 5:
                exp_multiplier = 1.5
            else:
                exp_multiplier = 1.2
            base_salary *= exp_multiplier
        
        # Technical strength multiplier
        tech_multipliers = {
            "strong": 1.5,
            "moderate": 1.2,
            "basic": 1.0
        }
        base_salary *= tech_multipliers.get(technical_strength, 1.0)
        
        # AI interest premium
        ai_terms = resume_data.get("ai_terms", [])
        if ai_terms:
            base_salary *= 1.2  # 20% premium for AI interest
        
        return {
            "min_salary": int(base_salary * 0.9),
            "max_salary": int(base_salary * 1.3),
            "target_salary": int(base_salary * 1.1),
            "currency": "USD",
            "negotiation_range": "±20%"
        }
    
    def _calculate_pm_transition_score(self, resume_data: Dict[str, Any]) -> float:
        """Calculate PM transition readiness score."""
        score = 0.0
        
        # PM keywords present (30 points)
        pm_keywords = resume_data.get("pm_keywords", [])
        if pm_keywords:
            score += min(len(pm_keywords) * 5, 30)
        
        # PM tools present (20 points)
        tools = resume_data.get("tools", [])
        pm_tools = ["jira", "confluence", "slack", "microsoft teams"]
        pm_tools_count = sum(1 for tool in pm_tools if tool in str(tools).lower())
        score += min(pm_tools_count * 4, 20)
        
        # Domain relevance (25 points)
        domains = resume_data.get("domains", [])
        pm_relevant_domains = ["saas", "fintech", "b2b", "analytics", "technology"]
        domain_relevance = sum(1 for domain in domains if domain.lower() in pm_relevant_domains)
        score += min(domain_relevance * 5, 25)
        
        # Project/API experience (15 points)
        projects_apis = resume_data.get("projects_apis", [])
        if projects_apis:
            score += min(len(projects_apis) * 3, 15)
        
        # QA background (10 points)
        if resume_data.get("qa_background", False):
            score += 10
        
        return min(score, 100.0)
    
    def _calculate_ai_interest_score(self, resume_data: Dict[str, Any]) -> float:
        """Calculate AI interest and alignment score."""
        score = 0.0
        
        # AI/ML terms present (40 points)
        ai_terms = resume_data.get("ai_terms", [])
        if ai_terms:
            score += min(len(ai_terms) * 8, 40)
        
        # AI tools and frameworks (30 points)
        ai_tools = ["tensorflow", "pytorch", "scikit", "pandas", "numpy", "chatgpt", "openai"]
        tools = resume_data.get("tools", [])
        ai_tools_count = sum(1 for tool in ai_tools if tool in str(tools).lower())
        score += min(ai_tools_count * 6, 30)
        
        # AI-related projects (20 points)
        projects_apis = resume_data.get("projects_apis", [])
        ai_projects = ["api", "microservices", "machine learning", "nlp", "computer vision"]
        ai_project_count = sum(1 for project in projects_apis if any(ai_term in project.lower() for ai_term in ai_projects))
        score += min(ai_project_count * 5, 20)
        
        # Technical strength in AI (10 points)
        technical_strength = resume_data.get("technical_strength", "basic")
        if technical_strength in ["moderate", "strong"]:
            score += 10
        
        return min(score, 100.0)
