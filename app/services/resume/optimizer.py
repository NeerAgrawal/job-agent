"""Safe, non-fabricating resume optimizer."""

import re
from typing import Dict, Any, List
from app.core.logging import logger


class ResumeOptimizer:
    """Tailors resume layout by reordering existing content for optimal keyword weight."""
    
    def __init__(self):
        self.logger = logger.bind(service="resume_optimizer")

    def optimize_resume(self, parsed_resume: Dict[str, Any], job_desc: str) -> Dict[str, Any]:
        """Create safe tailored structure based on job keywords."""
        bullets = parsed_resume.get("experience_bullets", [])
        job_desc_lower = job_desc.lower()
        
        # 1. Reorder Bullet Points safely
        optimized_bullets = self._prioritize_bullets(bullets, job_desc_lower)
        
        # 2. Adjust Section Importance Weightings
        sections = parsed_resume.get("sections", {})
        optimized_sections = dict(sections)
        
        # Format optimized experience text from the ordered bullets
        if "experience" in optimized_sections and optimized_bullets:
            # Join ordered bullets as formatted list
            optimized_sections["experience"] = "\n".join(f"• {b}" for b in optimized_bullets)
            
        # 3. Structure Optimized Skill Bank (sorting existing skills based on job demand)
        skills = parsed_resume.get("skills", [])
        optimized_skills = sorted(
            skills, 
            key=lambda s: 10 if s.lower() in job_desc_lower else 1, 
            reverse=True
        )
        
        return {
            "optimized_sections": optimized_sections,
            "optimized_bullets": optimized_bullets,
            "optimized_skills": optimized_skills,
            "original_skills": skills,
            "tailoring_strategy": "Prioritized metric impact and key semantic term alignment."
        }

    def _prioritize_bullets(self, bullets: List[str], keyword_context: str) -> List[str]:
        """Reorder existing bullet entries based on relevance score without mutating string content."""
        scored_bullets = []
        
        metric_patterns = [r'\d+%', r'\$', r'\b\d+x\b', r'\b(million|billion|k|m|b)\b']
        
        for bullet in bullets:
            score = 0
            bullet_lower = bullet.lower()
            
            # Factor 1: Direct keyword overlap with Job Description (High Weight)
            words = bullet_lower.split()
            for word in words:
                if len(word) > 3 and word in keyword_context:
                    score += 5
                    
            # Factor 2: Numerical Metric Weight (Medium weight boost for impact)
            for pattern in metric_patterns:
                if re.search(pattern, bullet, re.IGNORECASE):
                    score += 15
                    break
                    
            # Factor 3: Ownership / Leadership Verbs boost
            if any(v in bullet_lower for v in ["led", "managed", "spearheaded", "launched", "delivered"]):
                score += 10
                
            scored_bullets.append((score, bullet))
            
        # Sort descending by score
        scored_bullets.sort(key=lambda x: x[0], reverse=True)
        
        return [b[1] for b in scored_bullets]
