"""
Authentication middleware for Flask application.
Provides API key and JWT authentication.
"""
import functools
from typing import Optional, List, Callable
from flask import request, jsonify, g, current_app
import jwt
from datetime import datetime, timedelta

from app.core.exceptions import DocAIException
from app.core.logging import get_logger
from app.models.api import APIResponse


logger = get_logger(__name__)


class AuthenticationError(DocAIException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(DocAIException):
    """Raised when authorization fails."""
    pass


def register_auth_middleware(app):
    """
    Register authentication middleware.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def authenticate_request():
        """Authenticate incoming requests."""
        # Skip auth for public endpoints
        public_endpoints = [
            'health_check',
            'index',
            'serve_static',
            'api_v1.documents.list_documents'  # Example public endpoint
        ]
        
        if request.endpoint in public_endpoints:
            return
        
        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return
        
        # Try different authentication methods
        try:
            # Try API key authentication
            api_key = extract_api_key(request)
            if api_key:
                user = authenticate_api_key(api_key)
                g.user = user
                g.auth_method = 'api_key'
                return
            
            # Try JWT authentication
            token = extract_jwt_token(request)
            if token:
                user = authenticate_jwt(token)
                g.user = user
                g.auth_method = 'jwt'
                return
            
            # No authentication provided for protected endpoint
            if not request.endpoint or not request.endpoint.startswith('static'):
                raise AuthenticationError(
                    "Authentication required",
                    {'auth_methods': ['api_key', 'jwt']}
                )
                
        except AuthenticationError as e:
            response = APIResponse.error(
                "Authentication failed",
                details=e.details,
                message=e.message
            )
            return jsonify(response.model_dump()), 401


def extract_api_key(request) -> Optional[str]:
    """
    Extract API key from request.
    
    Args:
        request: Flask request object
        
    Returns:
        API key or None
    """
    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]
    
    # Check X-API-Key header
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return api_key
    
    # Check query parameter (less secure, not recommended)
    api_key = request.args.get('api_key')
    if api_key:
        logger.warning("API key provided in query parameter - this is insecure")
        return api_key
    
    return None


def extract_jwt_token(request) -> Optional[str]:
    """
    Extract JWT token from request.
    
    Args:
        request: Flask request object
        
    Returns:
        JWT token or None
    """
    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('JWT '):
        return auth_header[4:]
    
    # Check cookie
    token = request.cookies.get('auth_token')
    if token:
        return token
    
    return None


def authenticate_api_key(api_key: str) -> dict:
    """
    Authenticate using API key.
    
    Args:
        api_key: API key to validate
        
    Returns:
        User information
        
    Raises:
        AuthenticationError: If authentication fails
    """
    # TODO: Implement actual API key validation
    # This would typically check against a database
    
    # For now, accept a demo key
    if api_key == "demo-api-key-12345":
        return {
            'id': 'demo-user',
            'name': 'Demo User',
            'roles': ['user'],
            'api_key_id': 'demo-key'
        }
    
    raise AuthenticationError(
        "Invalid API key",
        {'api_key': api_key[:8] + '...'}  # Show partial key for debugging
    )


def authenticate_jwt(token: str) -> dict:
    """
    Authenticate using JWT token.
    
    Args:
        token: JWT token to validate
        
    Returns:
        User information
        
    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        # Get secret from config
        secret = current_app.docai_config.server.secret_key
        
        # Decode token
        payload = jwt.decode(
            token,
            secret,
            algorithms=['HS256']
        )
        
        # Check expiration
        exp = payload.get('exp')
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise AuthenticationError("Token expired")
        
        # Return user info
        return {
            'id': payload.get('sub'),
            'name': payload.get('name'),
            'roles': payload.get('roles', []),
            'jwt_id': payload.get('jti')
        }
        
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(
            "Invalid token",
            {'error': str(e)}
        )


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for a route.
    
    Args:
        f: Route function
        
    Returns:
        Decorated function
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user'):
            response = APIResponse.error(
                "Authentication required",
                message="This endpoint requires authentication"
            )
            return jsonify(response.model_dump()), 401
        return f(*args, **kwargs)
    return decorated_function


def require_roles(roles: List[str]) -> Callable:
    """
    Decorator to require specific roles for a route.
    
    Args:
        roles: List of required roles (user must have at least one)
        
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user'):
                response = APIResponse.error(
                    "Authentication required",
                    message="This endpoint requires authentication"
                )
                return jsonify(response.model_dump()), 401
            
            user_roles = g.user.get('roles', [])
            if not any(role in user_roles for role in roles):
                response = APIResponse.error(
                    "Insufficient permissions",
                    message=f"This endpoint requires one of these roles: {', '.join(roles)}"
                )
                return jsonify(response.model_dump()), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_jwt_token(user_id: str, name: str, roles: List[str], 
                      expiration_hours: int = 24) -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        user_id: User ID
        name: User name
        roles: User roles
        expiration_hours: Token expiration time in hours
        
    Returns:
        JWT token
    """
    # Get secret from config
    from app.core.config import get_config
    secret = get_config().server.secret_key
    
    # Create payload
    payload = {
        'sub': user_id,
        'name': name,
        'roles': roles,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=expiration_hours),
        'jti': str(uuid.uuid4())  # JWT ID for revocation
    }
    
    # Generate token
    token = jwt.encode(payload, secret, algorithm='HS256')
    
    return token


import uuid