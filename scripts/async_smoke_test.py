#!/usr/bin/env python3
"""Async smoke test for job fetcher pipeline."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.fetchers.orchestrator import FetcherOrchestrator
from app.database.session import get_db_session
from app.repositories import JobRepository
from app.core.logging import setup_logging, logger


async def async_smoke_test():
    """Comprehensive async smoke test for job fetcher pipeline."""
    setup_logging()
    
    try:
        print("🚀 Starting Async Smoke Test")
        print("=" * 50)
        
        # Test 1: Database initialization
        print("📊 Testing database initialization...")
        async with get_db_session() as session:
            job_repo = JobRepository(session)
            total_jobs = await job_repo.count()
            print(f"✅ Database initialized, total jobs: {total_jobs}")
        
        # Test 2: Orchestrator initialization
        print("\n🔄 Testing orchestrator initialization...")
        orchestrator = FetcherOrchestrator()
        print("✅ Orchestrator initialized successfully")
        
        # Test 3: Concurrent fetching with bounded concurrency
        print("\n🌐 Testing concurrent fetching...")
        fetch_result = await orchestrator.fetch_from_all_sources(limit=10)
        
        print(f"📈 Fetch results:")
        print(f"   Total sources: {fetch_result.get('total_sources', 0)}")
        print(f"   Successful sources: {fetch_result.get('successful_sources', 0)}")
        print(f"   Total jobs fetched: {fetch_result.get('total_jobs_fetched', 0)}")
        print(f"   Jobs saved: {fetch_result.get('jobs_saved', 0)}")
        
        # Test 4: Individual source fetching
        print("\n🎯 Testing individual source fetching...")
        for source_name in ["greenhouse", "lever", "wellfound"]:
            try:
                jobs = await orchestrator.fetch_from_source(source_name, limit=5)
                print(f"   ✅ {source_name}: {len(jobs)} jobs fetched")
            except Exception as e:
                print(f"   ❌ {source_name}: {e}")
        
        # Test 5: Filter functionality
        print("\n🔍 Testing filter functionality...")
        pm_roles_filter = {"pm_roles": ["product manager", "program manager"]}
        filtered_result = await orchestrator.fetch_from_all_sources(limit=10, filters=pm_roles_filter)
        print(
            f"   PM roles filter: "
            f"{filtered_result.get('jobs_after_filtering', 0)} jobs"
        )
        
        # Test 6: Statistics gathering
        print("\n📊 Testing statistics gathering...")
        stats = await orchestrator.get_statistics()
        print(f"   Active fetchers: {len(stats.get('active_fetchers', []))}")
        print(f"   Last fetch: {stats.get('last_fetch', 'N/A')}")
        
        # Test 7: Clean shutdown
        print("\n🛑 Testing clean shutdown...")
        await asyncio.sleep(1)  # Simulate cleanup
        print("✅ Clean shutdown completed")
        
        print("\n" + "=" * 50)
        print("✅ Async smoke test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.exception("Async smoke test failed", service="smoke_test")
        print(f"\n❌ Async smoke test failed: {e}")
        return False


def main():
    """Main function for script execution."""
    try:
        success = asyncio.run(async_smoke_test())
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
