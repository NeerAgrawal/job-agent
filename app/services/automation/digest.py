"""Daily digest formatter for Telegram-friendly job summaries."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logging import logger


class DigestFormatter:
    """Formats daily job digests for Telegram delivery."""
    
    def __init__(self):
        self.logger = logger.bind(service="digest")
        self.max_jobs_per_digest = 10
        self.max_reason_length = 50
        self.max_title_length = 40
    
    def format_daily_digest(
        self,
        jobs: List[Dict[str, Any]],
        summary_stats: Dict[str, Any],
        include_all_jobs: bool = False
    ) -> str:
        """Format a daily digest for Telegram delivery."""
        try:
            # Filter and sort jobs
            filtered_jobs = self._filter_jobs(jobs, include_all_jobs)
            
            if not filtered_jobs:
                return self._format_empty_digest(summary_stats)
            
            # Build digest
            digest_parts = []
            
            # Header
            digest_parts.append(self._format_header(summary_stats))
            
            # Jobs
            digest_parts.append(self._format_jobs(filtered_jobs))
            
            # Summary
            digest_parts.append(self._format_summary(summary_stats))
            
            # Footer
            digest_parts.append(self._format_footer())
            
            return "\n".join(digest_parts)
            
        except Exception as e:
            self.logger.exception("Failed to format daily digest")
            return "📊 *Daily PM Job Digest*\n\n❌ Error formatting digest. Please check logs."
    
    def _filter_jobs(self, jobs: List[Dict[str, Any]], include_all_jobs: bool = False) -> List[Dict[str, Any]]:
        """Filter jobs for digest inclusion."""
        filtered = []
        
        for job in jobs:
            # Only include jobs with minimum score
            if job.get('final_score', 0) >= 45.0 or include_all_jobs:
                filtered.append(job)
        
        # Sort by score (descending)
        filtered.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        # Limit to max jobs
        return filtered[:self.max_jobs_per_digest]
    
    def _format_header(self, summary_stats: Dict[str, Any]) -> str:
        """Format digest header."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        job_count = summary_stats.get('shortlist_count', 0)
        
        header = f"📊 *Daily PM Job Digest*\n"
        header += f"📅 {date_str}\n"
        header += f"🎯 {job_count} top opportunities\n"
        
        return header
    
    def _format_jobs(self, jobs: List[Dict[str, Any]]) -> str:
        """Format jobs section."""
        if not jobs:
            return "❌ No jobs found today."
        
        jobs_section = ""
        
        for i, job in enumerate(jobs, 1):
            job_section = f"*{i}. {self._truncate_text(job.get('title', 'Unknown'), self.max_title_length)}*\n"
            job_section += f"🏢 {job.get('company', 'Unknown')}\n"
            job_section += f"📍 {job.get('location', 'Unknown')}\n"
            job_section += f"⭐ Score: {job.get('final_score', 0):.1f}\n"
            job_section += f"🎯 {job.get('pm_category', 'PM')}\n"
            
            # Salary if available
            salary = job.get('salary', 'Not specified')
            if salary and salary != 'Not specified':
                job_section += f"💰 {salary}\n"
            
            # Why matched (truncated)
            reason = job.get('relevance_reason', 'No reason provided')
            job_section += f"📝 {self._truncate_text(reason, self.max_reason_length)}\n"
            
            # Direct URL
            job_url = job.get('job_url', '')
            if job_url:
                job_section += f"🔗 [Apply]({job_url})\n"
            
            job_section += "\n"
            jobs_section += job_section
        
        return jobs_section
    
    def _format_summary(self, summary_stats: Dict[str, Any]) -> str:
        """Format summary section."""
        summary = f"📈 *Summary*\n"
        summary += f"🔍 Jobs analyzed: {summary_stats.get('total_analyzed', 0)}\n"
        summary += f"🎯 Shortlisted: {summary_stats.get('shortlist_count', 0)}\n"
        summary += f"⭐ Avg score: {summary_stats.get('avg_score', 0):.1f}\n"
        
        # Add category distribution if available
        category_dist = summary_stats.get('category_distribution', {})
        if category_dist:
            summary += f"📋 Categories: {len(category_dist)}\n"
        
        return summary
    
    def _format_footer(self) -> str:
        """Format digest footer."""
        return "💼 *Daily PM Opportunities* - Powered by AI"
    
    def _format_empty_digest(self, summary_stats: Dict[str, Any]) -> str:
        """Format empty digest when no jobs found."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        digest = f"📊 *Daily PM Job Digest*\n"
        digest += f"📅 {date_str}\n\n"
        digest += "❌ No new jobs found today.\n\n"
        
        if summary_stats.get('total_analyzed', 0) > 0:
            digest += f"🔍 Jobs analyzed: {summary_stats.get('total_analyzed', 0)}\n"
            digest += "🎯 None met quality threshold\n"
        
        return digest
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length."""
        if not text:
            return "Not specified"
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."
    
    def format_test_digest(self) -> str:
        """Format a test digest for verification."""
        test_jobs = [
            {
                'title': 'Associate Product Manager',
                'company': 'Tech Startup',
                'location': 'Remote',
                'final_score': 65.2,
                'pm_category': 'Associate PM',
                'salary': '$80k-$100k',
                'relevance_reason': 'Strong PM transition fit with technical background',
                'job_url': 'https://example.com/job1'
            },
            {
                'title': 'Technical Product Manager',
                'company': 'AI Company',
                'location': 'San Francisco',
                'final_score': 62.1,
                'pm_category': 'Technical PM',
                'salary': '$120k-$150k',
                'relevance_reason': 'API/platform alignment with engineering collaboration',
                'job_url': 'https://example.com/job2'
            }
        ]
        
        test_summary = {
            'total_analyzed': 15,
            'shortlist_count': 2,
            'avg_score': 63.65,
            'category_distribution': {'Associate PM': 1, 'Technical PM': 1}
        }
        
        return self.format_daily_digest(test_jobs, test_summary, include_all_jobs=True)
    
    def format_error_digest(self, error_message: str) -> str:
        """Format an error digest."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        digest = f"📊 *Daily PM Job Digest*\n"
        digest += f"📅 {date_str}\n\n"
        digest += f"❌ *Error occurred*\n\n"
        digest += f"🔍 {self._truncate_text(error_message, 100)}\n\n"
        digest += "💼 *Daily PM Opportunities* - Powered by AI"
        
        return digest
