import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

# Windows consoles default to a legacy codepage (e.g. cp1252), not UTF-8. Since log
# messages and CLI output throughout this project use emoji, force UTF-8 on stdout/
# stderr as early as possible (module import time) so it applies before loguru's
# default handler or any print() call in a script that imports this module.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def setup_logging() -> None:
    """Configure logging with loguru."""

    # Remove default handler
    logger.remove()
    
    # Ensure log directory exists
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # Add file handler
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )
    
    logger.info(f"Logging initialized with level: {settings.log_level}")


# Export configured logger
__all__ = ["logger", "setup_logging"]
