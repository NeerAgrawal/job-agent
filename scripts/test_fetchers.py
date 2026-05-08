#!/usr/bin/env python3
"""Test script for job fetchers."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.fetchers.orchestrator import FetcherOrchestrator
from app.repositories import JobRepository
from app.database.session import get_db_session
from app.core.logging import setup_logging, logger


async def test_all_fetchers():
    """Test all job fetchers."""
    setup_logging()
    
    orchestrator = FetcherOrchestrator()
    
    try:
        logger.info("Starting comprehensive fetcher test...")
        
        # Test basic fetch
        jobs = await orchestrator.fetch_all_jobs(limit=10)
        
        if jobs:
            logger.info(f"Successfully fetched {len(jobs)} jobs:")
            for i, job in enumerate(jobs, 1):
                logger.info(f"  {i}. {job.title} at {job.company}")
        
        # Test with filters
        logger.info("\nTesting with filters...")
        
        # PM roles filter
        pm_jobs = await orchestrator.fetch_all_jobs(
            limit=5,
            filters={"pm_roles_only": True}
        )
        logger.info(f"PM roles filter returned {len(pm_jobs)} jobs")
        
        # Location filter
        location_jobs = await orchestrator.fetch_all_jobs(
            limit=5,
            filters={"location": "San Francisco"}
        )
        logger.info(f"Location filter returned {len(location_jobs)} jobs")
        
        # Search filter
        search_jobs = await orchestrator.fetch_all_jobs(
            limit=5,
            filters={"search": "Product Manager"}
        )
        logger.info(f"Search filter returned {len(search_jobs)} jobs")
        
        # Get statistics
        stats = await orchestrator.get_statistics()
        logger.info(f"Fetch statistics: {stats}")
        
        # Save to database
        if jobs:
            save_result = await orchestrator.save_all_jobs(jobs)
            logger.info(f"Save result: {save_result}")
        
        logger.info("✅ Fetcher test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fetcher test failed: {e}")
        return False


async def test_individual_fetchers():
    """Test each individual fetcher."""
    setup_logging()
    
    orchestrator = FetcherOrchestrator()
    
    fetchers = ["greenhouse", "lever", "wellfound"]
    
    for source in fetchers:
        logger.info(f"\nTesting {source} fetcher...")
        
        try:
            jobs = await orchestrator.fetch_from_source(source, limit=3)
            
            if jobs:
                logger.info(f"  ✓ {source}: {len(jobs)} jobs fetched")
                for job in jobs:
                    logger.info(f"    - {job.title} ({job.company})")
            else:
                logger.warning(f"  ⚠️ {source}: No jobs found")
                
        except Exception as e:
            logger.error(f"  ❌ {source}: Error - {e}")


async def test_database_integration():
    """Test database integration."""
    setup_logging()
    
    try:
        logger.info("Testing database integration...")
        
        async with get_db_session() as session:
            job_repo = JobRepository(session)
            
            # Test database operations
            total_jobs = await job_repo.count()
            logger.info(f"Total jobs in database: {total_jobs}")
            
            # Test recent jobs
            recent_jobs = await job_repo.get_recent_jobs(days=7)
            logger.info(f"Recent jobs (7 days): {len(recent_jobs)}")
            
            # Test job creation
            from app.schemas.job import JobCreate
            test_job = JobCreate(
                title="Test Product Manager",
                company="Test Company",
                location="San Francisco, CA",
                salary=120000.0,
                source="Test",
                job_url="https://example.com/job/1",
                jd_text="Test job description for product manager role...",
                remote_status="remote"
            )
            
            created_job = await job_repo.create(test_job.dict())
            logger.info(f"Created test job: {created_job.title}")
            
        logger.info("✅ Database integration test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database integration test failed: {e}")
        return False


def main():
    """Main function for script execution."""
    try:
        print("🚀 Starting Job Fetcher Tests")
        print("=" * 50)
        
        # Test all fetchers
        success = asyncio.run(test_all_fetchers())
        
        if success:
            print("\n✅ All fetchers test completed!")
        else:
            print("\n❌ All fetchers test failed!")
        
        print("\n" + "=" * 50)
        
        # Test individual fetchers
        asyncio.run(test_individual_fetchers())
        
        print("\n" + "=" * 50)
        
        # Test database integration
        success = asyncio.run(test_database_integration())
        
        if success:
            print("✅ Database integration test completed!")
        else:
            print("❌ Database integration test failed!")
        
        print("\n🎯 All tests completed!")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
