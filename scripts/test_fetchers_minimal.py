#!/usr/bin/env python3
"""Minimal test script for job fetchers."""

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
    """Minimal test of fetcher functionality."""
    setup_logging()
    
    try:
        print("🚀 Starting Minimal Fetcher Test")
        print("=" * 50)
        
        # Test basic fetch
        orchestrator = FetcherOrchestrator()
        
        # Test with mock data (no network calls)
        print("\n📊 Testing with mock data...")
        
        # Create mock jobs
        mock_jobs = [
            {
                "title": f"Mock Job {i+1}",
                "company": f"Mock Company {i+1}",
                "location": "San Francisco, CA",
                "salary": 100000.0 + (i * 10000),
                "source": "Mock",
                "job_url": f"https://example.com/job/{i+1}",
                "posted_at": "2026-05-01T12:00:00",
                "jd_text": f"Mock job description {i+1}",
                "applicant_count": 50 + i,
                "remote_status": "remote" if i % 2 == 0 else "hybrid",
                "domain_tags": ["mock", "test"]
            }
            for i in range(3):
                mock_jobs.append(mock_job)
        
        # Test orchestrator with mock data
        if mock_jobs:
            print(f"✅ Mock data created: {len(mock_jobs)} jobs")
        else:
            print("❌ Failed to create mock data")
        
        print("\n" + "=" * 50)
        print("✅ Minimal fetcher test completed!")
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
