#!/usr/bin/env python3
"""Smoke test for job fetcher pipeline."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.repositories import JobRepository
from app.database.session import get_db_session
from app.schemas.job import JobCreate
from app.core.logging import setup_logging, logger


async def smoke_test():
    """Smoke test the job fetcher pipeline."""
    setup_logging()
    
    try:
        print("🚀 Starting Smoke Test")
        print("=" * 50)
        
        # Initialize database
        async with get_db_session() as session:
            job_repo = JobRepository(session)
            
            # Test database operations
            print("\n📊 Testing database operations...")
            
            # Test job creation
            test_job = JobCreate(
                title="Smoke Test Product Manager",
                company="Smoke Test Company",
                location="San Francisco, CA",
                salary=120000.0,
                source="Smoke Test",
                job_url="https://example.com/job/1",
                jd_text="Test job description for smoke testing...",
                remote_status="remote"
            )
            
            created_job = await job_repo.create(test_job.model_dump())
            print(f"  ✅ Created job: {created_job.title}")
            
            # Test job retrieval
            retrieved_job = await job_repo.get_by_id(created_job.id)
            if retrieved_job:
                print(f"  ✅ Retrieved job: {retrieved_job.title}")
            else:
                print(f"  ❌ Failed to retrieve job")
            
            # Test job count
            total_jobs = await job_repo.count()
            print(f"  ✅ Total jobs in database: {total_jobs}")
            
            # Test recent jobs
            recent_jobs = await job_repo.get_recent_jobs(days=7)
            print(f"  ✅ Recent jobs (7 days): {len(recent_jobs)}")
        
        print("\n" + "=" * 50)
        print("✅ Smoke test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        return False


def main():
    """Main function for script execution."""
    try:
        success = asyncio.run(smoke_test())
        if success:
            print("✅ All smoke tests passed!")
            sys.exit(0)
        else:
            print("❌ Smoke test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
