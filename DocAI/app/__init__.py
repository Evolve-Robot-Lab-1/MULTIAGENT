"""
DocAI Flask application factory.
"""
from flask import Flask, jsonify
from flask_cors import CORS

from app.core.config import Config, get_config
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import DocAIException
from app.api.middleware.error_handler import register_error_handlers
from app.api.middleware.request_tracking import register_request_tracking
from app.api.middleware.auth import register_auth_middleware
from app.api.v1 import register_v1_routes
from app.services.base import Container


def create_app(config: Config = None) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        config: Application configuration (uses default if not provided)
        
    Returns:
        Configured Flask application
    """
    # Get configuration
    config = config or get_config()
    
    # Set up logging
    setup_logging(config)
    logger = get_logger(__name__)
    
    # Create Flask app
    app = Flask(__name__, static_folder='../static2.0')
    
    # Configure app
    app.config['SECRET_KEY'] = config.server.secret_key
    app.config['MAX_CONTENT_LENGTH'] = config.storage.max_content_length
    app.config['UPLOAD_FOLDER'] = str(config.storage.upload_folder)
    
    # Enable CORS
    CORS(app, 
         origins=config.server.cors_origins,
         supports_credentials=True)
    
    # Register middleware in order
    register_request_tracking(app)  # First - track all requests
    register_auth_middleware(app)   # Second - authenticate requests
    register_error_handlers(app)    # Third - handle errors
    
    # Register API routes
    register_v1_routes(app)
    
    # Register OpenAPI documentation
    from app.api.openapi import init_openapi
    init_openapi(app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Basic health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'environment': config.environment,
            'version': '2.0.0'
        })
    
    # Root endpoint
    @app.route('/')
    def index():
        """Serve the main application page."""
        from flask import send_from_directory
        return send_from_directory(app.static_folder, 'indexf.html')
    
    # Static file serving
    @app.route('/static2.0/<path:filename>')
    def serve_static(filename):
        """Serve static files."""
        from flask import send_from_directory
        return send_from_directory(app.static_folder, filename)
    
    # Store config in app
    app.docai_config = config
    
    # Create service container
    app.container = Container(config)
    
    logger.info(
        f"DocAI application created",
        extra={
            'environment': config.environment,
            'debug': config.server.debug,
            'port': config.server.port
        }
    )
    
    return app


def create_app_with_services(config: Config = None) -> Flask:
    """
    Create Flask app and initialize all services.
    
    Args:
        config: Application configuration
        
    Returns:
        Flask app with initialized services
    """
    app = create_app(config)
    
    # Import and register services
    from app.services.document_service import DocumentService
    from app.services.chat_service import ChatService
    from app.services.rag_service import RAGService
    from app.services.agent_manager import AgentManager
    
    # Register services in container
    app.container.register(DocumentService)
    app.container.register(ChatService)
    app.container.register(RAGService)
    app.container.register(AgentManager)
    
    return app