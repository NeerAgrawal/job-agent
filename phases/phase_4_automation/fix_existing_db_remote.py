import sys
import asyncio
from pathlib import Path

# Adjust Python Path to allow importing 'app'
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from app.database.session import get_db_session
from app.models.job import Job
from sqlalchemy import select
from app.services.fetchers.browser.browser_utils import BrowserUtils

async def main():
    print("🛠️ DB Repair: Setting remote_status using content heuristics...")
    
    utils = BrowserUtils()
    
    async with get_db_session() as session:
        stmt = select(Job)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        fixed = 0
        for job in jobs:
            inferred = utils.determine_remote_status(job.location, job.jd_text, job.title)
            if inferred:
                job.remote_status = inferred
                fixed += 1
                print(f"✅ Job: {job.title[:30]} at {job.company[:20]} -> {inferred.capitalize()}")
        
        await session.commit()
        print(f"Successfully populated {fixed} remote_status records in SQLite!")

if __name__ == "__main__":
    asyncio.run(main())
