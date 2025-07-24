"""
Error handling middleware for Flask application.
"""
import traceback
import uuid
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from app.core.exceptions import DocAIException, RequestValidationError
from app.core.logging import get_logger, get_request_id
from app.models.api import APIResponse, ErrorDetail, ValidationErrorResponse


logger = get_logger(__name__)


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(RequestValidationError)
    def handle_validation_error(error: RequestValidationError):
        """Handle request validation errors."""
        request_id = get_request_id()
        
        logger.warning(
            f"Request validation failed",
            extra={
                'request_id': request_id,
                'errors': error.errors,
                'path': request.path
            }
        )
        
        # Convert to error details
        error_details = []
        for field, message in error.errors.items():
            error_details.append(
                ErrorDetail(field=field, message=message)
            )
        
        response = ValidationErrorResponse(
            errors=error_details
        )
        
        return jsonify(response.model_dump()), 400
    
    @app.errorhandler(DocAIException)
    def handle_docai_exception(error: DocAIException):
        """Handle custom DocAI exceptions."""
        request_id = get_request_id()
        
        logger.error(
            f"DocAI exception: {error.message}",
            extra={
                'request_id': request_id,
                'error_type': error.__class__.__name__,
                'details': error.details,
                'path': request.path
            }
        )
        
        response = APIResponse.error(
            error=error.__class__.__name__,
            details=error.details,
            message=error.message
        )
        response.request_id = request_id
        
        # Determine status code based on exception type
        status_code = 400
        if 'NotFound' in error.__class__.__name__:
            status_code = 404
        elif 'Unauthorized' in error.__class__.__name__:
            status_code = 401
        elif 'Forbidden' in error.__class__.__name__:
            status_code = 403
        elif 'Conflict' in error.__class__.__name__:
            status_code = 409
        
        return jsonify(response.model_dump()), status_code
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        """Handle Werkzeug HTTP exceptions."""
        request_id = get_request_id()
        
        logger.warning(
            f"HTTP exception: {error}",
            extra={
                'request_id': request_id,
                'status_code': error.code,
                'path': request.path
            }
        )
        
        response = APIResponse.error(
            error=error.name,
            message=error.description
        )
        response.request_id = request_id
        
        return jsonify(response.model_dump()), error.code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        request_id = get_request_id()
        
        logger.warning(
            f"Resource not found",
            extra={
                'request_id': request_id,
                'path': request.path,
                'method': request.method
            }
        )
        
        response = APIResponse.error(
            error="NotFound",
            message=f"Resource not found: {request.path}"
        )
        response.request_id = request_id
        
        return jsonify(response.model_dump()), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 errors."""
        request_id = get_request_id()
        error_id = str(uuid.uuid4())
        
        logger.error(
            f"Internal server error",
            extra={
                'request_id': request_id,
                'error_id': error_id,
                'path': request.path,
                'method': request.method
            },
            exc_info=True
        )
        
        response = APIResponse.error(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={'error_id': error_id}
        )
        response.request_id = request_id
        
        # Include stack trace in development
        if app.debug:
            response.error['stack_trace'] = traceback.format_exc()
        
        return jsonify(response.model_dump()), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        """Handle all other unexpected errors."""
        request_id = get_request_id()
        error_id = str(uuid.uuid4())
        
        logger.error(
            f"Unexpected error: {str(error)}",
            extra={
                'request_id': request_id,
                'error_id': error_id,
                'error_type': error.__class__.__name__,
                'path': request.path,
                'method': request.method
            },
            exc_info=True
        )
        
        response = APIResponse.error(
            error="UnexpectedError",
            message="An unexpected error occurred",
            details={'error_id': error_id}
        )
        response.request_id = request_id
        
        # Include error details in development
        if app.debug:
            response.error['details'] = {
                'error_id': error_id,
                'type': error.__class__.__name__,
                'message': str(error),
                'stack_trace': traceback.format_exc()
            }
        
        return jsonify(response.model_dump()), 500