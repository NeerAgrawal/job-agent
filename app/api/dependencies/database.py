from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db


def get_database_session(db: Session = Depends(get_db)) -> Session:
    """Dependency to get database session."""
    return db


__all__ = ["get_database_session"]
