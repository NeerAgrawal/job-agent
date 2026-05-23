"""PM fit analyzer for contrasting jobs and structured resumes."""

import re
from typing import Dict, Any, List
from app.core.logging import logger


class PMFitAnalyzer:
    """Calculates explicit ATS-style overlap scores and highlights skillset discrepancies."""
    
    def __init__(self):
        self.logger = logger.bind(service="pm_fit_analyzer")

    def analyze_fit(self, resume_data: Dict[str, Any], job_title: str, job_desc: str) -> Dict[str, Any]:
        """Generate granular fit scorecard comparing resume profile to role specifications."""
        try:
            job_title_lower = job_title.lower()
            job_desc_lower = job_desc.lower()
            
            resume_skills = [s.lower() for s in resume_data.get("skills", [])]
            resume_keywords = [k.lower() for k in resume_data.get("pm_keywords", [])]
            
            # 1. Identify Critical Skill Demands in Job
            job_skill_demands = self._extract_critical_demands(job_desc_lower)
            
            # 2. Keyword Overlap Math
            matched_skills = [skill for skill in job_skill_demands if any(skill in rs for rs in resume_skills + resume_keywords)]
            missing_skills = [skill for skill in job_skill_demands if skill not in matched_skills]
            
            overlap_pct = (len(matched_skills) / len(job_skill_demands)) * 100 if job_skill_demands else 50.0
            
            # 3. PM Domain Matrix matching
            job_domain = self._identify_job_domain(job_title_lower, job_desc_lower)
            domain_fit = 1.0 if job_domain == resume_data.get("dominant_domain", "Generalist") else 0.6
            
            # 4. Seniority Alignment
            seniority_fit = self._assess_seniority_alignment(
                job_title_lower, 
                resume_data.get("years_experience", 3)
            )
            
            # 5. Aggregated ATS-style Confidence Rating (0-100)
            ats_score = (
                (overlap_pct * 0.5) +
                (domain_fit * 30) +
                (seniority_fit * 20)
            )
            ats_score = min(max(round(ats_score, 1), 10.0), 100.0)
            
            # 6. Rationale builder
            strong_points = self._build_strengths(matched_skills, domain_fit, seniority_fit)
            weak_points = self._build_gaps(missing_skills, domain_fit, seniority_fit)
            
            return {
                "ats_fit_score": ats_score,
                "job_domain": job_domain,
                "domain_fit": "High" if domain_fit == 1.0 else "Medium",
                "keyword_overlap_pct": round(overlap_pct, 1),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "seniority_matched": "Yes" if seniority_fit == 1.0 else "Partial",
                "explanation": {
                    "strong_match": strong_points,
                    "weak_match": weak_points
                }
            }
            
        except Exception as e:
            self.logger.error(f"Fit assessment crash: {e}")
            return {"ats_fit_score": 50.0, "explanation": {"strong_match": ["General PM Alignment"], "weak_match": []}}

    def _extract_critical_demands(self, desc: str) -> List[str]:
        """Scan Job Description for high-priority technical/PM skill identifiers."""
        inventory = [
            "sql", "python", "api", "agile", "scrum", "jira", "roadmap", "mvp",
            "ab testing", "analytics", "saas", "b2b", "b2c", "microservices",
            "growth", "conversion", "ai", "ml", "llm", "wireframes", "stakeholders"
        ]
        
        found = [item for item in inventory if item in desc]
        return found if found else ["agile", "roadmap", "stakeholders"]  # Baseline demands

    def _identify_job_domain(self, title: str, desc: str) -> str:
        """Assess PM specialization of the target job."""
        if any(k in title or k in desc for k in ["growth", "acquisition", "funnel"]):
            return "Growth"
        if any(k in title or k in desc for k in ["ai", "ml", "intelligence", "llm"]):
            return "AI / ML"
        if any(k in title or k in desc for k in ["platform", "infra", "api"]):
            return "Platform / API"
        if any(k in title or k in desc for k in ["technical", "software", "backend"]):
            return "Technical"
        
        return "Generalist"

    def _assess_seniority_alignment(self, title: str, years_exp: int) -> float:
        """Score how candidate's years of experience maps to job level."""
        years = years_exp if years_exp else 3
        
        is_senior = any(k in title for k in ["senior", "sr", "lead", "principal", "director"])
        is_entry = any(k in title for k in ["associate", "apm", "junior", "intern"])
        
        if is_senior:
            return 1.0 if years >= 5 else (0.7 if years >= 3 else 0.4)
        elif is_entry:
            return 1.0 if years <= 4 else 0.8
        else:
            # Mid-level role
            return 1.0 if 2 <= years <= 7 else 0.7

    def _build_strengths(self, matches: List[str], domain_fit: float, seniority: float) -> List[str]:
        strengths = []
        if len(matches) >= 3:
            strengths.append(f"Strong core skill overlap ({', '.join(matches[:3])})")
        if domain_fit == 1.0:
            strengths.append("Perfect PM domain alignment")
        if seniority == 1.0:
            strengths.append("Candidate meets experience criteria")
        if not strengths:
            strengths.append("Baseline PM qualification matched")
        return strengths

    def _build_gaps(self, missing: List[str], domain_fit: float, seniority: float) -> List[str]:
        gaps = []
        if missing:
            gaps.append(f"Missing critical terms: {', '.join(missing[:3])}")
        if domain_fit < 1.0:
            gaps.append("Candidate profile is cross-domain")
        if seniority < 0.5:
            gaps.append("Target job is significantly senior for candidate")
        return gaps
