#!/usr/bin/env python3
"""
Test script for Telegram delivery functionality.

This script tests:
- Telegram bot connection
- Message formatting
- Digest generation
- Duplicate prevention

Usage:
    python scripts/test_telegram_delivery.py [--test-digest] [--test-connection] [--send-test]
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.automation.telegram import TelegramService
from app.services.automation.digest import DigestFormatter
from app.services.automation.delivery_tracker import DeliveryTracker
from app.core.logging import logger


async def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Test Telegram Delivery")
    parser.add_argument("--test-connection", action="store_true", help="Test Telegram connection")
    parser.add_argument("--send-test", action="store_true", help="Send test message")
    parser.add_argument("--test-digest", action="store_true", help="Generate and show test digest")
    parser.add_argument("--test-duplicate", action="store_true", help="Test duplicate prevention")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logger.remove()
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
    
    try:
        telegram_service = TelegramService()
        digest_formatter = DigestFormatter()
        delivery_tracker = DeliveryTracker()
        
        if args.test_connection:
            await test_connection(telegram_service)
        
        if args.test_digest:
            await test_digest(digest_formatter)
        
        if args.send_test:
            await send_test_message(telegram_service, digest_formatter)
        
        if args.test_duplicate:
            await test_duplicate_prevention(delivery_tracker)
        
        # Default: run all tests
        if not any([args.test_connection, args.test_digest, args.send_test, args.test_duplicate]):
            await run_all_tests(telegram_service, digest_formatter, delivery_tracker)
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


async def test_connection(telegram_service: TelegramService) -> None:
    """Test Telegram bot connection."""
    print("🔗 Testing Telegram Connection")
    print("=" * 40)
    
    if not telegram_service.is_enabled():
        print("❌ Telegram service not configured")
        print("📝 Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return
    
    print("🔍 Testing bot connection...")
    connection_ok = await telegram_service.test_connection()
    
    if connection_ok:
        print("✅ Connection successful!")
        print("📱 Bot is ready to send messages")
    else:
        print("❌ Connection failed!")
        print("🔍 Check bot token and network connection")


async def test_digest(digest_formatter: DigestFormatter) -> None:
    """Test digest formatting."""
    print("📝 Testing Digest Formatting")
    print("=" * 40)
    
    print("🔄 Generating test digest...")
    test_digest = digest_formatter.format_test_digest()
    
    print("✅ Test digest generated:")
    print("-" * 40)
    print(test_digest)
    print("-" * 40)
    
    print(f"📊 Digest length: {len(test_digest)} characters")
    
    # Test message splitting
    telegram_service = TelegramService()
    chunks = telegram_service._split_message(test_digest) if hasattr(telegram_service, '_split_message') else [test_digest]
    print(f"📦 Message chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"   Chunk {i}: {len(chunk)} characters")


async def send_test_message(telegram_service: TelegramService, digest_formatter: DigestFormatter) -> None:
    """Send test message to Telegram."""
    print("📤 Sending Test Message")
    print("=" * 40)
    
    if not telegram_service.is_enabled():
        print("❌ Telegram service not configured")
        return
    
    print("🔄 Generating test digest...")
    test_digest = digest_formatter.format_test_digest()
    
    print("📤 Sending to Telegram...")
    success = await telegram_service.send_long_message(test_digest)
    
    if success:
        print("✅ Test message sent successfully!")
        print("📱 Check your Telegram for the test digest")
    else:
        print("❌ Failed to send test message!")
        print("🔍 Check logs for detailed error information")


async def test_duplicate_prevention(delivery_tracker: DeliveryTracker) -> None:
    """Test duplicate prevention."""
    print("🚫 Testing Duplicate Prevention")
    print("=" * 40)
    
    # Test data
    test_jobs = [
        {
            'title': 'Associate Product Manager',
            'company': 'Tech Startup',
            'job_url': 'https://example.com/job1',
            'final_score': 65.2
        },
        {
            'title': 'Technical Product Manager',
            'company': 'AI Company',
            'job_url': 'https://example.com/job2',
            'final_score': 62.1
        },
        {
            'title': 'Associate Product Manager',  # Duplicate URL
            'company': 'Tech Startup',
            'job_url': 'https://example.com/job1',
            'final_score': 65.2
        }
    ]
    
    print(f"📊 Testing with {len(test_jobs)} jobs (1 duplicate)...")
    
    # Mark first job as delivered
    await delivery_tracker.mark_job_delivered(
        job_url='https://example.com/job1',
        delivery_method='telegram',
        delivery_status='success'
    )
    
    # Filter jobs
    filtered_jobs = await delivery_tracker.filter_undelivered_jobs(test_jobs)
    
    print(f"✅ Original jobs: {len(test_jobs)}")
    print(f"✅ Filtered jobs: {len(filtered_jobs)}")
    print(f"🚫 Duplicates removed: {len(test_jobs) - len(filtered_jobs)}")
    
    print("\n📋 Remaining jobs:")
    for job in filtered_jobs:
        print(f"   - {job.get('title')} at {job.get('company')}")
    
    # Get stats
    stats = await delivery_tracker.get_delivery_stats()
    print(f"\n📊 Delivery stats:")
    print(f"   Total delivered: {stats['total_delivered']}")
    print(f"   Recent deliveries: {stats['recent_deliveries']}")
    print(f"   Success rate: {stats['recent_success_rate']:.1%}")


async def run_all_tests(
    telegram_service: TelegramService,
    digest_formatter: DigestFormatter,
    delivery_tracker: DeliveryTracker
) -> None:
    """Run all tests."""
    print("🧪 Running All Telegram Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Connection
    print("\n1️⃣ Testing Connection...")
    if telegram_service.is_enabled():
        connection_ok = await telegram_service.test_connection()
        if connection_ok:
            print("✅ Connection test passed")
            tests_passed += 1
        else:
            print("❌ Connection test failed")
    else:
        from app.core.config.settings import settings

        print(settings.telegram_bot_token)
        print(settings.telegram_chat_id)
        print("⚠️ Connection test skipped (not configured)")
    
    # Test 2: Digest formatting
    print("\n2️⃣ Testing Digest Formatting...")
    try:
        test_digest = digest_formatter.format_test_digest()
        if test_digest and len(test_digest) > 100:
            print("✅ Digest formatting test passed")
            tests_passed += 1
        else:
            print("❌ Digest formatting test failed")
    except Exception as e:
        print(f"❌ Digest formatting test failed: {e}")
    
    # Test 3: Message splitting
    print("\n3️⃣ Testing Message Splitting...")
    try:
        long_text = "A" * 5000  # Long text to test splitting
        chunks = telegram_service._split_message(long_text)
        if len(chunks) > 1:
            print("✅ Message splitting test passed")
            tests_passed += 1
        else:
            print("❌ Message splitting test failed")
    except Exception as e:
        print(f"❌ Message splitting test failed: {e}")
    
    # Test 4: Duplicate prevention
    print("\n4️⃣ Testing Duplicate Prevention...")
    try:
        await delivery_tracker.mark_job_delivered(
            job_url='https://test.com/job1',
            delivery_method='test',
            delivery_status='success'
        )
        
        test_jobs = [
            {'job_url': 'https://test.com/job1'},
            {'job_url': 'https://test.com/job2'}
        ]
        
        filtered = await delivery_tracker.filter_undelivered_jobs(test_jobs)
        if len(filtered) == 1:
            print("✅ Duplicate prevention test passed")
            tests_passed += 1
        else:
            print("❌ Duplicate prevention test failed")
    except Exception as e:
        print(f"❌ Duplicate prevention test failed: {e}")
    
    # Summary
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed!")
        print("🚀 Telegram delivery system is ready")
    else:
        print("⚠️ Some tests failed")
        print("🔍 Check configuration and logs")
    
    # Offer to send test message if configured
    if telegram_service.is_enabled() and tests_passed >= 2:
        print("\n📤 Send test message to Telegram? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                await send_test_message(telegram_service, digest_formatter)
        except KeyboardInterrupt:
            print("\n🛑 Test cancelled")


if __name__ == "__main__":
    asyncio.run(main())
