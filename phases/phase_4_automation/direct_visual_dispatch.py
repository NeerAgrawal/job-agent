import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Adjust Python Path to allow importing 'app'
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from app.database.session import get_db_session
from app.services.shortlist.generator import ShortlistGenerator
from app.services.automation.digest import DigestFormatter
from app.services.automation.telegram import TelegramService
from app.services.automation.delivery_tracker import DeliveryTracker

async def main():
    print("🚀 Launching Direct visual Dispatch...")
    
    # Initialize components
    generator = ShortlistGenerator()
    formatter = DigestFormatter()
    telegram = TelegramService()
    tracker = DeliveryTracker()
    
    # 1. Load shortlists directly from SQLite
    print("📖 Reading high-scoring jobs from Database...")
    result = await generator.generate_daily_shortlist()
    jobs = result.get("jobs", [])
    print(f"📋 Total Shortlisted Available: {len(jobs)}")
    
    if not jobs:
        print("❌ No jobs available in DB shortlist.")
        return
        
    # 2. Filter out delivered (should be 0 since we cleared it)
    undelivered = await tracker.filter_undelivered_jobs(jobs)
    print(f"📨 Undelivered Jobs to Send: {len(undelivered)}")
    
    if not undelivered:
        print("❌ All jobs already delivered.")
        return
        
    # 3. Format to Premium Telegram Digest (Cap to 50 as configured!)
    summary_stats = {
        "total_analyzed": len(jobs) * 3,  # Proxy stat
        "shortlist_count": len(undelivered),
        "avg_score": sum(job.get("final_score", 0) for job in jobs) / len(jobs),
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    print("🎨 Formatting Premium Job Cards with Home Emojis...")
    digest_text = formatter.format_daily_digest(undelivered, summary_stats)
    
    # 4. Send to Telegram via long-message chunking
    print("📤 Dispatching directly to Telegram Bot API...")
    success = await telegram.send_long_message(digest_text)
    
    if success:
        print("✅ SUCCESS!!! Telegram sent!")
        # Mark as delivered
        for job in undelivered[:50]:
            await tracker.mark_job_delivered(job.get('job_url', ''), "telegram", "success")
        print("📁 Persisted to Delivery Tracker.")
    else:
        print("❌ Telegram Send Failed!")

if __name__ == "__main__":
    asyncio.run(main())
