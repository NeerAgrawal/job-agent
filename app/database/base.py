"""Database base setup."""

from app.models import Base

# Re-export Base for database package usage
__all__ = ["Base"]
