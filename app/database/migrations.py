"""Database migration utilities."""

from sqlalchemy.ext.asyncio import AsyncSession
from app.database.engine import engine
from app.database.base import Base
from app.core.logging import logger


async def create_tables():
    """Create all database tables."""
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            
            # Verify tables were created
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
        
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def drop_tables():
    """Drop all database tables (use with caution)."""
    async with AsyncSession(engine) as session:
        try:
            await session.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
