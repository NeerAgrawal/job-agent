#!/usr/bin/env python3
"""Minimal test for job fetchers."""

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


async def test_minimal():
    """Minimal test to verify basic functionality."""
    setup_logging()
    
    try:
        print("🚀 Starting Minimal Test")
        print("=" * 50)
        
        # Test database connection
        async with get_db_session() as session:
            job_repo = JobRepository(session)
            total_jobs = await job_repo.count()
            print(f"✅ Database connected, total jobs: {total_jobs}")
        
        print("\n" + "=" * 50)
        print("✅ Minimal test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main function for script execution."""
    try:
        success = asyncio.run(test_minimal())
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
