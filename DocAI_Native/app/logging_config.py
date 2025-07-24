"""
Structured logging configuration with rotation
Enterprise-grade logging setup
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime

from config import CFG


def setup_logging():
    """Configure structured logging with rotation"""
    
    # Create logs directory
    log_dir = CFG.BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if CFG.DEBUG else logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Console formatter
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "docai_native.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG if CFG.DEBUG else logging.INFO)
    
    # File formatter (more detailed)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    
    # Flask logger
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.setLevel(logging.WARNING)  # Reduce Flask noise
    
    # UNO bridge logger  
    uno_logger = logging.getLogger('uno_bridge')
    uno_logger.setLevel(logging.DEBUG if CFG.DEBUG else logging.INFO)
    
    # Document processor logger
    doc_logger = logging.getLogger('app.services.document_processor')
    doc_logger.setLevel(logging.DEBUG if CFG.DEBUG else logging.INFO)
    
    # API logger
    api_logger = logging.getLogger('app.api')
    api_logger.setLevel(logging.DEBUG if CFG.DEBUG else logging.INFO)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {'DEBUG' if CFG.DEBUG else 'INFO'}")
    logger.info(f"Log files: {log_dir}")
    
    return logger


def log_request_info(func):
    """Decorator to log request information"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = datetime.now()
        
        # Log request start
        logger.info(f"START {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"COMPLETE {func.__name__} ({duration:.3f}s)")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"ERROR {func.__name__} ({duration:.3f}s): {e}")
            raise
            
    return wrapper


class StructuredLogger:
    """Structured logging helper for consistent log format"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def info(self, message, **kwargs):
        """Log info with structured data"""
        if kwargs:
            self.logger.info(f"{message} | {self._format_data(kwargs)}")
        else:
            self.logger.info(message)
    
    def error(self, message, **kwargs):
        """Log error with structured data"""
        if kwargs:
            self.logger.error(f"{message} | {self._format_data(kwargs)}")
        else:
            self.logger.error(message)
    
    def warning(self, message, **kwargs):
        """Log warning with structured data"""
        if kwargs:
            self.logger.warning(f"{message} | {self._format_data(kwargs)}")
        else:
            self.logger.warning(message)
    
    def debug(self, message, **kwargs):
        """Log debug with structured data"""
        if kwargs:
            self.logger.debug(f"{message} | {self._format_data(kwargs)}")
        else:
            self.logger.debug(message)
    
    def _format_data(self, data):
        """Format structured data for logging"""
        return " | ".join(f"{k}={v}" for k, v in data.items())