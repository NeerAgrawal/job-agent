#!/usr/bin/env python3
"""Database initialization script."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.database.migrations import create_tables
from app.database.models import Base
from app.database.engine import engine
from app.core.logging import setup_logging, logger


async def init_database():
    """Initialize database with all tables."""
    setup_logging()
    
    try:
        logger.info("Starting database initialization...")
        
        # Create all tables
        await create_tables()
        
        # Verify tables were created
        async with engine.begin() as conn:
            # Check if tables exist
            tables = Base.metadata.tables.keys()
            logger.info(f"Created {len(tables)} tables: {', '.join(tables)}")
            
            # Verify each table exists
            for table_name in tables:
                try:
                    result = await conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = result.scalar()
                    logger.info(f"Table '{table_name}' exists with {count} rows")
                except Exception as e:
                    logger.error(f"Could not verify table '{table_name}': {e}")
        
        logger.info("Database initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def main():
    """Main function for script execution."""
    try:
        success = asyncio.run(init_database())
        if success:
            print("✅ Database initialized successfully!")
            sys.exit(0)
        else:
            print("❌ Database initialization failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Database initialization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
