"""Shortlist exporter for CSV and Markdown formats."""

import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logging import logger


class ShortlistExporter:
    """Exports shortlist data to CSV and Markdown formats."""
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
    def export_to_csv(
        self,
        shortlist: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """Export shortlist to CSV format.
        
        Args:
            shortlist: List of shortlist jobs
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to exported CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_shortlist_{timestamp}.csv"
        
        csv_path = self.export_dir / filename
        
        # CSV columns
        fieldnames = [
            "rank",
            "title", 
            "company",
            "final_score",
            "semantic_score",
            "transition_score",
            "salary_score",
            "pm_category",
            "location",
            "source",
            "posted_at",
            "job_url",
            "relevance_reason"
        ]
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for job in shortlist:
                    row = {
                        "rank": job.get("rank", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "final_score": job.get("final_score", 0),
                        "semantic_score": job.get("semantic_score", 0),
                        "transition_score": job.get("transition_score", 0),
                        "salary_score": job.get("salary_score", 0),
                        "pm_category": job.get("pm_category", ""),
                        "location": job.get("location", ""),
                        "source": job.get("source", ""),
                        "posted_at": job.get("posted_at", ""),
                        "job_url": job.get("job_url", ""),
                        "relevance_reason": job.get("relevance_reason", "")
                    }
                    writer.writerow(row)
            
            logger.info(f"CSV exported to: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    def export_to_markdown(
        self,
        shortlist: List[Dict[str, Any]],
        stats: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export shortlist to Markdown format.
        
        Args:
            shortlist: List of shortlist jobs
            stats: Shortlist statistics
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to exported Markdown file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_shortlist_{timestamp}.md"
        
        md_path = self.export_dir / filename
        
        try:
            markdown_content = self._generate_markdown_content(shortlist, stats)
            
            with open(md_path, 'w', encoding='utf-8') as mdfile:
                mdfile.write(markdown_content)
            
            logger.info(f"Markdown exported to: {md_path}")
            return str(md_path)
            
        except Exception as e:
            logger.error(f"Failed to export Markdown: {e}")
            raise
    
    def _generate_markdown_content(
        self,
        shortlist: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> str:
        """Generate Markdown content for shortlist."""
        
        # Header
        content = []
        content.append("# Daily PM Shortlist")
        content.append("")
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Summary Stats
        content.append("## 📊 Summary")
        content.append("")
        content.append(f"- **Total Jobs Analyzed**: {stats['total_jobs_analyzed']}")
        content.append(f"- **Jobs Filtered Out**: {stats['jobs_filtered_out']}")
        content.append(f"- **Shortlist Count**: {stats['shortlist_count']}")
        content.append(f"- **Top Average Score**: {stats['top_average_score']}")
        content.append(f"- **Newest Job Age**: {stats['newest_job_age_days']} days")
        content.append("")
        
        # PM Category Distribution
        if stats['pm_category_distribution']:
            content.append("### PM Category Distribution")
            content.append("")
            for category, count in stats['pm_category_distribution'].items():
                emoji = {"pm": "✅", "reject": "❌", "unknown": "❓"}.get(category, "📝")
                content.append(f"- **{emoji} {category.title()}**: {count}")
            content.append("")
        
        # Jobs List
        content.append("## 🎯 Top PM Opportunities")
        content.append("")
        
        for job in shortlist:
            content.append(f"### #{job['rank']} {job['title']}")
            content.append("")
            content.append(f"**🏢 Company**: {job['company']}")
            content.append(f"**📍 Location**: {job['location']}")
            content.append(f"**⭐ Score**: {job['final_score']}")
            content.append(f"**🎯 Category**: {job['pm_category'].title()}")
            content.append(f"**🌐 Source**: {job['source']}")
            
            # Salary
            salary_display = self._format_salary(job.get("salary"))
            content.append(f"**💰 Salary**: {salary_display}")
            
            # Posted time
            posted_display = self._format_posted_time(job.get("posted_at"))
            content.append(f"**📅 Posted**: {posted_display}")
            
            # Why matched
            content.append(f"**📝 Why Matched**: {job['relevance_reason']}")
            
            # URL
            content.append(f"**🔗 Apply**: [{job['title']}]({job['job_url']})")
            content.append("")
            content.append("---")
            content.append("")
        
        # Footer
        content.append("## 📈 Notes")
        content.append("")
        content.append("- Jobs are ranked by AI scoring algorithm")
        content.append("- Only PM-relevant roles with minimum quality score are included")
        content.append("- Fresh jobs posted within last 7 days")
        content.append("")
        content.append("*Generated by Job AI Agent*")
        
        return "\n".join(content)
    
    def _format_salary(self, salary: Optional[float]) -> str:
        """Format salary for display."""
        if not salary or salary <= 0:
            return "Not specified"
        
        if salary < 80000:
            return f"${int(salary/1000)}k"
        elif salary < 120000:
            return f"${int(salary/1000)}k-${int(salary/5000)}k"
        else:
            return f"${int(salary/1000)}k+"
    
    def _format_posted_time(self, posted_at: Optional[str]) -> str:
        """Format posted time for display."""
        if not posted_at:
            return "Unknown"
        
        try:
            posted_dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
            days_ago = (datetime.utcnow() - posted_dt).days
            
            if days_ago <= 1:
                return "Today"
            elif days_ago <= 7:
                return f"{days_ago} days ago"
            else:
                return posted_dt.strftime('%Y-%m-%d')
                
        except Exception:
            return "Unknown"
