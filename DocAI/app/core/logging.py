"""
Logging configuration for DocAI application.
Provides structured logging with proper formatting and rotation.
"""
import logging
import logging.handlers
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from contextvars import ContextVar

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured logs.
    Includes request ID tracking and extra context.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Get request ID from context
        request_id = request_id_var.get()
        
        # Build structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process,
        }
        
        # Add request ID if available
        if request_id:
            log_entry['request_id'] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'pathname', 'process', 'processName', 'relativeCreated', 
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Get request ID from context
        request_id = request_id_var.get()
        
        # Add request ID to format if available
        if request_id:
            record.request_id = f"[{request_id[:8]}]"
        else:
            record.request_id = ""
        
        # Use parent formatter
        return super().format(record)


def setup_logging(config: 'Config') -> None:
    """
    Set up logging configuration.
    
    Args:
        config: Application configuration
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(config.logging.file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level
    root_logger.setLevel(config.logging.level)
    
    # Console handler with human-readable format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.logging.level)
    console_format = HumanReadableFormatter(
        '%(asctime)s - %(name)s - %(levelname)s %(request_id)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler with structured format and rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.logging.file_path,
        maxBytes=config.logging.max_bytes,
        backupCount=config.logging.backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(config.logging.level)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        config.logging.error_file_path,
        maxBytes=config.logging.max_bytes,
        backupCount=config.logging.backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # Set third-party library log levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Log startup message
    root_logger.info(
        "Logging configured",
        extra={
            'log_level': config.logging.level,
            'log_file': str(config.logging.file_path),
            'error_file': str(config.logging.error_file_path)
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for current context.
    
    Args:
        request_id: Request ID to set (generates new one if not provided)
        
    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


def clear_request_id() -> None:
    """Clear request ID from context."""
    request_id_var.set(None)


class LogContext:
    """
    Context manager for adding extra context to logs.
    
    Usage:
        with LogContext(user_id='123', action='upload'):
            logger.info("Processing file")
    """
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.logger = logging.getLogger()
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def log_performance(func):
    """
    Decorator to log function performance.
    
    Usage:
        @log_performance
        def slow_function():
            time.sleep(1)
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(
                f"Function {func.__name__} completed",
                extra={
                    'function': func.__name__,
                    'duration_seconds': duration,
                    'status': 'success'
                }
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    'function': func.__name__,
                    'duration_seconds': duration,
                    'status': 'error',
                    'error': str(e)
                },
                exc_info=True
            )
            
            raise
    
    return wrapper