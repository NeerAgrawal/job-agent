#!/usr/bin/env python3
"""Add AI matching fields to job table using direct SQL."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import engine
from app.core.logging import setup_logging, logger
from sqlalchemy import text


async def add_ai_fields_sql():
    """Add AI matching fields to job table using direct SQL."""
    setup_logging()
    
    try:
        print("🔧 Adding AI matching fields to job table...")
        
        # SQL statements to add AI fields
        sql_statements = [
            "ALTER TABLE jobs ADD COLUMN semantic_score REAL NULL",
            "ALTER TABLE jobs ADD COLUMN final_score REAL NULL", 
            "ALTER TABLE jobs ADD COLUMN salary_score REAL NULL",
            "ALTER TABLE jobs ADD COLUMN transition_score REAL NULL",
            "ALTER TABLE jobs ADD COLUMN relevance_reason TEXT NULL",
            "CREATE INDEX IF NOT EXISTS idx_jobs_semantic_score ON jobs(semantic_score)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_final_score ON jobs(final_score)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_salary_score ON jobs(salary_score)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_transition_score ON jobs(transition_score)"
        ]
        
        async with engine.begin() as conn:
            for sql in sql_statements:
                try:
                    await conn.execute(text(sql))
                    print(f"   ✅ Executed: {sql[:50]}...")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"   ⚠️  Column already exists: {sql[:50]}...")
                    else:
                        raise e
        
        print("✅ AI matching fields added successfully!")
        return True
        
    except Exception as e:
        logger.exception("Failed to add AI fields")
        print(f"❌ Failed to add AI fields: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(add_ai_fields_sql())
    sys.exit(0 if success else 1)
