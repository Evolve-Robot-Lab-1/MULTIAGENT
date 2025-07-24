"""
API v1 route registration.
"""
from flask import Flask, Blueprint

from app.api.v1.documents import create_documents_blueprint
from app.api.v1.chat import create_chat_blueprint
from app.api.v1.agents import create_agents_blueprint


def register_v1_routes(app: Flask) -> None:
    """
    Register all v1 API routes.
    
    Args:
        app: Flask application instance
    """
    # Create v1 blueprint
    v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    
    # Register sub-blueprints
    v1.register_blueprint(create_documents_blueprint())
    v1.register_blueprint(create_chat_blueprint())
    v1.register_blueprint(create_agents_blueprint())
    
    # Register v1 blueprint with app
    app.register_blueprint(v1)
    
    # Also register legacy routes for backward compatibility
    register_legacy_routes(app)


def register_legacy_routes(app: Flask) -> None:
    """
    Register legacy routes for backward compatibility.
    
    Args:
        app: Flask application instance
    """
    from flask import redirect, url_for
    
    # Redirect legacy routes to v1
    @app.route('/rag/upload', methods=['POST'])
    def legacy_upload():
        return redirect(url_for('api_v1.documents.upload'), code=307)
    
    @app.route('/rag/status', methods=['GET'])
    def legacy_rag_status():
        return redirect(url_for('api_v1.documents.rag_status'), code=307)
    
    @app.route('/api/query_stream', methods=['POST'])
    def legacy_query_stream():
        return redirect(url_for('api_v1.chat.stream'), code=307)