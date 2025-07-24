"""
OpenAPI/Swagger documentation setup for DocAI API.
"""
from flask import Blueprint, jsonify
from flask_restx import Api, Resource, fields, Namespace
from functools import wraps
from typing import Dict, Any

from app.core.config import settings


# Create blueprint for API documentation
api_bp = Blueprint('api_docs', __name__, url_prefix='/api/docs')

# Initialize Flask-RESTX API
api = Api(
    api_bp,
    version='1.0',
    title='DocAI API',
    description='Document Intelligence Platform API Documentation',
    doc='/swagger',
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key'
        }
    },
    security='apikey'
)

# Create namespaces
auth_ns = api.namespace('auth', description='Authentication operations')
documents_ns = api.namespace('documents', description='Document operations')
chat_ns = api.namespace('chat', description='Chat operations')
agents_ns = api.namespace('agents', description='Agent operations')
health_ns = api.namespace('health', description='Health check operations')

# Common models
error_model = api.model('Error', {
    'error': fields.String(required=True, description='Error message'),
    'code': fields.Integer(required=True, description='Error code'),
    'details': fields.Raw(description='Additional error details')
})

success_model = api.model('Success', {
    'status': fields.String(required=True, description='Status message'),
    'data': fields.Raw(description='Response data'),
    'metadata': fields.Raw(description='Response metadata')
})

# Authentication models
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

token_model = api.model('Token', {
    'access_token': fields.String(required=True, description='JWT access token'),
    'token_type': fields.String(required=True, description='Token type'),
    'expires_in': fields.Integer(required=True, description='Token expiration time in seconds')
})

# Document models
document_upload_model = api.model('DocumentUpload', {
    'title': fields.String(required=True, description='Document title'),
    'description': fields.String(description='Document description'),
    'tags': fields.List(fields.String, description='Document tags'),
    'process_ocr': fields.Boolean(default=False, description='Enable OCR processing'),
    'extract_metadata': fields.Boolean(default=True, description='Extract document metadata')
})

document_model = api.model('Document', {
    'id': fields.String(required=True, description='Document ID'),
    'title': fields.String(required=True, description='Document title'),
    'filename': fields.String(required=True, description='Original filename'),
    'file_type': fields.String(required=True, description='File type'),
    'size': fields.Integer(required=True, description='File size in bytes'),
    'created_at': fields.DateTime(required=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(required=True, description='Last update timestamp'),
    'metadata': fields.Raw(description='Document metadata'),
    'tags': fields.List(fields.String, description='Document tags'),
    'status': fields.String(required=True, description='Processing status')
})

# Chat models
chat_message_model = api.model('ChatMessage', {
    'message': fields.String(required=True, description='User message'),
    'session_id': fields.String(description='Chat session ID'),
    'model': fields.String(description='AI model to use'),
    'provider': fields.String(description='AI provider'),
    'use_rag': fields.Boolean(default=False, description='Use RAG for response'),
    'stream': fields.Boolean(default=False, description='Stream response'),
    'temperature': fields.Float(description='Model temperature'),
    'max_tokens': fields.Integer(description='Maximum tokens in response')
})

chat_response_model = api.model('ChatResponse', {
    'id': fields.String(required=True, description='Message ID'),
    'message': fields.String(required=True, description='AI response'),
    'session_id': fields.String(required=True, description='Chat session ID'),
    'model': fields.String(required=True, description='Model used'),
    'created_at': fields.DateTime(required=True, description='Creation timestamp'),
    'usage': fields.Raw(description='Token usage information'),
    'sources': fields.List(fields.Raw, description='RAG sources if used')
})

# Agent models
agent_status_model = api.model('AgentStatus', {
    'browser_agent': fields.Raw(description='Browser agent status'),
    'document_agent': fields.Raw(description='Document agent status'),
    'system': fields.Raw(description='System status')
})

agent_task_model = api.model('AgentTask', {
    'task_type': fields.String(required=True, description='Type of task'),
    'parameters': fields.Raw(required=True, description='Task parameters'),
    'priority': fields.String(description='Task priority'),
    'callback_url': fields.String(description='Webhook URL for completion')
})


# Authentication endpoints
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_model)
    @auth_ns.response(401, 'Invalid credentials', error_model)
    def post(self):
        """Authenticate user and get access token"""
        pass


@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @auth_ns.response(401, 'Invalid token', error_model)
    @auth_ns.marshal_with(token_model)
    def post(self):
        """Refresh access token"""
        pass


# Document endpoints
@documents_ns.route('')
class DocumentList(Resource):
    @documents_ns.marshal_list_with(document_model)
    @documents_ns.param('page', 'Page number', type=int, default=1)
    @documents_ns.param('per_page', 'Items per page', type=int, default=20)
    @documents_ns.param('search', 'Search query', type=str)
    @documents_ns.param('tags', 'Filter by tags', type=str)
    def get(self):
        """Get list of documents"""
        pass

    @documents_ns.expect(document_upload_model)
    @documents_ns.marshal_with(document_model)
    @documents_ns.response(413, 'File too large', error_model)
    def post(self):
        """Upload a new document"""
        pass


