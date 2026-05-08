"""Resume parser for extracting structured candidate information."""

import asyncio
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import PyPDF2
from docx import Document

from app.core.logging import logger


class ResumeParser:
    """Parse resumes from various formats and extract structured data."""
    
    def __init__(self):
        self.logger = logger.bind(service="resume_parser")
    
    async def parse_resume(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse resume file and extract structured information."""
        try:
            self.logger.info(f"Parsing resume: {file_path}")
            
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"Resume file not found: {file_path}")
                return None
            
            file_ext = path.suffix.lower()
            
            if file_ext == '.pdf':
                return await self._parse_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return await self._parse_docx(file_path)
            elif file_ext == '.txt':
                return await self._parse_txt(file_path)
            else:
                self.logger.warning(f"Unsupported file format: {file_ext}")
                return None
                
        except Exception as e:
            self.logger.exception(f"Failed to parse resume: {file_path}")
            return None
    
    async def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF resume."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                return self._extract_resume_data(text)
                
        except Exception as e:
            self.logger.exception(f"PDF parsing failed: {file_path}")
            raise
    
    async def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX resume."""
        try:
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return self._extract_resume_data(text)
            
        except Exception as e:
            self.logger.exception(f"DOCX parsing failed: {file_path}")
            raise
    
    async def _parse_txt(self, file_path: str) -> Dict[str, Any]:
        """Parse TXT resume."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            return self._extract_resume_data(text)
            
        except Exception as e:
            self.logger.exception(f"TXT parsing failed: {file_path}")
            raise
    
    def _extract_resume_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from resume text."""
        text_lower = text.lower()
        
        # Extract skills
        skills = self._extract_skills(text_lower)
        
        # Extract tools
        tools = self._extract_tools(text_lower)
        
        # Extract PM keywords
        pm_keywords = self._extract_pm_keywords(text_lower)
        
        # Extract domains
        domains = self._extract_domains(text_lower)
        
        # Extract years of experience
        years_exp = self._extract_years_experience(text_lower)
        
        # Extract projects/APIs
        projects_apis = self._extract_projects_apis(text_lower)
        
        # Extract AI-related terms
        ai_terms = self._extract_ai_terms(text_lower)
        
        return {
            "raw_text": text,
            "skills": skills,
            "tools": tools,
            "pm_keywords": pm_keywords,
            "domains": domains,
            "years_experience": years_exp,
            "projects_apis": projects_apis,
            "ai_terms": ai_terms,
            "qa_background": self._has_qa_background(text_lower),
            "technical_strength": self._assess_technical_strength(text_lower)
        }
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from text."""
        skill_patterns = [
            r'\b(python|java|javascript|typescript|sql|react|vue|angular|docker|kubernetes|aws|gcp|azure)\b',
            r'\b(agile|scrum|kanban|jira|confluence|git|ci\/cd|devops)\b',
            r'\b(api|rest|graphql|microservices|serverless|lambda|functions)\b',
            r'\b(django|flask|fastapi|express|spring|node)\b'
        ]
        
        skills = set()
        for pattern in skill_patterns:
            matches = [match.group() for match in re.finditer(pattern, text, re.IGNORECASE)]
            skills.update(matches)
        
        return list(skills)
    
    def _extract_tools(self, text: str) -> List[str]:
        """Extract tools and platforms from text."""
        tool_patterns = [
            r'\b(github|gitlab|bitbucket|jira|confluence|slack|teams|zoom)\b',
            r'\b(jenkins|circleci|travis|github actions|gitlab ci)\b',
            r'\b(aws|azure|gcp|heroku|netlify|vercel)\b',
            r'\b(docker|kubernetes|terraform|ansible|puppet)\b'
        ]
        
        tools = set()
        for pattern in tool_patterns:
            matches = [match.group() for match in re.finditer(pattern, text, re.IGNORECASE)]
            tools.update(matches)
        
        return list(tools)
    
    def _extract_pm_keywords(self, text: str) -> List[str]:
        """Extract PM-related keywords."""
        pm_patterns = [
            r'\b(product manager|program manager|project manager|pm|product owner|scrum master)\b',
            r'\b(product|program|project)\s+(management|coordination|leadership)\b',
            r'\b(stakeholder|roadmap|backlog|sprint|user story|agile)\b',
            r'\b(requirements|specifications|wireframes|prototypes|mvp)\b',
            r'\b(kpi|metrics|analytics|reporting|dashboard)\b'
        ]
        
        keywords = set()
        for pattern in pm_patterns:
            matches = [match.group() for match in re.finditer(pattern, text, re.IGNORECASE)]
            keywords.update(matches)
        
        return list(keywords)
    
    def _extract_domains(self, text: str) -> List[str]:
        """Extract domain expertise."""
        domain_patterns = [
            r'\b(fintech|healthcare|ecommerce|saas|b2b)\b',
            r'\b(education|technology|media|entertainment|retail)\b',
            r'\b(healthcare|finance|insurance|banking|real estate)\b',
            r'\b(manufacturing|logistics|transportation|energy)\b'
        ]
        
        domains = set()
        for pattern in domain_patterns:
            matches = [match.group() for match in re.finditer(pattern, text, re.IGNORECASE)]
            domains.update(matches)
        
        return list(domains)
    
    def _extract_years_experience(self, text: str) -> Optional[int]:
        """Extract years of experience."""
        # Look for patterns like "5 years", "5+ years", etc.
        exp_patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\s*-\s*(\d+)\s*years?',
            r'over\s+(\d+)\s*years?'
        ]
        
        max_years = 0
        for pattern in exp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    years = int(match[1])  # Take the higher number in ranges
                else:
                    years = int(match)
                max_years = max(max_years, years)
        
        return max_years if max_years > 0 else None
    
    def _extract_projects_apis(self, text: str) -> List[str]:
        """Extract project and API experience."""
        api_patterns = [
            r'\b(rest|graphql|soap|grpc)\b',
            r'\b(api|endpoint|microservice|serverless|webhook)\b',
            r'\b(paypal|stripe|twilio|sendgrid|aws\s+api|google\s+api)\b'
        ]
        
        apis = set()
        for pattern in api_patterns:
            matches = [match.group() for match in re.finditer(pattern, text, re.IGNORECASE)]
            apis.update(matches)
        
        return list(apis)
    
    def _extract_ai_terms(self, text: str) -> List[str]:
        """Extract AI-related terms."""
        ai_patterns = [
            r'\b(machine learning|artificial intelligence|ai|ml|nlp|computer vision)\b',
            r'\b(neural|deep learning|tensorflow|pytorch|scikit|pandas)\b',
            r'\b(chatgpt|gpt|openai|claude|bard|gemini)\b',
            r'\b(prompt|llm|generative ai|transformer)\b'
        ]
        
        terms = set()
        for pattern in ai_patterns:
            matches = [match.group() for match in re.finditer(pattern, text, re.IGNORECASE)]
            terms.update(matches)
        
        return list(terms)
    
    def _has_qa_background(self, text: str) -> bool:
        """Check if candidate has QA background."""
        qa_patterns = [
            r'\b(quality assurance|qa|testing|test automation|selenium|cypress)\b',
            r'\b(unit test|integration test|e2e|test case|bug|defect)\b',
            r'\b(jest|mocha|pytest|karma|jasmine)\b'
        ]
        
        for pattern in qa_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _assess_technical_strength(self, text: str) -> str:
        """Assess technical strength based on skills and tools."""
        technical_indicators = [
            'python', 'java', 'javascript', 'typescript', 'sql',
            'react', 'vue', 'angular', 'docker', 'kubernetes',
            'aws', 'gcp', 'azure', 'api', 'microservices',
            'django', 'flask', 'fastapi', 'git', 'ci/cd'
        ]
        
        found_indicators = 0
        for indicator in technical_indicators:
            if indicator in text.lower():
                found_indicators += 1
        
        # Assess strength based on technical indicators found
        if found_indicators >= 8:
            return "strong"
        elif found_indicators >= 5:
            return "moderate"
        elif found_indicators >= 3:
            return "basic"
        else:
            return "limited"
