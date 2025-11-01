import logging
import os
from logging.handlers import RotatingFileHandler

# -------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------
# This module sets up project-wide logging with rotation.
# Logs are written to both the console and a rotating file.
# -------------------------------------------------------

# Define log directory and file paths
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "system.log")

def configure_logging():
    """Configure global logging settings for the application."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File handler with rotation (max 5MB per file, up to 3 backups)
    fh = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.INFO)
    fh_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    # Console handler for real-time log visibility
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)
