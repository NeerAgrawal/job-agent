#!/usr/bin/env python3
"""Simple test script for job fetchers."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.fetchers.orchestrator import FetcherOrchestrator
from app.database.repositories import JobRepository
from app.database.session import get_db_session
from app.core.logging import setup_logging, logger


async def test_simple_fetch():
    """Simple test of fetcher functionality."""
    setup_logging()
    
    try:
        print("🚀 Starting Simple Fetcher Test")
        print("=" * 50)
        
        # Test basic fetch
        orchestrator = FetcherOrchestrator()
        
        # Test fetching a few jobs
        jobs = await orchestrator.fetch_all_jobs(limit=3)
        
        if jobs:
            print(f"✅ Successfully fetched {len(jobs)} jobs:")
            for i, job in enumerate(jobs, 1):
                print(f"  {i}. {job.title} at {job.company}")
        else:
            print("❌ No jobs fetched")
        
        print("\n" + "=" * 50)
        print("✅ Simple fetcher test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main function for script execution."""
    try:
        success = asyncio.run(test_simple_fetch())
        if success:
            print("✅ All tests passed!")
            sys.exit(0)
        else:
            print("❌ Tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
