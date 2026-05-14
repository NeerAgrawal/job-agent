import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, func

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.session import get_db_session
from app.models.job import Job

async def main():
    async with get_db_session() as session:
        # Group by source
        stmt = select(Job.source, func.count(Job.id)).group_by(Job.source)
        result = await session.execute(stmt)
        print("📊 --- Job Counts by Source ---")
        for source, count in result.all():
            print(f"• {source}: {count} jobs")
            
        # Check scored jobs count by source
        print("\n🎯 --- Scored Jobs by Source (final_score >= 45) ---")
        stmt = select(Job.source, func.count(Job.id)).where(Job.final_score >= 45.0).group_by(Job.source)
        result = await session.execute(stmt)
        for source, count in result.all():
            print(f"• {source}: {count} jobs")
            
        # Check remote status populating
        print("\n🏠 --- Remote Status Summary ---")
        stmt = select(Job.remote_status, func.count(Job.id)).group_by(Job.remote_status)
        result = await session.execute(stmt)
        for status, count in result.all():
            print(f"• {status}: {count} jobs")
            
        # Get some sample titles from Instahyre and Cutshort
        print("\n🦄 --- Recent Instahyre jobs (Samples) ---")
        stmt = select(Job.title, Job.company, Job.final_score).where(Job.source.like("%instahyre%")).limit(5)
        result = await session.execute(stmt)
        for title, company, score in result.all():
            print(f"• '{title}' at '{company}' | Score: {score}")
            
        print("\n✂️ --- Recent Cutshort jobs (Samples) ---")
        stmt = select(Job.title, Job.company, Job.final_score).where(Job.source.like("%cutshort%")).limit(5)
        result = await session.execute(stmt)
        for title, company, score in result.all():
            print(f"• '{title}' at '{company}' | Score: {score}")

if __name__ == "__main__":
    asyncio.run(main())
