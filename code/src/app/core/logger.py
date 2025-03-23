import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                "logs/app.log",
                maxBytes=10000000,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)