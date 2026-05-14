#!/usr/bin/env python3
"""Add AI matching fields to job table."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import engine, get_db_session
from app.models import Base
from app.core.logging import setup_logging, logger


async def add_ai_fields():
    """Add AI matching fields to job table."""
    setup_logging()
    
    try:
        print("🔧 Adding AI matching fields to job table...")
        
        # Create all tables (this will add the new fields)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ AI matching fields added successfully!")
        return True
        
    except Exception as e:
        logger.exception("Failed to add AI fields")
        print(f"❌ Failed to add AI fields: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(add_ai_fields())
    sys.exit(0 if success else 1)
