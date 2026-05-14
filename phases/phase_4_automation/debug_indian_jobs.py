import sys
import asyncio
from pathlib import Path

# Adjust Python Path to allow importing 'app'
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from app.database.session import get_db_session
from app.models.job import Job
from app.repositories.job import JobRepository
from app.services.ai.title_filters import get_title_category
from app.services.shortlist.generator import ShortlistGenerator
from sqlalchemy import select

async def main():
    print("🔎 Diagnostic: Inspecting Database for Indian Fetcher Jobs\n" + "="*70)
    
    generator = ShortlistGenerator()
    
    async with get_db_session() as session:
        repo = JobRepository(session)
        
        # Query all jobs from database
        stmt = select(Job)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        print(f"📊 Total jobs in database: {len(jobs)}")
        
        # Filter for Indian fetcher jobs
        indian_sources = ['naukri', 'cutshort', 'instahyre', 'naukri_browser', 'instahyre_browser']
        indian_jobs = [j for j in jobs if str(j.source).lower() in indian_sources or any(src in str(j.source).lower() for src in indian_sources)]
        
        print(f"🇮🇳 Indian fetcher jobs found: {len(indian_jobs)}")
        
        if not indian_jobs:
            print("❌ No Indian fetcher jobs found in database!")
            # Print all unique sources
            sources = set(str(j.source) for j in jobs)
            print(f"Available sources in DB: {sources}")
            return
            
        print("\n📋 Job Details & Shortlist Criteria Breakdown:")
        print(f"{'ID':<4} | {'Source':<15} | {'Title':<35} | {'Score':<6} | {'PM?':<4} | {'Valid URL?':<10}")
        print("-" * 95)
        
        for idx, job in enumerate(indian_jobs, 1):
            pm_cat = get_title_category(job.title)
            is_pm = pm_cat == "pm"
            url_valid = repo.validate_job_url(job.job_url)
            score = round(job.final_score, 2) if job.final_score is not None else "None"
            
            print(f"{idx:<4} | {str(job.source)[:15]:<15} | {str(job.title)[:35]:<35} | {str(score):<6} | {'✅' if is_pm else '❌':<4} | {'✅' if url_valid else '❌':<10}")
            if not url_valid:
                print(f"     ↪️ Invalid URL: {job.job_url}")

if __name__ == "__main__":
    asyncio.run(main())
