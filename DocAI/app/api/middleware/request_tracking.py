"""
Request tracking middleware for Flask application.
Adds request ID tracking and logging to all requests.
"""
import time
import uuid
from flask import Flask, request, g
from werkzeug.exceptions import HTTPException

from app.core.logging import set_request_id, get_request_id, clear_request_id, get_logger


logger = get_logger(__name__)


def register_request_tracking(app: Flask) -> None:
    """
    Register request tracking middleware.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def before_request():
        """Set up request tracking before each request."""
        # Generate or extract request ID
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        
        # Set request ID in context
        set_request_id(request_id)
        
        # Store in Flask g object for easy access
        g.request_id = request_id
        g.start_time = time.time()
        
        # Log request start
        logger.info(
            f"Request started",
            extra={
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'content_length': request.content_length
            }
        )
    
    @app.after_request
    def after_request(response):
        """Add tracking headers to response."""
        # Add request ID to response headers
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        # Calculate request duration
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            
            # Log request completion
            logger.info(
                f"Request completed",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_seconds': duration,
                    'response_size': response.content_length or 0
                }
            )
        
        return response
    
    @app.teardown_request
    def teardown_request(exception=None):
        """Clean up after request."""
        # Clear request ID from context
        clear_request_id()
        
        # Log any exceptions that occurred
        if exception:
            logger.error(
                f"Request failed with exception",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'exception': str(exception)
                },
                exc_info=True
            )