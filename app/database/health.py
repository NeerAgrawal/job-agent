"""Database health check utilities."""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime, timedelta

from app.database.engine import engine
from app.models import Base
from app.core.logging import logger


async def check_database_connection() -> Dict[str, Any]:
    """Check database connection and basic health."""
    try:
        async with AsyncSession(engine) as session:
            # Test basic connection
            result = await session.execute(text("SELECT 1"))
            connection_ok = result.scalar() == 1
            
            # Check database info
            db_info = {}
            
            if connection_ok:
                # Get database type and version
                try:
                    if "sqlite" in str(engine.url):
                        db_info["type"] = "SQLite"
                        version_result = await session.execute(text("SELECT sqlite_version()"))
                        db_info["version"] = version_result.scalar()
                    else:
                        db_info["type"] = "PostgreSQL"
                        version_result = await session.execute(text("SELECT version()"))
                        db_info["version"] = version_result.scalar()
                except Exception as e:
                    logger.warning(f"Could not get database version: {e}")
                    db_info["type"] = "Unknown"
                    db_info["version"] = "Unknown"
            
            return {
                "status": "healthy" if connection_ok else "unhealthy",
                "connection": connection_ok,
                "database": db_info,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connection": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def check_table_health() -> Dict[str, Any]:
    """Check if all tables exist and are accessible."""
    try:
        async with AsyncSession(engine) as session:
            tables = {}
            
            # Check each table
            table_names = [
                "jobs", "applications", "outreach", 
                "resume_versions", "scoring_logs"
            ]
            
            for table_name in table_names:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    tables[table_name] = {
                        "exists": True,
                        "accessible": True,
                        "row_count": count
                    }
                except Exception as e:
                    tables[table_name] = {
                        "exists": False,
                        "accessible": False,
                        "error": str(e)
                    }
            
            # Overall health
            all_tables_healthy = all(
                table.get("accessible", False) for table in tables.values()
            )
            
            return {
                "status": "healthy" if all_tables_healthy else "degraded",
                "tables": tables,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Table health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def check_database_performance() -> Dict[str, Any]:
    """Check database performance metrics."""
    try:
        async with AsyncSession(engine) as session:
            performance = {}
            
            # Test query performance
            start_time = datetime.utcnow()
            result = await session.execute(text("SELECT 1"))
            query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            performance["query_latency_ms"] = query_time
            
            # Check database size (SQLite only)
            if "sqlite" in str(engine.url):
                try:
                    size_result = await session.execute(text(
                        "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
                    ))
                    size_bytes = size_result.scalar()
                    performance["database_size_mb"] = size_bytes / (1024 * 1024)
                except Exception as e:
                    logger.warning(f"Could not get database size: {e}")
                    performance["database_size_mb"] = "Unknown"
            
            # Check recent activity
            try:
                recent_result = await session.execute(text(
                    "SELECT COUNT(*) FROM jobs WHERE created_at > datetime('now', '-1 day')"
                ))
                recent_jobs = recent_result.scalar()
                performance["recent_jobs_24h"] = recent_jobs
            except Exception as e:
                logger.warning(f"Could not get recent activity: {e}")
                performance["recent_jobs_24h"] = "Unknown"
            
            # Performance status
            performance_status = "healthy"
            if query_time > 1000:  # > 1 second
                performance_status = "degraded"
            if query_time > 5000:  # > 5 seconds
                performance_status = "unhealthy"
            
            performance["status"] = performance_status
            performance["timestamp"] = datetime.utcnow().isoformat()
            
            return performance
    except Exception as e:
        logger.error(f"Performance check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def get_comprehensive_health_check() -> Dict[str, Any]:
    """Get comprehensive database health check."""
    try:
        # Run all health checks
        connection_health = await check_database_connection()
        table_health = await check_table_health()
        performance_health = await check_database_performance()
        
        # Determine overall status
        statuses = [
            connection_health.get("status", "unhealthy"),
            table_health.get("status", "unhealthy"),
            performance_health.get("status", "unhealthy")
        ]
        
        if all(status == "healthy" for status in statuses):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "connection": connection_health,
            "tables": table_health,
            "performance": performance_health,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def get_database_statistics() -> Dict[str, Any]:
    """Get comprehensive database statistics."""
    try:
        async with AsyncSession(engine) as session:
            stats = {}
            
            # Table statistics
            table_queries = {
                "jobs": "SELECT COUNT(*) as total, COUNT(CASE WHEN match_score IS NOT NULL THEN 1 END) as scored",
                "applications": "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'offered' THEN 1 END) as offers",
                "outreach": "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'replied' THEN 1 END) as replied",
                "resume_versions": "SELECT COUNT(*) as total, COUNT(CASE WHEN is_primary = 1 THEN 1 END) as primary",
                "scoring_logs": "SELECT COUNT(*) as total, COUNT(CASE WHEN is_successful = 1 THEN 1 END) as successful"
            }
            
            for table, query in table_queries.items():
                try:
                    result = await session.execute(text(query))
                    row = result.fetchone()
                    if row:
                        stats[table] = {
                            "total": row[0],
                            "special_count": row[1] if len(row) > 1 else 0
                        }
                except Exception as e:
                    logger.warning(f"Could not get stats for {table}: {e}")
                    stats[table] = {"error": str(e)}
            
            # Time-based statistics
            try:
                # Last 7 days activity
                week_ago = datetime.utcnow() - timedelta(days=7)
                
                jobs_week = await session.execute(
                    text("SELECT COUNT(*) FROM jobs WHERE created_at > :week_ago"),
                    {"week_ago": week_ago}
                )
                stats["recent_activity"] = {
                    "jobs_last_7_days": jobs_week.scalar()
                }
            except Exception as e:
                logger.warning(f"Could not get time-based stats: {e}")
                stats["recent_activity"] = {"error": str(e)}
            
            stats["timestamp"] = datetime.utcnow().isoformat()
            return stats
    except Exception as e:
        logger.error(f"Database statistics failed: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
