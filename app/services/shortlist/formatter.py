"""Shortlist formatter for cleaning and normalizing job data."""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.ai.title_filters import get_title_category
from app.core.logging import logger


class ShortlistFormatter:
    """Formats and cleans shortlist job data."""
    
    def __init__(self):
        self.max_description_length = 200
        
    def format_shortlist_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format a list of shortlist jobs."""
        formatted_jobs = []
        
        for job in jobs:
            formatted_job = self.format_job(job)
            formatted_jobs.append(formatted_job)
        
        return formatted_jobs
    
    def format_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Format individual job data."""
        formatted_job = job.copy()
        
        # Clean relevance reason
        formatted_job["relevance_reason"] = self.clean_relevance_reason(
            job.get("relevance_reason", "")
        )
        
        # Format salary display
        formatted_job["salary_display"] = self.format_salary_display(
            job.get("salary")
        )
        
        # Format recency display
        formatted_job["recency_display"] = self.format_recency_display(
            job.get("posted_at")
        )
        
        # Normalize location
        formatted_job["location_clean"] = self.normalize_location(
            job.get("location", "")
        )
        
        # Clean title
        formatted_job["title_clean"] = self.clean_title(job.get("title", ""))
        
        # Ensure PM category
        if "pm_category" not in formatted_job:
            formatted_job["pm_category"] = get_title_category(job.get("title", ""))
        
        # Truncate noisy descriptions
        if "description" in formatted_job:
            formatted_job["description_clean"] = self.truncate_description(
                formatted_job.get("description", "")
            )
        
        return formatted_job
    
    def clean_relevance_reason(self, reason: str) -> str:
        """Clean and normalize relevance reason."""
        if not reason:
            return "No reason provided"
        
        # Remove common noise patterns
        noise_patterns = [
            r'\s+',  # Multiple spaces
            r'[^\w\s\-\.\,\!\?\;\:]',  # Special characters except basic punctuation
            r'\b(very|really|quite|extremely|highly)\b',  # Weak intensifiers
        ]
        
        cleaned = reason.strip()
        
        # Apply noise patterns
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        # Capitalize first letter
        cleaned = cleaned.capitalize()
        
        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Return original if cleaning removed too much
        if len(cleaned) < 10:
            return reason.strip()
        
        return cleaned
    
    def format_salary_display(self, salary: Optional[float]) -> str:
        """Format salary for clean display."""
        if not salary or salary <= 0:
            return "Not specified"
        
        # Round to nearest 5k
        rounded_salary = round(salary / 5000) * 5000
        
        if rounded_salary < 120000:
            return f"${int(rounded_salary/1000)}k"
        else:
            return f"${int(rounded_salary/1000)}k+"
    
    def format_recency_display(self, posted_at: Optional[str]) -> str:
        """Format posted time for clean display."""
        if not posted_at:
            return "Unknown"
        
        try:
            posted_dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
            days_ago = (datetime.utcnow() - posted_dt).days
            
            if days_ago <= 1:
                return "Today"
            elif days_ago <= 2:
                return "Yesterday"
            elif days_ago <= 7:
                return f"{days_ago} days ago"
            elif days_ago <= 14:
                return "Last week"
            elif days_ago <= 30:
                return "This month"
            else:
                return posted_dt.strftime('%b %d')
                
        except Exception:
            return "Unknown"
    
    def normalize_location(self, location: str) -> str:
        """Normalize location for clean display."""
        if not location:
            return "Remote"
        
        # Clean location
        cleaned = location.strip()
        
        # Standardize remote indicators
        remote_patterns = [
            r'remote',
            r'work from home',
            r'wfh',
            r'anywhere',
            r'global'
        ]
        
        for pattern in remote_patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                return "Remote"
        
        # Extract city, state, country
        parts = [part.strip() for part in cleaned.split(',')]
        
        if len(parts) >= 2:
            # City, State/Country
            city = parts[0]
            state = parts[1]
            
            # Abbreviate common states
            state_abbr = {
                'california': 'CA',
                'new york': 'NY',
                'texas': 'TX',
                'washington': 'WA',
                'illinois': 'IL',
                'massachusetts': 'MA',
                'pennsylvania': 'PA'
            }
            
            state_lower = state.lower()
            if state_lower in state_abbr:
                state = state_abbr[state_lower]
            
            return f"{city}, {state}"
        
        return cleaned
    
    def clean_title(self, title: str) -> str:
        """Clean job title for display."""
        if not title:
            return "Unknown Role"
        
        # Remove common noise
        noise_patterns = [
            r'\s+',  # Multiple spaces
            r'[^\w\s\-\.\&]',  # Special characters except basic ones
        ]
        
        cleaned = title.strip()
        
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, ' ', cleaned)
        
        # Capitalize properly
        words = cleaned.split()
        capitalized_words = []
        
        for word in words:
            # Keep common abbreviations uppercase
            if word.upper() in ['PM', 'APM', 'AI', 'API', 'CEO', 'CTO', 'CPO']:
                capitalized_words.append(word.upper())
            else:
                capitalized_words.append(word.capitalize())
        
        return ' '.join(capitalized_words)
    
    def truncate_description(self, description: str) -> str:
        """Truncate description to reasonable length."""
        if not description:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', description.strip())
        
        if len(cleaned) <= self.max_description_length:
            return cleaned
        
        # Truncate at word boundary
        truncated = cleaned[:self.max_description_length]
        last_space = truncated.rfind(' ')
        
        if last_space > self.max_description_length * 0.8:
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def group_jobs_by_category(self, jobs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group jobs by PM category."""
        groups = {
            "Technical PM": [],
            "AI PM": [],
            "Platform/API PM": [],
            "APM / Junior PM": [],
            "General PM": []
        }
        
        for job in jobs:
            category = self.determine_pm_category(job)
            if category in groups:
                groups[category].append(job)
            else:
                groups["General PM"].append(job)
        
        return groups
    
    def determine_pm_category(self, job: Dict[str, Any]) -> str:
        """Determine detailed PM category from job data."""
        title = job.get("title", "").lower()
        domain_tags = job.get("domain_tags", [])
        
        # Technical PM
        if any(keyword in title for keyword in ["technical", "engineering", "infrastructure"]):
            return "Technical PM"
        
        # AI PM
        if any(keyword in title for keyword in ["ai", "machine learning", "ml", "data"]) or \
           any(tag in domain_tags for tag in ["ai", "machine learning", "data"]):
            return "AI PM"
        
        # Platform/API PM
        if any(keyword in title for keyword in ["platform", "api"]) or \
           any(tag in domain_tags for tag in ["platform", "api"]):
            return "Platform/API PM"
        
        # APM / Junior PM
        if any(keyword in title for keyword in ["associate", "junior", "apm", "entry"]):
            return "APM / Junior PM"
        
        # General PM
        return "General PM"
