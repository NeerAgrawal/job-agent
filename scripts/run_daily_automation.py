#!/usr/bin/env python3
"""
Daily automation script for PM job processing and Telegram delivery.

This script runs the complete daily pipeline:
1. Cleanup old jobs
2. Fetch fresh jobs
3. Run AI scoring
4. Generate shortlist
5. Export CSV/Markdown
6. Send Telegram digest
7. Track deliveries

Usage:
    python scripts/run_daily_automation.py [--test] [--status] [--run-now]
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.automation.scheduler import DailyScheduler, AutomationConfig
from app.services.automation.telegram import TelegramService
from app.services.automation.digest import DigestFormatter
from app.services.automation.delivery_tracker import DeliveryTracker
from app.core.logging import logger


async def main():
    """Main automation runner."""
    parser = argparse.ArgumentParser(description="Daily PM Job Automation")
    parser.add_argument("--test", action="store_true", help="Test Telegram delivery")
    parser.add_argument("--status", action="store_true", help="Show scheduler status")
    parser.add_argument("--run-now", action="store_true", help="Run automation immediately")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without Telegram delivery")
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
        # Initialize scheduler
        config = AutomationConfig()
        scheduler = DailyScheduler(config)
        
        if args.status:
            await show_status(scheduler)
            return
        
        if args.test:
            await test_telegram(scheduler)
            return
        
        if args.run_now:
            await run_automation(scheduler, dry_run=args.dry_run)
            return
        
        # Default: start scheduler and keep running
        await start_scheduler(scheduler)
        
    except KeyboardInterrupt:
        logger.info("Automation stopped by user")
    except Exception as e:
        logger.error(f"Automation failed: {e}")
        sys.exit(1)


async def show_status(scheduler: DailyScheduler) -> None:
    """Show scheduler status."""
    print("📊 Daily Automation Status")
    print("=" * 50)
    
    status = scheduler.get_status()
    
    print(f"🔄 Running: {status['is_running']}")
    print(f"⏰ Next run: {status.get('next_run_time', 'Not scheduled')}")
    print(f"📅 Last run: {status.get('last_run_time', 'Never')}")
    
    config = status['config']
    print(f"\n⚙️ Configuration:")
    print(f"   Enabled: {config['enabled']}")
    print(f"   Delivery hour: {config['delivery_hour']:02d}:00 {config['delivery_timezone']}")
    print(f"   Max jobs/day: {config['max_jobs_per_day']}")
    print(f"   Min score threshold: {config['min_score_threshold']}")
    print(f"   Telegram enabled: {config['telegram_enabled']}")
    
    last_stats = status.get('last_run_stats', {})
    if last_stats:
        print(f"\n📈 Last Run Results:")
        print(f"   Success: {last_stats.get('success', False)}")
        print(f"   Jobs fetched: {last_stats.get('jobs_fetched', 0)}")
        print(f"   Jobs scored: {last_stats.get('jobs_scored', 0)}")
        print(f"   Jobs delivered: {last_stats.get('jobs_delivered', 0)}")
        print(f"   Telegram sent: {last_stats.get('telegram_sent', False)}")
        print(f"   Duration: {last_stats.get('duration_seconds', 0):.1f}s")
        
        if last_stats.get('errors'):
            print(f"   Errors: {len(last_stats['errors'])}")
            for error in last_stats['errors']:
                print(f"     - {error}")
    
    # Telegram status
    telegram_service = TelegramService()
    print(f"\n📱 Telegram Status:")
    print(f"   Configured: {telegram_service.is_enabled()}")
    
    if telegram_service.is_enabled():
        connection_ok = await telegram_service.test_connection()
        print(f"   Connection: {'✅ OK' if connection_ok else '❌ Failed'}")


async def test_telegram(scheduler: DailyScheduler) -> None:
    """Test Telegram delivery."""
    print("📱 Testing Telegram Delivery")
    print("=" * 50)
    
    success = await scheduler.test_telegram()
    
    if success:
        print("✅ Telegram test successful!")
        print("📊 Test digest sent to Telegram")
    else:
        print("❌ Telegram test failed!")
        print("🔍 Check configuration and logs")


async def run_automation(scheduler: DailyScheduler, dry_run: bool = False) -> None:
    """Run automation immediately."""
    print("🚀 Running Daily Automation")
    print("=" * 50)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No Telegram delivery")
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Run the automation
        stats = await scheduler.run_now()
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        # Display results
        print("\n📊 Automation Results:")
        print(f"   Success: {'✅' if stats['success'] else '❌'}")
        print(f"   Duration: {duration:.1f}s")
        
        steps = stats.get('steps_completed', [])
        print(f"   Steps completed: {', '.join(steps) if steps else 'None'}")
        
        print(f"\n📈 Job Statistics:")
        print(f"   Jobs fetched: {stats.get('jobs_fetched', 0)}")
        print(f"   Jobs scored: {stats.get('jobs_scored', 0)}")
        print(f"   Jobs delivered: {stats.get('jobs_delivered', 0)}")
        print(f"   Telegram sent: {'✅' if stats.get('telegram_sent') else '❌'}")
        
        errors = stats.get('errors', [])
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors:
                print(f"   - {error}")
        
        if stats['success']:
            print(f"\n✅ Automation completed successfully!")
        else:
            print(f"\n❌ Automation completed with errors!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Automation failed: {e}")
        sys.exit(1)


async def start_scheduler(scheduler: DailyScheduler) -> None:
    """Start scheduler and keep running."""
    print("🔄 Starting Daily Scheduler")
    print("=" * 50)
    
    # Show configuration
    config = scheduler.config
    print(f"⏰ Scheduled to run at {config.delivery_hour:02d}:00 {config.delivery_timezone}")
    print(f"📱 Telegram: {'✅ Enabled' if config.telegram_enabled else '❌ Disabled'}")
    print(f"📊 Max jobs/day: {config.max_jobs_per_day}")
    print(f"⭐ Min score threshold: {config.min_score_threshold}")
    
    # Start scheduler
    scheduler.start()
    
    print(f"\n✅ Scheduler started successfully!")
    print(f"📅 Next run: {scheduler.scheduler.get_job('daily_automation').next_run_time}")
    print(f"\n🔄 Running continuously... (Press Ctrl+C to stop)")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping scheduler...")
        scheduler.stop()
        print(f"✅ Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())
