import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

def setup_logging():
    """Configure logging for the application"""
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colored output
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # File handler for all logs
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="10 days",
        compression="zip"
    )
    
    # Separate error log file
    error_log_file = settings.logs_dir / "errors.log"
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Operations log (for high-level operations tracking)
    operations_log_file = settings.logs_dir / "operations.log"
    operations_logger = logger.bind(type="operation")
    
    return logger

def log_operation(operation_type: str, message: str, **kwargs):
    """Log high-level operations"""
    logger.bind(type="operation").info(f"[{operation_type}] {message}", **kwargs)

def log_automation_step(step: str, message: str, **kwargs):
    """Log automation steps"""
    logger.bind(type="automation").info(f"[{step}] {message}", **kwargs)

def log_api_request(method: str, endpoint: str, **kwargs):
    """Log API requests"""
    logger.bind(type="api").info(f"[{method}] {endpoint}", **kwargs)

# Initialize logging
setup_logging()
