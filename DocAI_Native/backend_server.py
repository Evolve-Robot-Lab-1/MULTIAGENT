"""
Backend Server for DocAI Native
Enterprise-grade Flask application with blueprints and validation
"""

import os
import sys
import signal
import threading
from pathlib import Path
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

from config import CFG
from app.logging_config import setup_logging, StructuredLogger
from app.api.v1 import api_v1

# Setup logging first
logger = setup_logging()
structured_logger = StructuredLogger(__name__)

def create_app(uno_bridge=None):
    """Create enterprise Flask app with blueprints and validation"""
    
    structured_logger.info("Initializing Flask application", 
                          app_name=CFG.APP_NAME, version=CFG.VERSION)
    
    # Initialize Flask app
    app = Flask(__name__, 
                static_folder=str(CFG.FRONTEND_DIR / 'static'),
                template_folder=str(CFG.FRONTEND_DIR))
    
    app.secret_key = CFG.FLASK_SECRET_KEY
    
    # Initialize window manager if UNO bridge is provided
    if uno_bridge:
        from app.services.window_manager import create_window_manager
        window_manager = create_window_manager(uno_bridge)
        # Set window manager in api_v1 module
        api_v1.window_manager = window_manager
        structured_logger.info("Window manager initialized with UNO bridge")
    
    # Configure CORS with security hardening
    cors_origins = ["http://127.0.0.1:*", "http://localhost:*"] if CFG.DEBUG else []
    CORS(app, 
         origins=cors_origins,
         methods=['GET', 'POST'],
         allow_headers=['Content-Type', 'Authorization'])
    
    # Register blueprints
    app.register_blueprint(api_v1)
    
    structured_logger.info("Flask app configured with blueprints", 
                          debug=CFG.DEBUG, cors_enabled=bool(cors_origins))
    
    # Serve frontend files
    @app.route('/')
    def index():
        """Serve main frontend page"""
        try:
            structured_logger.info("Serving index page")
            return send_from_directory(CFG.FRONTEND_DIR, 'index.html')
        except Exception as e:
            structured_logger.error("Failed to serve index.html", error=str(e))
            return f"Error loading application: {e}", 500
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files"""
        try:
            return send_from_directory(CFG.FRONTEND_DIR / 'static', filename)
        except Exception as e:
            structured_logger.error("Failed to serve static file", 
                                   filename=filename, error=str(e))
            return "File not found", 404
    
    @app.route('/test_libreoffice_embedding.html')
    def test_libreoffice():
        """Serve LibreOffice embedding test page"""
        try:
            return send_from_directory(Path(__file__).parent, 'test_libreoffice_embedding.html')
        except Exception as e:
            structured_logger.error("Failed to serve test page", error=str(e))
            return "Test page not found", 404
    
    @app.route('/test_api_debug.html')
    def test_api_debug():
        """Serve API debug test page"""
        try:
            return send_from_directory(Path(__file__).parent, 'test_api_debug.html')
        except Exception as e:
            structured_logger.error("Failed to serve debug page", error=str(e))
            return "Debug page not found", 404
    
    @app.route('/test_pywebview_api.html')
    def test_pywebview_api():
        """Serve PyWebView API deep debug page"""
        try:
            return send_from_directory(Path(__file__).parent, 'test_pywebview_api.html')
        except Exception as e:
            structured_logger.error("Failed to serve PyWebView debug page", error=str(e))
            return "Debug page not found", 404
    
    @app.route('/Durga.png')
    def serve_logo():
        """Serve Durga logo from assets"""
        try:
            return send_from_directory(CFG.FRONTEND_DIR / 'static' / 'assets', 'Durga.png')
        except Exception as e:
            structured_logger.error("Failed to serve Durga.png", error=str(e))
            return "Logo not found", 404
    
    # Legacy API compatibility (redirect to v1)
    @app.route('/api/view_document_native')
    def legacy_view_document():
        """Legacy endpoint for backward compatibility"""
        from flask import redirect, url_for
        structured_logger.warning("Legacy API endpoint accessed", 
                                 endpoint="/api/view_document_native")
        return redirect(url_for('api_v1.view_document_native', **request.args))
    
    # Native file picker endpoint
    @app.route('/api/native_pick_file', methods=['POST'])
    def native_pick_file():
        """Handle file picking through backend instead of PyWebView API"""
        try:
            # This endpoint will be called when PyWebView API fails
            # For now, return a message
            return jsonify({
                'success': False,
                'message': 'Please use the file picker button to select files'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Direct file view endpoint for native mode
    @app.route('/view_document_direct', methods=['POST'])
    def view_document_direct():
        """View document from direct file path (native mode)"""
        try:
            data = request.get_json() or {}
            file_path_str = data.get('filePath')
            
            if not file_path_str:
                return jsonify({
                    'success': False,
                    'error': 'No file path provided'
                }), 400
            
            file_path = Path(file_path_str)
            if not file_path.exists():
                return jsonify({
                    'success': False,
                    'error': 'File not found'
                }), 404
            
            # Process the file same as view_document
            file_ext = file_path.suffix.lower()
            filename = file_path.name
            
            # For text files, return content directly
            if file_ext in ['.txt', '.md']:
                content = file_path.read_text()
                html_content = f"<pre>{content}</pre>"
                
                return jsonify({
                    'success': True,
                    'pages': [html_content],
                    'filename': filename,
                    'type': 'text'
                })
            
            # For document files, try LibreOffice conversion
            elif file_ext in ['.doc', '.docx', '.odt', '.pdf']:
                try:
                    from app.services.libreoffice_uno_converter_improved import render_document_with_uno_images
                    
                    structured_logger.info("Attempting LibreOffice UNO conversion", filename=filename)
                    uno_result = render_document_with_uno_images(str(file_path))
                    
                    if uno_result and uno_result.get('success'):
                        content = uno_result.get('content', '')
                        pages = [content] if content else []
                        return jsonify({
                            'pages': pages,
                            'total_pages': len(pages),
                            'success': True,
                            'method': uno_result.get('method'),
                            'images_found': uno_result.get('images_found', 0)
                        })
                    else:
                        # Fallback to simple HTML message
                        return jsonify({
                            'success': True,
                            'pages': [f'<div style="padding: 50px; text-align: center;"><h2>{filename}</h2><p>Document conversion failed. Please check LibreOffice installation.</p><p>Error: {uno_result.get("error", "Unknown error") if uno_result else "Converter returned None"}</p></div>'],
                            'filename': filename,
                            'type': file_ext[1:]
                        })
                        
                except ImportError as e:
                    structured_logger.warning("LibreOffice converter not available", error=str(e))
                    return jsonify({
                        'success': True,
                        'pages': [f'<div style="padding: 50px; text-align: center;"><h2>{filename}</h2><p>Document preview requires LibreOffice.</p><p>Please ensure LibreOffice is installed.</p></div>'],
                        'filename': filename,
                        'type': file_ext[1:]
                    })
            else:
                # For other files, return placeholder
                return jsonify({
                    'success': True,
                    'pages': [f'<div style="padding: 50px; text-align: center;"><h2>{filename}</h2><p>Preview not available for {file_ext} files.</p></div>'],
                    'filename': filename,
                    'type': file_ext[1:]
                })
                
        except Exception as e:
            structured_logger.error("View document direct failed", error=str(e))
            return jsonify({'error': str(e), 'success': False}), 500

    # Document view endpoint with proper conversion
    @app.route('/view_document/<filename>')
    def view_document(filename):
        """View document with HTML conversion"""
        try:
            from pathlib import Path
            import os
            from urllib.parse import unquote, quote
            
            # Decode URL-encoded filename
            filename = unquote(filename)
            structured_logger.info(f"View document request for: {filename} (after URL decoding)")
            
            # Try multiple locations for files
            file_path = None
            
            # Try both the decoded filename and URL-encoded version
            filenames_to_try = [
                filename,  # Original decoded name
                filename.replace(' ', '%20'),  # URL-encoded spaces
                quote(filename)  # Fully URL-encoded
            ]
            
            search_dirs = [
                CFG.BASE_DIR / "uploads",
                CFG.DOCUMENTS_DIR,
                CFG.DOCUMENTS_DIR.parent,  # Check parent directory too
                # Also check the DocAI uploads directory
                CFG.BASE_DIR.parent / "DocAI" / "uploads" / "documents"
            ]
            
            # Try all combinations of directories and filename variations
            for search_dir in search_dirs:
                for try_filename in filenames_to_try:
                    path = search_dir / try_filename
                    if path.exists() and path.is_file():
                        file_path = path
                        structured_logger.info(f"Found file at: {file_path}")
                        break
                if file_path:
                    break
            
            if not file_path:
                structured_logger.warning(f"File not found in any location: {filename}")
                return jsonify({
                    'success': False,
                    'error': 'File not found'
                }), 404
            
            file_ext = file_path.suffix.lower()
            
            # For text files, return content directly
            if file_ext in ['.txt', '.md']:
                content = file_path.read_text()
                html_content = f"<pre>{content}</pre>"
                
                return jsonify({
                    'success': True,
                    'pages': [html_content],
                    'filename': filename,
                    'type': 'text'
                })
            
            # For document files, try LibreOffice conversion
            elif file_ext in ['.doc', '.docx', '.odt', '.pdf']:
                # Check if LibreOffice converter is available
                try:
                    # Import the converter
                    from app.services.libreoffice_uno_converter_improved import render_document_with_uno_images
                    
                    structured_logger.info("Attempting LibreOffice UNO conversion", filename=filename)
                    uno_result = render_document_with_uno_images(str(file_path))
                    
                    if uno_result and uno_result.get('success'):
                        content = uno_result.get('content', '')
                        pages = [content] if content else []
                        return jsonify({
                            'pages': pages,
                            'total_pages': len(pages),
                            'success': True,
                            'method': uno_result.get('method'),
                            'images_found': uno_result.get('images_found', 0)
                        })
                    else:
                        # Fallback to simple HTML message
                        return jsonify({
                            'success': True,
                            'pages': [f'<div style="padding: 50px; text-align: center;"><h2>{filename}</h2><p>Document conversion failed. Please check LibreOffice installation.</p><p>Error: {uno_result.get("error", "Unknown error") if uno_result else "Converter returned None"}</p></div>'],
                            'filename': filename,
                            'type': file_ext[1:]
                        })
                        
                except ImportError as e:
                    structured_logger.warning("LibreOffice converter not available", error=str(e))
                    # Fallback for when converter is not available
                    return jsonify({
                        'success': True,
                        'pages': [f'<div style="padding: 50px; text-align: center;"><h2>{filename}</h2><p>Document preview requires LibreOffice.</p><p>Please ensure LibreOffice is installed.</p></div>'],
                        'filename': filename,
                        'type': file_ext[1:]
                    })
            else:
                # For other files, return placeholder
                return jsonify({
                    'success': True,
                    'pages': [f'<div style="padding: 50px; text-align: center;"><h2>{filename}</h2><p>Preview not available for {file_ext} files.</p></div>'],
                    'filename': filename,
                    'type': file_ext[1:]
                })
                
        except Exception as e:
            structured_logger.error("View document failed", error=str(e), filename=filename)
            return jsonify({'error': str(e), 'success': False}), 500
    
    # Chat functionality (TODO: integrate with existing DocAI chat)
    @app.route('/api/open_with_libreoffice', methods=['POST'])
    def open_with_libreoffice():
        """Open document with LibreOffice"""
        try:
            data = request.json
            file_path = data.get('file_path')
            
            if not file_path:
                return jsonify({'success': False, 'error': 'No file path provided'})
            
            # Import the helper module
            from open_with_libreoffice import open_with_libreoffice as open_doc
            
            success = open_doc(file_path)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Document opened with LibreOffice'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to open document'
                })
                
        except Exception as e:
            structured_logger.error("Failed to open with LibreOffice", error=str(e))
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Chat endpoint - placeholder for existing logic integration"""
        try:
            data = request.json or {}
            message = data.get('message', '')
            
            structured_logger.info("Chat request received", message_length=len(message))
            
            # TODO: Integrate with existing DocAI chat service
            response = {
                'response': f'Echo: {message}',
                'status': 'success',
                'timestamp': '2024-01-01T00:00:00Z'
            }
            
            return jsonify(response)
            
        except Exception as e:
            structured_logger.error("Chat request failed", error=str(e))
            return jsonify({'error': str(e)}), 500
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        structured_logger.warning("404 Not Found", url=request.url)
        return jsonify({
            'error': 'Endpoint not found', 
            'code': 'NOT_FOUND',
            'path': request.path
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        structured_logger.error("500 Internal Error", error=str(error))
        return jsonify({
            'error': 'Internal server error', 
            'code': 'INTERNAL_ERROR'
        }), 500
    
    # Setup graceful shutdown handling
    _setup_shutdown_handlers(app)
    
    # Log successful app creation
    route_count = len(app.url_map._rules)
    structured_logger.info("Flask app creation complete", 
                          routes=route_count, 
                          blueprints=['api_v1'])
    
    return app


# Graceful shutdown handling
_shutdown_event = threading.Event()


def _setup_shutdown_handlers(app):
    """Setup graceful shutdown signal handlers"""
    
    def signal_handler(signum, frame):
        structured_logger.info("Shutdown signal received", signal=signum)
        _shutdown_event.set()
        
        # Perform cleanup
        structured_logger.info("Performing graceful shutdown cleanup")
        
        # TODO: Close UNO connections, cleanup temp files, etc.
        
        structured_logger.info("Graceful shutdown complete")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def is_shutting_down():
    """Check if application is shutting down"""
    return _shutdown_event.is_set()

# Legacy function for backward compatibility
def process_document_native(file_path):
    """Legacy wrapper for document processing"""
    from app.services.document_processor import create_document_processor
    processor = create_document_processor()
    return processor.process_native(Path(file_path))