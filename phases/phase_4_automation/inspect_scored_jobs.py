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

async def main():
    async with get_db_session() as session:
        stmt = select(Job).where(Job.final_score.isnot(None))
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        print(f"Scored jobs found: {len(jobs)}")
        for idx, job in enumerate(jobs, 1):
            print(f"{idx}. {job.title} | Company: {job.company} | Score: {job.final_score} | Semantic: {job.semantic_score} | Rel Reason: {job.relevance_reason}")

if __name__ == "__main__":
    asyncio.run(main())
