#!/usr/bin/env python3

"""Generate daily PM job shortlist."""

import asyncio
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.database.engine import engine
from app.services.shortlist import ShortlistGenerator, ShortlistExporter
from app.services.shortlist.cleanup import JobCleanup
from app.core.logging import logger


async def main():
    """Main function to generate daily shortlist."""
    
    print("🚀 Starting Daily PM Shortlist Generation")
    print("=" * 60)
    
    try:
        # Initialize services
        generator = ShortlistGenerator()
        exporter = ShortlistExporter()
        cleanup = JobCleanup()
        
        # Step 1: Cleanup old jobs
        print("\n🧹 Cleaning up stale jobs...")
        cleanup_stats = await cleanup.cleanup_stale_jobs()
        print(f"   ✅ Removed {cleanup_stats['stale_jobs_removed']} stale jobs")
        print(f"   ✅ Removed {cleanup_stats['invalid_urls_removed']} invalid URLs")
        print(f"   ✅ Removed {cleanup_stats['low_quality_removed']} low-quality jobs")
        print(f"   ✅ Removed {cleanup_stats['duplicate_urls_removed']} duplicate URLs")
        
        # Step 2: Generate shortlist
        print("\n📋 Generating daily shortlist...")
        resume_path = project_root / "data" / "resume.pdf"
        
        # Check if resume exists
        if not resume_path.exists():
            print(f"   ⚠️ Resume not found at {resume_path}, using existing scores")
            resume_path = None
        
        shortlist_result = await generator.generate_daily_shortlist(
            resume_path=str(resume_path) if resume_path else None,
            limit=10
        )
        
        # Step 3: Export results
        print("\n📤 Exporting shortlist...")
        
        # Export to CSV
        csv_path = exporter.export_to_csv(shortlist_result["jobs"])
        print(f"   ✅ CSV exported: {csv_path}")
        
        # Export to Markdown
        md_path = exporter.export_to_markdown(
            shortlist_result["jobs"], 
            shortlist_result["stats"]
        )
        print(f"   ✅ Markdown exported: {md_path}")
        
        # Step 4: Display summary
        print("\n📊 Daily Shortlist Summary")
        print("=" * 60)
        
        stats = shortlist_result["stats"]
        print(f"📈 Total Jobs Analyzed: {stats['total_jobs_analyzed']}")
        print(f"🔍 Jobs Filtered Out: {stats['jobs_filtered_out']}")
        print(f"🎯 Shortlist Count: {stats['shortlist_count']}")
        print(f"⭐ Top Average Score: {stats['top_average_score']}")
        print(f"📅 Newest Job Age: {stats['newest_job_age_days']} days")
        
        # PM Category Distribution
        if stats['pm_category_distribution']:
            print("\n📋 PM Category Distribution:")
            for category, count in stats['pm_category_distribution'].items():
                emoji = {"pm": "✅", "reject": "❌", "unknown": "❓"}.get(category, "📝")
                print(f"   {emoji} {category.title()}: {count}")
        
        # Top 3 Jobs
        if shortlist_result["jobs"]:
            print("\n🏆 Top 3 Opportunities:")
            for i, job in enumerate(shortlist_result["jobs"][:3], start=1):
                print(f"\n{i}. {job['title']} at {job['company']}")
                print(f"   📍 {job['location']} | ⭐ {job['final_score']} | 🎯 {job['pm_category'].title()}")
                print(f"   💰 {job.get('salary_display', 'Not specified')} | 📅 {job.get('recency_display', 'Unknown')}")
                print(f"   📝 {job['relevance_reason']}")
                print(f"   🔗 {job['job_url']}")
        
        print("\n" + "=" * 60)
        print("✅ Daily PM Shortlist Generation Complete!")
        print(f"📁 Check exports/ directory for files")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Daily shortlist generation failed: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    finally:
        # Dispose the pool or aiosqlite's non-daemon threads keep this script
        # alive after it has finished, holding a lock on data/jobs.db.
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
