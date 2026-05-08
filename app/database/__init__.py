"""Database package for all database-related functionality."""

from .engine import engine
from .session import get_db_session
from .models import Base
from .repositories import (
    BaseRepository,
    JobRepository, 
    ApplicationRepository, 
    OutreachRepository, 
    ResumeVersionRepository, 
    ScoringLogRepository
)
from .migrations import create_tables
from .health import (
    check_database_connection,
    check_table_health,
    check_database_performance,
    get_comprehensive_health_check,
    get_database_statistics
)
from .seed import seed_database, clear_database

__all__ = [
    "engine",
    "get_db_session", 
    "Base",
    "BaseRepository",
    "JobRepository", 
    "ApplicationRepository", 
    "OutreachRepository", 
    "ResumeVersionRepository", 
    "ScoringLogRepository",
    "create_tables",
    "check_database_connection",
    "check_table_health", 
    "check_database_performance",
    "get_comprehensive_health_check",
    "get_database_statistics",
    "seed_database",
    "clear_database"
]
