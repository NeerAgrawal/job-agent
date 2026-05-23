"""Resume variant generator for preset PM profiles."""

from typing import Dict, Any, Optional
from .optimizer import ResumeOptimizer
from app.core.logging import logger


class VariantGenerator:
    """Creates specialized, trustworthy variations of the master resume targeting distinct PM profiles."""
    
    def __init__(self):
        self.optimizer = ResumeOptimizer()
        self.logger = logger.bind(service="variant_generator")
        
        # Domain contexts to guide prioritization
        self.contexts = {
            "growth_pm_resume": (
                "growth, conversion, revenue, acquisition, a/b testing, funnels, "
                "ltv, monetization, signup, engagement, retention, optimization"
            ),
            "ai_pm_resume": (
                "ai, ml, artificial intelligence, machine learning, llm, genai, "
                "models, dataset, training, deep learning, natural language, data science"
            ),
            "platform_pm_resume": (
                "platform, api, scaling, microservices, systems, integrations, developer, "
                "latency, scalability, infrastructure, saas, architecture"
            ),
            "technical_pm_resume": (
                "technical, software, engineering, code, sql, database, cloud, "
                "aws, backend, system design, cicd, devops, automation"
            )
        }

    def generate_variant(self, parsed_resume: Dict[str, Any], variant_name: str) -> Optional[Dict[str, Any]]:
        """Fabricate optimized metadata package corresponding to a target variant name."""
        try:
            target_context = self.contexts.get(variant_name)
            
            if not target_context:
                self.logger.warning(f"Variant profile '{variant_name}' not defined. Defaulting to platform profile.")
                target_context = self.contexts["platform_pm_resume"]
                variant_name = "platform_pm_resume"
                
            self.logger.info(f"Generating variant profile for {variant_name}")
            
            # Use optimizer to prioritize content against pre-defined profile domain context
            optimized = self.optimizer.optimize_resume(parsed_resume, target_context)
            
            return {
                "variant": variant_name,
                "target_focus": variant_name.replace("_resume", "").replace("_", " ").title(),
                "optimized_sections": optimized["optimized_sections"],
                "optimized_bullets": optimized["optimized_bullets"],
                "optimized_skills": optimized["optimized_skills"],
                "tailoring_strategy": f"Derived variant focusing on {variant_name.replace('_', ' ')} requirements."
            }
            
        except Exception as e:
            self.logger.error(f"Variant generation failure: {e}")
            return None
            
    def get_recommended_variant(self, job_domain: str) -> str:
        """Return the appropriate variant handle based on matched job domain."""
        mapping = {
            "Growth": "growth_pm_resume",
            "AI / ML": "ai_pm_resume",
            "Platform / API": "platform_pm_resume",
            "Technical": "technical_pm_resume"
        }
        return mapping.get(job_domain, "platform_pm_resume")
