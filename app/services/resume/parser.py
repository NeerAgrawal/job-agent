"""Extended resume parser for ingestion and segmentation."""

import re
from typing import Dict, Any, Optional, List
from app.services.ai.resume_parser import ResumeParser
from app.core.logging import logger


class ExtendedResumeParser:
    """Extends base parsing with heuristic structural segmentation."""
    
    def __init__(self):
        self.base_parser = ResumeParser()
        self.logger = logger.bind(service="extended_resume_parser")

    async def parse_and_segment(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse a resume file and extract segmented components."""
        try:
            # 1. Extract core structured keywords using original logic
            base_data = await self.base_parser.parse_resume(file_path)
            if not base_data:
                return None
            
            raw_text = base_data.get("raw_text", "")
            
            # 2. Segment text sections
            sections = self._segment_sections(raw_text)
            
            # 3. Extract individual experience bullets
            experience_bullets = self._extract_experience_bullets(sections.get("experience", ""))
            
            return {
                **base_data,
                "sections": sections,
                "experience_bullets": experience_bullets
            }
            
        except Exception as e:
            self.logger.error(f"Failed to segment resume: {e}")
            return None

    def _segment_sections(self, text: str) -> Dict[str, str]:
        """Heuristically split text into key resume sections."""
        sections = {}
        
        # Section header definitions
        headers = {
            "experience": r'\b(experience|employment|work history|professional background)\b',
            "skills": r'\b(skills|technologies|technical skills|competencies)\b',
            "education": r'\b(education|academic history|degrees)\b',
            "projects": r'\b(projects|portfolio|key projects)\b',
            "summary": r'\b(summary|professional summary|profile|objective)\b'
        }
        
        # Find indices of headers
        found_headers = []
        lines = text.split("\n")
        
        for idx, line in enumerate(lines):
            cleaned_line = line.strip().lower()
            # Headers are usually short lines
            if len(cleaned_line) < 30:
                for sect_name, pattern in headers.items():
                    if re.search(pattern, cleaned_line):
                        found_headers.append((idx, sect_name))
                        break
        
        # Sort by line index
        found_headers.sort(key=lambda x: x[0])
        
        # Split content by indices
        if not found_headers:
            # Fallback if no headers detected
            sections["experience"] = text
            return sections
            
        for i in range(len(found_headers)):
            start_idx = found_headers[i][0]
            sect_name = found_headers[i][1]
            
            if i + 1 < len(found_headers):
                end_idx = found_headers[i+1][0]
            else:
                end_idx = len(lines)
                
            section_content = "\n".join(lines[start_idx+1:end_idx]).strip()
            sections[sect_name] = section_content
            
        return sections

    def _extract_experience_bullets(self, exp_text: str) -> List[str]:
        """Extract specific achievement/bullet lines from experience segment."""
        bullets = []
        lines = exp_text.split("\n")
        
        # Standard bullet chars
        bullet_patterns = r'^\s*[•\-\*·]\s*'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if re.match(bullet_patterns, line):
                cleaned = re.sub(bullet_patterns, '', line).strip()
                if cleaned:
                    bullets.append(cleaned)
            elif len(line) > 30:
                # If a line is reasonably long and does not start with bullet
                # it could be a bullet that lost formatting. Add for coverage.
                bullets.append(line)
                
        return bullets
