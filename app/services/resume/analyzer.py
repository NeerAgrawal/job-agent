"""Resume analyzer for dissecting experience metrics, domains, and leadership signals."""

import re
from typing import Dict, Any, List
from app.core.logging import logger


class ResumeAnalyzer:
    """Extracts quantitative metrics, leadership signals, and domain vectors from resume content."""
    
    def __init__(self):
        self.logger = logger.bind(service="resume_analyzer")

    def analyze_structured_resume(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deduce key vector strengths from parsed resume segments."""
        bullets = parsed_data.get("experience_bullets", [])
        raw_text = parsed_data.get("raw_text", "")
        
        # 1. Extract metrics
        metrics = self._extract_metrics(bullets)
        
        # 2. Calculate Domain Vector Intensity
        domain_profile = self._calculate_domain_profile(raw_text)
        
        # 3. Identify Leadership & Impact signals
        leadership_signals = self._extract_leadership_signals(bullets)
        
        return {
            "metrics_detected": metrics,
            "metrics_count": len(metrics),
            "domain_profile": domain_profile,
            "dominant_domain": max(domain_profile, key=domain_profile.get) if domain_profile else "Generalist",
            "leadership_signals": leadership_signals
        }

    def _extract_metrics(self, bullets: List[str]) -> List[str]:
        """Identify existing bullets that contain numerical achievements."""
        metric_bullets = []
        
        # Regex to detect: %, $, $10M, 5x, 50% increase, 10,000 users, scale, revenue
        patterns = [
            r'\d+%',                              # 15%
            r'\$\s*\d+',                          # $500
            r'\b\d+x\b',                          # 3x
            r'\b(million|billion|k|m|b)\b',       # 5M, 10k
            r'\b(revenue|conversion|churn|nps)\b' # KPIs
        ]
        
        for bullet in bullets:
            for pattern in patterns:
                if re.search(pattern, bullet, re.IGNORECASE):
                    metric_bullets.append(bullet)
                    break
                    
        return metric_bullets

    def _calculate_domain_profile(self, text: str) -> Dict[str, float]:
        """Build relevance vector for PM sub-specialties."""
        text_lower = text.lower()
        
        domains = {
            "Growth": ["growth", "conversion", "revenue", "acquisition", "activation", "a/b testing", "funnel", "ltv", "cac", "monetization"],
            "AI / ML": ["ai", "ml", "machine learning", "llm", "nlp", "deep learning", "data science", "genai", "neural", "model training"],
            "Platform / API": ["api", "platform", "infrastructure", "microservices", "scaling", "saas", "developer", "integration", "latency"],
            "Technical": ["architecture", "cloud", "aws", "sql", "database", "backend", "systems", "performance", "deployment"]
        }
        
        profile = {}
        for domain, keywords in domains.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            profile[domain] = float(score)
            
        # Normalize if total score > 0
        total = sum(profile.values())
        if total > 0:
            for domain in profile:
                profile[domain] = round((profile[domain] / total) * 100, 1)
        else:
            for domain in profile:
                profile[domain] = 0.0
                
        return profile

    def _extract_leadership_signals(self, bullets: List[str]) -> List[str]:
        """Isolate bullets utilizing high-ownership verb structures."""
        signals = []
        
        verbs = [
            r'\b(led|managed|mentored|launched|defined|owned)\b',
            r'\b(spearheaded|established|designed|drove|negotiated)\b',
            r'\b(orchestrated|optimized|transformed|scaled)\b'
        ]
        
        for bullet in bullets:
            for verb_pattern in verbs:
                if re.search(verb_pattern, bullet, re.IGNORECASE):
                    signals.append(bullet)
                    break
                    
        return signals
