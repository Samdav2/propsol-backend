import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "app.log"

def setup_logging():
    """
    Configures logging for the application.
    - Writes logs to logs/app.log with rotation.
    - Writes logs to console (stdout).
    """
    # Create a custom logger
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    # Create handlers
    c_handler = logging.StreamHandler(sys.stdout)
    f_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5) # 10MB, 5 backups

    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.INFO)

    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)

    # Add handlers to the logger
    # Check if handlers are already added to avoid duplicates
    if not logger.hasHandlers():
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    # Also configure uvicorn loggers to use our file handler
    logging.getLogger("uvicorn.access").addHandler(f_handler)
    logging.getLogger("uvicorn.error").addHandler(f_handler)

    return logger

logger = setup_logging()
