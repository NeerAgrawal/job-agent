import sys
import os
import asyncio
from pathlib import Path

# Adjust Python Path to allow importing 'app'
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
sys.path.insert(0, str(root_dir))

from app.services.automation.telegram import TelegramService
from app.core.logging import setup_logging

async def main():
    setup_logging()
    print("🔄 Initializing Telegram Service...")
    telegram = TelegramService()
    
    print(f"🤖 Bot token loaded: {'✅ Yes' if telegram.bot_token else '❌ No'}")
    print(f"👥 Chat ID loaded: {'✅ Yes' if telegram.chat_id else '❌ No'}")
    print(f"⚙️ Enabled status: {'✅ Enabled' if telegram.is_enabled() else '❌ Disabled'}")
    
    if not telegram.is_enabled():
        print("❌ Telegram is not configured! Check your .env file.")
        return
        
    print("\n📡 Testing connection to Telegram API...")
    connected = await telegram.test_connection()
    if connected:
        print("✅ Connection verified! Testing message delivery...")
        sent = await telegram.send_test_message()
        if sent:
            print("🎉 Success! Check your Telegram app for the test message.")
        else:
            print("❌ Failed to send test message. Check server logs.")
    else:
        print("❌ Connection failed. Check your API token, proxy settings, or network connectivity.")

if __name__ == "__main__":
    asyncio.run(main())
