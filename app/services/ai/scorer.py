"""Scoring engine for comprehensive job evaluation."""

import asyncio
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from app.core.logging import logger


@dataclass
class JobScore:
    """Comprehensive job score result."""
    job_id: str
    title: str
    company: str
    semantic_score: float
    pm_role_score: float
    qa_to_pm_score: float
    api_platform_score: float
    ai_technical_score: float
    salary_score: float
    recency_score: float
    location_score: float
    final_score: float
    relevance_reason: str


class ScoringEngine:
    """Comprehensive scoring engine for job-resume matching."""
    
    def __init__(self):
        self.logger = logger.bind(service="scorer")
        
    async def score_job(
        self,
        job_data: Dict[str, Any],
        resume_profile: Dict[str, Any],
        semantic_similarity: float
    ) -> JobScore:
        """Score a job against a resume profile."""
        try:
            self.logger.info(f"Scoring job: {job_data.title}")
            
            # Initialize scores
            scores = {
                "semantic": 0.0,
                "pm_role": 0.0,
                "qa_to_pm": 0.0,
                "api_platform": 0.0,
                "ai_technical": 0.0,
                "salary": 0.0,
                "recency": 0.0,
                "location": 0.0
            }
            
            # 1. Semantic Similarity Score (25%)
            scores["semantic"] = self._score_semantic_similarity(semantic_similarity)
            
            # 2. PM Role Relevance Score (20%)
            scores["pm_role"] = self._score_pm_role_relevance(job_data, resume_profile)
            
            # 3. QA-to-PM Transition Score (15%)
            scores["qa_to_pm"] = self._score_qa_to_pm_transition(job_data, resume_profile)
            
            # 4. API/Platform Alignment Score (15%)
            scores["api_platform"] = self._score_api_platform_alignment(job_data, resume_profile)
            
            # 5. AI/Technical PM Alignment Score (15%)
            scores["ai_technical"] = self._score_ai_technical_alignment(job_data, resume_profile)
            
            # 6. Salary Desirability Score (10%)
            scores["salary"] = self._score_salary_desirability(job_data, resume_profile)
            
            # 7. Recency Score (5%)
            scores["recency"] = self._score_recency(job_data)
            
            # 8. Location Preference Score (5%)
            scores["location"] = self._score_location_preference(job_data, resume_profile)
            
            # Calculate final score
            final_score = sum(scores.values())
            
            # Generate relevance reason
            relevance_reason = self._generate_relevance_reason(scores, job_data, resume_profile)
            
            return JobScore(
                job_id=str(job_data.id),
                title=job_data.title,
                company=job_data.company,
                semantic_score=scores["semantic"],
                pm_role_score=scores["pm_role"],
                qa_to_pm_score=scores["qa_to_pm"],
                api_platform_score=scores["api_platform"],
                ai_technical_score=scores["ai_technical"],
                salary_score=scores["salary"],
                recency_score=scores["recency"],
                location_score=scores["location"],
                final_score=final_score,
                relevance_reason=relevance_reason
            )
            
        except Exception as e:
            self.logger.exception("Failed to score job")
            raise
    
    def _score_semantic_similarity(self, similarity: float) -> float:
        """Score semantic similarity component."""
        # Convert similarity to 0-100 scale
        similarity_score = min(similarity * 100, 100)
        
        # Apply diminishing returns for very high similarity
        if similarity_score >= 90:
            return 25.0
        elif similarity_score >= 80:
            return 22.5
        elif similarity_score >= 70:
            return 20.0
        elif similarity_score >= 60:
            return 17.5
        elif similarity_score >= 50:
            return 15.0
        else:
            return similarity_score * 0.25
    
    def _score_pm_role_relevance(self, job_data, resume_profile: Dict[str, Any]) -> float:
        """Score PM role relevance."""
        job_title = job_data.title.lower()
        job_description = job_data.jd_text.lower()
        
        # Target roles from resume
        target_roles = resume_profile.get("target_roles", [])
        
        # PM keyword matching
        pm_keywords = ["product manager", "program manager", "project manager", "pm", "product owner"]
        keyword_matches = sum(1 for keyword in pm_keywords if keyword in job_title or keyword in job_description)
        keyword_score = min(keyword_matches * 4, 20)
        
        # Role level matching
        seniority_keywords = ["senior", "lead", "principal", "director", "vp"]
        role_level_score = 0
        for keyword in seniority_keywords:
            if keyword in job_title:
                role_level_score += 5
        
        # Target role alignment
        role_alignment_score = 0
        for target_role in target_roles:
            if target_role.lower() in job_title:
                role_alignment_score += 8
        
        return min(keyword_score + role_level_score + role_alignment_score, 20)
    
    def _score_qa_to_pm_transition(self, job_data, resume_profile: Dict[str, Any]) -> float:
        """Score QA-to-PM transition fit."""
        job_description = job_data.jd_text.lower()
        
        # QA background in resume
        has_qa_background = resume_profile.get("qa_background", False)
        qa_score = 10 if has_qa_background else 0
        
        # PM transition indicators in job
        transition_keywords = ["transition", "grow", "career path", "advancement", "mentor", "lead"]
        transition_score = 0
        for keyword in transition_keywords:
            if keyword in job_description:
                transition_score += 3
        
        # Management experience indicators
        management_keywords = ["manage", "team", "lead", "coordinate", "oversee"]
        management_score = 0
        for keyword in management_keywords:
            if keyword in job_description:
                management_score += 2
        
        return min(qa_score + transition_score + management_score, 15)
    
    def _score_api_platform_alignment(self, job_data, resume_profile: Dict[str, Any]) -> float:
        """Score API/platform alignment."""
        job_description = job_data.jd_text.lower()
        
        # API-related keywords
        api_keywords = ["api", "rest", "graphql", "microservices", "serverless", "webhook", "endpoint"]
        api_matches = sum(1 for keyword in api_keywords if keyword in job_description)
        api_score = min(api_matches * 3, 15)
        
        # Platform keywords
        platform_keywords = ["platform", "ecosystem", "integration", "saas", "b2b"]
        platform_matches = sum(1 for keyword in platform_keywords if keyword in job_description)
        platform_score = min(platform_matches * 2, 10)
        
        return min(api_score + platform_score, 15)
    
    def _score_ai_technical_alignment(self, job_data, resume_profile: Dict[str, Any]) -> float:
        """Score AI/technical PM alignment."""
        job_description = job_data.jd_text.lower()
        
        # AI/ML keywords
        ai_keywords = ["ai", "machine learning", "ml", "nlp", "data science", "analytics", "artificial intelligence"]
        ai_matches = sum(1 for keyword in ai_keywords if keyword in job_description)
        ai_score = min(ai_matches * 3, 15)
        
        # Technical strength from resume
        technical_strength = resume_profile.get("technical_strength", "basic")
        tech_bonus = {"strong": 5, "moderate": 3, "basic": 0}
        tech_score = tech_bonus.get(technical_strength, 0)
        
        return min(ai_score + tech_score, 15)
    
    def _score_salary_desirability(self, job_data, resume_profile: Dict[str, Any]) -> float:
        """Score salary desirability."""
        job_salary = job_data.salary or 0
        salary_preferences = resume_profile.get("salary_preferences", {})
        
        if not job_salary or not salary_preferences:
            return 5.0
        
        target_salary = salary_preferences.get("target_salary", 80000)
        
        # Calculate salary alignment
        if job_salary >= target_salary:
            salary_score = 10
        elif job_salary >= target_salary * 0.8:
            salary_score = 8
        elif job_salary >= target_salary * 0.6:
            salary_score = 6
        else:
            salary_score = 3
        
        return salary_score
    
    def _score_recency(self, job_data) -> float:
        """Score job recency."""
        posted_at = job_data.posted_at
        if not posted_at:
            return 0.0
        
        from datetime import datetime, timedelta
        
        try:
            # Parse posted date
            if isinstance(posted_at, str):
                posted_date = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
            else:
                posted_date = posted_at
            
            # Calculate days since posting
            days_ago = (datetime.utcnow() - posted_date).days
            
            # Score based on recency
            if days_ago <= 7:
                return 5.0
            elif days_ago <= 30:
                return 3.0
            elif days_ago <= 90:
                return 1.0
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _score_location_preference(self, job_data, resume_profile: Dict[str, Any]) -> float:
        """Score location preference."""
        job_location = job_data.location.lower() if job_data.location else ""
        preferred_locations = [loc.lower() for loc in resume_profile.get("preferred_locations", [])]
        
        if job_location in preferred_locations:
            return 5.0
        elif "remote" in job_location:
            return 4.0
        else:
            return 1.0
    
    def _generate_relevance_reason(self, scores: Dict[str, float], job_data, resume_profile: Dict[str, Any]) -> str:
        """Generate human-readable relevance reason."""
        reasons = []
        
        # High scoring factors
        if scores["semantic"] >= 20:
            reasons.append("Strong semantic match")
        if scores["pm_role"] >= 15:
            reasons.append("PM role alignment")
        if scores["salary"] >= 8:
            reasons.append("Competitive salary")
        if scores["location"] >= 4:
            reasons.append("Preferred location")
        
        # Special cases
        job_title = job_data.title.lower()
        if "senior" in job_title and scores["pm_role"] >= 15:
            reasons.append("Senior PM position")
        
        if scores["ai_technical"] >= 12:
            reasons.append("AI/technical PM role")
        
        if not reasons:
            return "Moderate match"
        
        return ", ".join(reasons)
