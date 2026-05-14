import sys
import asyncio
import re
from pathlib import Path

# Adjust Python Path to allow importing 'app'
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from app.database.session import get_db_session
from app.models.job import Job
from sqlalchemy import select

def extract_company_from_url(url: str, title: str) -> str:
    """Identical logic to the deployed fallback parser."""
    try:
        if not url or 'naukri.com' not in url:
            return ""
        
        path = url.split('/')[-1]
        if not path:
            return ""
            
        slug = path.lower()
        
        if 'job-listings-' in slug:
            slug = slug.replace('job-listings-', '')
        
        title_slug = str(title).lower().replace(' ', '-')
        if title_slug in slug:
            slug = slug.replace(title_slug, '')
        
        for term in ['product-manager', 'technical-product-manager', 'apm', 'program-manager', 'pm']:
            slug = slug.replace(term, '')
        
        exp_match = re.search(r'-\d+-to-\d+-years(-\d+)?$', slug)
        if exp_match:
            slug = slug[:exp_match.start()]
        else:
            slug = re.sub(r'-\d+$', '', slug)
            slug = re.sub(r'-\d+-to-\d+-years$', '', slug)
        
        common_cities = ['bengaluru', 'bangalore', 'hyderabad', 'noida', 'mumbai', 'pune', 'delhi', 'chennai', 'india', 'gurgaon']
        for city in common_cities:
            slug = re.sub(r'-' + city + r'$', '', slug)
        
        slug = slug.strip('-').replace('-', ' ')
        
        if slug:
            return ' '.join(word.capitalize() for word in slug.split())
    except Exception:
        pass
    return ""

async def main():
    print("🛠️ DB Repair: Fixing missing company names using URL slugs...")
    
    async with get_db_session() as session:
        stmt = select(Job).where(Job.company == "Unknown")
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        print(f"Discovered {len(jobs)} jobs with 'Unknown' company.")
        
        fixed = 0
        for job in jobs:
            parsed_company = extract_company_from_url(job.job_url, job.title)
            if parsed_company:
                job.company = parsed_company
                fixed += 1
                print(f"✅ Fixed: {job.title} -> {parsed_company}")
        
        await session.commit()
        print(f"Successfully updated {fixed} company names in SQLite!")

if __name__ == "__main__":
    asyncio.run(main())
