"""Comprehensive unit tests for Phase 6A: Resume Intelligence & Workflow Layer."""

import unittest
import os
import sys
import tempfile
from pathlib import Path

# Ensure correct root pathing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.resume.parser import ExtendedResumeParser
from app.services.resume.analyzer import ResumeAnalyzer
from app.services.resume.matcher import PMFitAnalyzer
from app.services.resume.optimizer import ResumeOptimizer
from app.services.resume.variants import VariantGenerator
from app.services.resume.exporter import ResumeExporter


class TestResumeIntelligence(unittest.TestCase):
    
    def setUp(self):
        # Dummy resume content mimicking core sections
        self.sample_resume_text = """
        JOHN DOE
        Product Manager
        
        SUMMARY
        Passionate Product Manager experienced in delivering SaaS scale platforms.
        
        EXPERIENCE
        • Led scaling efforts for core developer platform, improving API latency by 35%.
        • Spearheaded growth hacking funnel initiatives resulting in a $2M revenue lift.
        • Coordinated cross-functional engineering stakeholders across 3 major cycles.
        • Mentored junior team members on data science methodologies.
        
        SKILLS
        Python, AWS, API, SQL, Agile, Scrum, Jira, SaaS, Data Science
        
        EDUCATION
        BS Computer Science
        """
        
        # Parsed representation used by pipeline
        self.parsed_data = {
            "raw_text": self.sample_resume_text,
            "skills": ["Python", "AWS", "API", "SQL", "Agile", "Scrum", "Jira"],
            "pm_keywords": ["Product Manager", "stakeholders", "funnel"],
            "years_experience": 5,
            "sections": {
                "summary": "Passionate Product Manager experienced in delivering SaaS scale platforms.",
                "experience": "• Led scaling efforts for core developer platform, improving API latency by 35%.\n• Spearheaded growth hacking funnel initiatives resulting in a $2M revenue lift.\n• Coordinated cross-functional engineering stakeholders across 3 major cycles.",
                "skills": "Python, AWS, API, SQL, Agile, Scrum, Jira, SaaS, Data Science"
            },
            "experience_bullets": [
                "Led scaling efforts for core developer platform, improving API latency by 35%.",
                "Spearheaded growth hacking funnel initiatives resulting in a $2M revenue lift.",
                "Coordinated cross-functional engineering stakeholders across 3 major cycles."
            ]
        }

    def test_parser_segmentation(self):
        """Ensure heuristics cleanly segment headers and harvest bullets."""
        parser = ExtendedResumeParser()
        
        sections = parser._segment_sections(self.sample_resume_text)
        self.assertIn("summary", sections)
        self.assertIn("experience", sections)
        self.assertIn("skills", sections)
        
        bullets = parser._extract_experience_bullets(sections["experience"])
        self.assertTrue(len(bullets) >= 3)
        self.assertTrue(any("API latency" in b for b in bullets))

    def test_analyzer_metrics_and_profile(self):
        """Verify numerical metrics recovery and PM domain scoring."""
        analyzer = ResumeAnalyzer()
        analysis = analyzer.analyze_structured_resume(self.parsed_data)
        
        # Numerical checks
        self.assertTrue(len(analysis["metrics_detected"]) >= 2)
        self.assertTrue(any("35%" in m for m in analysis["metrics_detected"]))
        self.assertTrue(any("$2M" in m for m in analysis["metrics_detected"]))
        
        # Profile check
        self.assertIn("Growth", analysis["domain_profile"])
        self.assertIn("Platform / API", analysis["domain_profile"])

    def test_fit_analyzer_logic(self):
        """Verify ATS fit score aggregates and highlights gaps correctly."""
        matcher = PMFitAnalyzer()
        
        job_title = "Senior Growth Product Manager"
        job_desc = "Looking for a PM to run ab testing experiments, improve funnel conversion and metrics."
        
        fit_report = matcher.analyze_fit(
            self.parsed_data, 
            job_title, 
            job_desc
        )
        
        # Verify keys and logical output
        self.assertIn("ats_fit_score", fit_report)
        self.assertEqual(fit_report["job_domain"], "Growth")
        self.assertGreaterEqual(fit_report["ats_fit_score"], 30.0)
        
        # Check mismatch gap highlighting
        weak = fit_report["explanation"]["weak_match"]
        self.assertTrue(any("Missing critical" in item or "cross-domain" in item for item in weak) or not weak)

    def test_optimizer_safe_reordering(self):
        """Verify bullets are prioritized without changing content strings."""
        optimizer = ResumeOptimizer()
        
        # Job emphasizing APIs & Platform
        context = "Looking for platform engineer PM focused on microservices and API latency architectures."
        
        optimized = optimizer.optimize_resume(self.parsed_data, context)
        
        # The first bullet should now be the platform one due to direct semantic keyword matching
        best_bullet = optimized["optimized_bullets"][0]
        self.assertIn("API latency", best_bullet)
        
        # Ensure same number of bullets retained (non-destructive)
        self.assertEqual(len(optimized["optimized_bullets"]), 3)

    def test_variant_generation(self):
        """Verify distinct profiles map to specific optimization contexts."""
        generator = VariantGenerator()
        
        variant = generator.generate_variant(self.parsed_data, "ai_pm_resume")
        
        self.assertIsNotNone(variant)
        self.assertEqual(variant["variant"], "ai_pm_resume")
        self.assertEqual(variant["target_focus"], "Ai Pm")
        
        # Ensure recommended mapper works
        v_rec = generator.get_recommended_variant("AI / ML")
        self.assertEqual(v_rec, "ai_pm_resume")

    def test_exporter_creation(self):
        """Verify analytical and markdown exports write successfully to disk."""
        exporter = ResumeExporter()
        
        variant_payload = {
            "variant": "test_pm",
            "target_focus": "Testing Manager",
            "optimized_sections": self.parsed_data["sections"],
            "optimized_skills": self.parsed_data["skills"]
        }
        
        # Test Markdown save
        md_path = exporter.export_variant_to_markdown(variant_payload, "Test Candidate")
        self.assertTrue(os.path.exists(md_path))
        
        # Clean up
        try:
            os.remove(md_path)
        except:
            pass


if __name__ == "__main__":
    unittest.main()
