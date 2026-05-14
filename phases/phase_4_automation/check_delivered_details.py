import sys
import asyncio
from pathlib import Path

# Adjust Python Path to allow importing 'app'
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from app.database.session import get_db_session
from app.models.job import Job
from sqlalchemy import select, desc

async def main():
    print("🔍 Diagnostic: Reading Saved DB Job Details\n" + "="*80)
    async with get_db_session() as session:
        stmt = select(Job).order_by(desc(Job.created_at)).limit(10)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        for idx, job in enumerate(jobs, 1):
            print(f"{idx}. Title:  {job.title}")
            print(f"   Comp:   {job.company}")
            print(f"   Loc:    {job.location}")
            print(f"   Salary: {job.salary}")
            print(f"   URL:    {job.job_url}")
            print(f"   Reason: {job.relevance_reason}")
            print(f"   Score:  {job.final_score}")
            print("-" * 80)

if __name__ == "__main__":
    asyncio.run(main())
