"""Exporter for saving optimized resumes and analysis artifacts."""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from app.core.logging import logger


class ResumeExporter:
    """Saves formatted resume variants and analysis matrices to physical storage."""
    
    def __init__(self):
        self.logger = logger.bind(service="resume_exporter")
        # Define default export directory inside project root
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)

    def export_variant_to_markdown(self, variant_data: Dict[str, Any], candidate_name: str) -> str:
        """Serialize optimized sections into structured, ATS-friendly markdown."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            v_name = variant_data.get("variant", "pm_resume")
            
            filename = f"{candidate_name.replace(' ', '_')}_{v_name}_{timestamp}.md"
            file_path = self.export_dir / filename
            
            sections = variant_data.get("optimized_sections", {})
            
            content = []
            content.append(f"# {candidate_name}")
            content.append(f"*{variant_data.get('target_focus', 'Product Manager')}*\n")
            
            # Render Summary if present
            if "summary" in sections:
                content.append("## Professional Summary")
                content.append(sections["summary"])
                content.append("")
                
            # Render structured Skill Bank
            skills = variant_data.get("optimized_skills", [])
            if skills:
                content.append("## Core Competencies")
                content.append(", ".join(skills))
                content.append("")
                
            # Render Experience (containing the reordered bullets)
            if "experience" in sections:
                content.append("## Professional Experience")
                content.append(sections["experience"])
                content.append("")
                
            # Render other sections (education, projects)
            for s_title, s_content in sections.items():
                if s_title not in ["summary", "experience"]:
                    content.append(f"## {s_title.title()}")
                    content.append(s_content)
                    content.append("")
                    
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
                
            self.logger.info(f"Successfully exported resume variant to {file_path}")
            return str(file_path.resolve())
            
        except Exception as e:
            self.logger.error(f"Failed to export resume variant: {e}")
            return ""

    def export_fit_analysis(self, analysis: Dict[str, Any], job_title: str, company: str) -> str:
        """Save detailed fit report for review."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            clean_company = company.replace(" ", "_")
            filename = f"fit_{clean_company}_{timestamp}.json"
            file_path = self.export_dir / filename
            
            payload = {
                "job_title": job_title,
                "company": company,
                "generated_at": datetime.now().isoformat(),
                "analysis": analysis
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
                
            return str(file_path.resolve())
        except Exception as e:
            self.logger.error(f"Fit export failure: {e}")
            return ""