@documents_ns.route('/<string:document_id>')
class Document(Resource):
    @documents_ns.marshal_with(document_model)
    @documents_ns.response(404, 'Document not found', error_model)
    def get(self, document_id):
        """Get document details"""
        pass

    @documents_ns.expect(document_upload_model)
    @documents_ns.marshal_with(document_model)
    @documents_ns.response(404, 'Document not found', error_model)
    def put(self, document_id):
        """Update document metadata"""
        pass

    @documents_ns.response(204, 'Document deleted')
    @documents_ns.response(404, 'Document not found', error_model)
    def delete(self, document_id):
        """Delete document"""
        pass


@documents_ns.route('/<string:document_id>/download')
class DocumentDownload(Resource):
    @documents_ns.response(404, 'Document not found', error_model)
    @documents_ns.produces(['application/octet-stream'])
    def get(self, document_id):
        """Download document file"""
        pass


@documents_ns.route('/<string:document_id>/convert')
class DocumentConvert(Resource):
    @documents_ns.param('format', 'Target format', type=str, required=True)
    @documents_ns.response(404, 'Document not found', error_model)
    @documents_ns.response(400, 'Invalid format', error_model)
    def post(self, document_id):
        """Convert document to different format"""
        pass


@documents_ns.route('/rag/status')
class RAGStatus(Resource):
    def get(self):
        """Get RAG system status"""
        pass


# Chat endpoints
@chat_ns.route('/completions')
class ChatCompletion(Resource):
    @chat_ns.expect(chat_message_model)
    @chat_ns.marshal_with(chat_response_model)
    @chat_ns.response(400, 'Invalid request', error_model)
    def post(self):
        """Send chat message and get response"""
        pass


@chat_ns.route('/stream')
class ChatStream(Resource):
    @chat_ns.expect(chat_message_model)
    @chat_ns.response(400, 'Invalid request', error_model)
    @chat_ns.produces(['text/event-stream'])
    def post(self):
        """Stream chat response"""
        pass


@chat_ns.route('/sessions/<string:session_id>/history')
class ChatHistory(Resource):
    @chat_ns.marshal_list_with(chat_response_model)
    @chat_ns.param('limit', 'Number of messages', type=int, default=50)
    def get(self, session_id):
        """Get chat history for session"""
        pass

    @chat_ns.response(204, 'History cleared')
    def delete(self, session_id):
        """Clear chat history for session"""
        pass


# Agent endpoints
@agents_ns.route('/status')
class AgentStatus(Resource):
    @agents_ns.marshal_with(agent_status_model)
    def get(self):
        """Get status of all agents"""
        pass


@agents_ns.route('/browser/start')
class BrowserAgentStart(Resource):
    @agents_ns.expect(agent_task_model)
    @agents_ns.response(202, 'Task accepted', success_model)
    @agents_ns.response(503, 'Agent unavailable', error_model)
    def post(self):
        """Start browser agent task"""
        pass


@agents_ns.route('/browser/stop')
class BrowserAgentStop(Resource):
    @agents_ns.response(204, 'Agent stopped')
    def post(self):
        """Stop browser agent"""
        pass


# Health endpoints
@health_ns.route('')
class Health(Resource):
    def get(self):
        """Get application health status"""
        return {
            'status': 'healthy',
            'timestamp': '2024-01-08T10:30:00Z',
            'version': settings.VERSION,
            'services': {
                'database': 'healthy',
                'redis': 'healthy',
                'agents': 'healthy'
            }
        }


@health_ns.route('/ready')
class ReadinessCheck(Resource):
    def get(self):
        """Check if application is ready to serve requests"""
        pass


@health_ns.route('/live')
class LivenessCheck(Resource):
    def get(self):
        """Check if application is alive"""
        pass


def init_openapi(app):
    """Initialize OpenAPI documentation."""
    app.register_blueprint(api_bp)
    
    # Add custom documentation
    @app.route('/api/docs')
    def api_documentation():
        return '''
        <html>
            <head>
                <title>DocAI API Documentation</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    h1 { color: #333; }
                    .link { margin: 10px 0; }
                    a { color: #007bff; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1>DocAI API Documentation</h1>
                <p>Welcome to the DocAI API documentation. Choose your preferred format:</p>
                <div class="link">
                    <a href="/api/docs/swagger">Interactive Swagger UI</a> - 
                    Explore and test API endpoints interactively
                </div>
                <div class="link">
                    <a href="/api/docs/swagger.json">OpenAPI Specification (JSON)</a> - 
                    Download the OpenAPI spec for code generation
                </div>
                <div class="link">
                    <a href="/api/v1">API Base URL</a> - 
                    The base URL for all API endpoints
                </div>
                <h2>Authentication</h2>
                <p>All API requests require an X-API-Key header:</p>
                <code>X-API-Key: your-api-key-here</code>
                <h2>Quick Start</h2>
                <p>Example request:</p>
                <pre>
curl -X POST https://api.docai.com/api/v1/chat/completions \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Hello, DocAI!",
    "session_id": "unique-session-id"
  }'
                </pre>
            </body>
        </html>
        '''
    
    return api