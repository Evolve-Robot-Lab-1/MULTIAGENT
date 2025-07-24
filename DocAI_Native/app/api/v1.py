"""
API v1 Blueprint with versioned endpoints
Enterprise-grade REST API with validation
"""

import logging
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from pydantic import ValidationError
from werkzeug.utils import secure_filename
from urllib.parse import unquote
import os

from config import CFG
from app.schemas import (
    FileRequest, ProcessRequest, ViewRequest, 
    HealthResponse, ErrorResponse, ConfigResponse
)
from app.services.document_processor import create_document_processor
from app.services.window_manager import create_window_manager

# Create blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)

# Initialize document processor
doc_processor = create_document_processor()

# Initialize window manager (will be set by app initialization)
window_manager = None


def create_error_response(error: str, code: str, details=None):
    """Create standardized error response"""
    return ErrorResponse(
        error=error,
        code=code,
        details=details,
        timestamp=datetime.utcnow().isoformat()
    ).dict()


def validate_request(schema, data):
    """Validate request data against schema"""
    try:
        return schema(**data)
    except ValidationError as e:
        raise ValueError(f"Validation error: {e}")


@api_v1.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Check LibreOffice availability
        lo_path = Path(CFG.LIBREOFFICE_PATH)
        lo_status = "available" if lo_path.exists() else "not_found"
        
        response = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            version=CFG.VERSION,
            services={
                "libreoffice": lo_status,
                "document_processor": "available"
            }
        )
        
        return jsonify(response.dict())
        
    except Exception as e:
        logger.exception("Health check failed")
        error_response = create_error_response(
            error="Health check failed",
            code="HEALTH_CHECK_ERROR",
            details={"exception": str(e)}
        )
        return jsonify(error_response), 500


@api_v1.route('/config', methods=['GET'])
def config():
    """Get application configuration"""
    try:
        lo_path = Path(CFG.LIBREOFFICE_PATH)
        
        response = ConfigResponse(
            app_name=CFG.APP_NAME,
            version=CFG.VERSION,
            supported_formats=list(CFG.ALLOWED_EXTENSIONS),
            max_file_size=CFG.MAX_FILE_SIZE,
            libreoffice_available=lo_path.exists()
        )
        
        return jsonify(response.dict())
        
    except Exception as e:
        logger.exception("Config retrieval failed")
        error_response = create_error_response(
            error="Failed to retrieve configuration",
            code="CONFIG_ERROR"
        )
        return jsonify(error_response), 500


@api_v1.route('/open_file', methods=['POST'])
def open_file():
    """Open and validate a file"""
    try:
        # Validate request
        file_req = validate_request(FileRequest, request.json or {})
        file_path = Path(file_req.path)
        
        logger.info(f"Opening file: {file_path}")
        
        # Validate file
        validation = doc_processor.validate_file(file_path)
        
        if validation['valid']:
            logger.info(f"File validated successfully: {file_path.name}")
            return jsonify({
                'success': True,
                'file': {
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': validation['size'],
                    'extension': validation['extension']
                },
                'message': 'File opened successfully'
            })
        else:
            logger.warning(f"File validation failed: {validation['error']}")
            error_response = create_error_response(
                error=validation['error'],
                code=validation['code'],
                details=validation
            )
            return jsonify(error_response), 400
            
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        error_response = create_error_response(
            error=str(e),
            code="VALIDATION_ERROR"
        )
        return jsonify(error_response), 400
        
    except Exception as e:
        logger.exception("File opening failed")
        error_response = create_error_response(
            error="Failed to open file",
            code="FILE_OPEN_ERROR"
        )
        return jsonify(error_response), 500


@api_v1.route('/process', methods=['POST'])
def process_document():
    """Process document for viewing"""
    try:
        # Validate request
        process_req = validate_request(ProcessRequest, request.json or {})
        file_path = Path(process_req.path)
        
        logger.info(f"Processing document: {file_path} in {process_req.mode} mode")
        
        # Process document
        if process_req.mode == 'native':
            result = doc_processor.process_native(file_path)
        else:
            result = doc_processor.process_html(file_path)
        
        if result['success']:
            logger.info(f"Document processed successfully: {file_path.name}")
            return jsonify(result)
        else:
            logger.error(f"Document processing failed: {result['error']}")
            error_response = create_error_response(
                error=result['error'],
                code=result['code'],
                details=result
            )
            return jsonify(error_response), 400
            
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        error_response = create_error_response(
            error=str(e),
            code="VALIDATION_ERROR"
        )
        return jsonify(error_response), 400
        
    except Exception as e:
        logger.exception("Document processing failed")
        error_response = create_error_response(
            error="Failed to process document",
            code="PROCESSING_ERROR"
        )
        return jsonify(error_response), 500


@api_v1.route('/view_document_native/<filename>', methods=['POST'])
def view_document_native(filename):
    """
    View document in native LibreOffice window
    
    Args:
        filename: Name of the document file to view
        
    Request Body:
        JSON with parent window information (position, size)
    """
    try:
        # Check if window manager is initialized
        if not window_manager:
            error_response = create_error_response(
                error="Window manager not initialized",
                code="SERVICE_UNAVAILABLE"
            )
            return jsonify(error_response), 503
        
        # Get parent window info from request body
        parent_window_info = request.get_json() or {}
        
        # Construct file path (assuming files are in uploads directory)
        file_path = CFG.BASE_DIR / "uploads" / filename
        
        # Validate file exists
        if not file_path.exists():
            # Try alternative paths
            alt_paths = [
                CFG.BASE_DIR / filename,
                Path(filename)  # Absolute path
            ]
            
            file_found = False
            for alt_path in alt_paths:
                if alt_path.exists():
                    file_path = alt_path
                    file_found = True
                    break
            
            if not file_found:
                error_response = create_error_response(
                    error=f"Document not found: {filename}",
                    code="FILE_NOT_FOUND"
                )
                return jsonify(error_response), 404
        
        # Validate file extension
        if file_path.suffix.lower() not in CFG.ALLOWED_EXTENSIONS:
            error_response = create_error_response(
                error=f"Unsupported file type: {file_path.suffix}",
                code="UNSUPPORTED_FILE_TYPE"
            )
            return jsonify(error_response), 400
        
        logger.info(f"Native view requested for: {file_path}")
        logger.debug(f"Parent window info: {parent_window_info}")
        
        # Open document in native window
        result = window_manager.open_document_window(
            str(file_path),
            parent_window_info
        )
        
        if result['success']:
            logger.info(f"Document opened in native viewer: {filename}")
            return jsonify(result)
        else:
            error_response = create_error_response(
                error=result.get('error', 'Failed to open document'),
                code="NATIVE_VIEW_ERROR",
                details=result
            )
            return jsonify(error_response), 500
        
    except Exception as e:
        logger.exception("Native view failed")
        error_response = create_error_response(
            error="Failed to open native view",
            code="NATIVE_VIEW_ERROR",
            details={"exception": str(e)}
        )
        return jsonify(error_response), 500


@api_v1.route('/document/<doc_id>/zoom', methods=['POST'])
def zoom_document(doc_id):
    """Set zoom level for a document"""
    try:
        if not window_manager:
            error_response = create_error_response(
                error="Window manager not initialized",
                code="SERVICE_UNAVAILABLE"
            )
            return jsonify(error_response), 503
        
        data = request.get_json() or {}
        zoom_level = data.get('zoom', 100)
        
        # Validate zoom level
        if not isinstance(zoom_level, (int, float)) or zoom_level < 10 or zoom_level > 500:
            error_response = create_error_response(
                error="Invalid zoom level (must be between 10 and 500)",
                code="INVALID_ZOOM_LEVEL"
            )
            return jsonify(error_response), 400
        
        # Get UNO bridge from window manager
        uno_bridge = window_manager.uno_bridge
        result = uno_bridge.zoom_document(doc_id, int(zoom_level))
        
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"Zoom operation failed for document {doc_id}")
        error_response = create_error_response(
            error="Failed to set zoom level",
            code="ZOOM_ERROR"
        )
        return jsonify(error_response), 500


@api_v1.route('/document/<doc_id>/page', methods=['POST'])
def navigate_page(doc_id):
    """Navigate to a specific page in the document"""
    try:
        if not window_manager:
            error_response = create_error_response(
                error="Window manager not initialized",
                code="SERVICE_UNAVAILABLE"
            )
            return jsonify(error_response), 503
        
        data = request.get_json() or {}
        page_num = data.get('page', 1)
        
        # Validate page number
        if not isinstance(page_num, int) or page_num < 1:
            error_response = create_error_response(
                error="Invalid page number",
                code="INVALID_PAGE_NUMBER"
            )
            return jsonify(error_response), 400
        
        # Get UNO bridge from window manager
        uno_bridge = window_manager.uno_bridge
        result = uno_bridge.scroll_to_page(doc_id, page_num)
        
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"Page navigation failed for document {doc_id}")
        error_response = create_error_response(
            error="Failed to navigate to page",
            code="PAGE_NAVIGATION_ERROR"
        )
        return jsonify(error_response), 500


@api_v1.route('/document/<doc_id>/close', methods=['POST'])
def close_document(doc_id):
    """Close a document window"""
    try:
        if not window_manager:
            error_response = create_error_response(
                error="Window manager not initialized",
                code="SERVICE_UNAVAILABLE"
            )
            return jsonify(error_response), 503
        
        result = window_manager.close_window(doc_id)
        
        if result['success']:
            return jsonify(result)
        else:
            error_response = create_error_response(
                error=result.get('error', 'Failed to close document'),
                code="CLOSE_ERROR"
            )
            return jsonify(error_response), 500
        
    except Exception as e:
        logger.exception(f"Failed to close document {doc_id}")
        error_response = create_error_response(
            error="Failed to close document",
            code="CLOSE_ERROR"
        )
        return jsonify(error_response), 500


@api_v1.route('/document/<doc_id>/info', methods=['GET'])
def get_document_info(doc_id):
    """Get information about an open document"""
    try:
        if not window_manager:
            error_response = create_error_response(
                error="Window manager not initialized",
                code="SERVICE_UNAVAILABLE"
            )
            return jsonify(error_response), 503
        
        # Get UNO bridge from window manager
        uno_bridge = window_manager.uno_bridge
        result = uno_bridge.get_document_info(doc_id)
        
        if result['success']:
            return jsonify(result)
        else:
            error_response = create_error_response(
                error=result.get('error', 'Document not found'),
                code="DOCUMENT_NOT_FOUND"
            )
            return jsonify(error_response), 404
        
    except Exception as e:
        logger.exception(f"Failed to get document info for {doc_id}")
        error_response = create_error_response(
            error="Failed to get document information",
            code="INFO_ERROR"
        )
        return jsonify(error_response), 500


@api_v1.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download a file"""
    try:
        # Security: Only allow downloads from specific directories
        safe_path = CFG.BASE_DIR / "uploads" / filename
        
        if not safe_path.exists():
            error_response = create_error_response(
                error="File not found",
                code="FILE_NOT_FOUND"
            )
            return jsonify(error_response), 404
        
        logger.info(f"File download: {safe_path.name}")
        return send_file(safe_path, as_attachment=True)
        
    except Exception as e:
        logger.exception("File download failed")
        error_response = create_error_response(
            error="Failed to download file",
            code="DOWNLOAD_ERROR"
        )
        return jsonify(error_response), 500


@api_v1.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file to the server"""
    try:
        # Ensure upload directory exists
        upload_dir = CFG.BASE_DIR / "uploads"
        upload_dir.mkdir(exist_ok=True)
        
        # Check if file part exists
        if 'file' not in request.files:
            error_response = create_error_response(
                error="No file part in request",
                code="NO_FILE_PART"
            )
            return jsonify(error_response), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            error_response = create_error_response(
                error="No file selected",
                code="NO_FILE_SELECTED"
            )
            return jsonify(error_response), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            error_response = create_error_response(
                error="Invalid filename",
                code="INVALID_FILENAME"
            )
            return jsonify(error_response), 400
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in CFG.ALLOWED_EXTENSIONS:
            error_response = create_error_response(
                error=f"File type not allowed: {file_ext}",
                code="INVALID_FILE_TYPE",
                details={"allowed_types": list(CFG.ALLOWED_EXTENSIONS)}
            )
            return jsonify(error_response), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > CFG.MAX_FILE_SIZE:
            error_response = create_error_response(
                error=f"File too large. Maximum size is {CFG.MAX_FILE_SIZE / (1024*1024):.1f}MB",
                code="FILE_TOO_LARGE",
                details={"max_size": CFG.MAX_FILE_SIZE, "file_size": file_size}
            )
            return jsonify(error_response), 400
        
        # Generate unique filename if file already exists
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        counter = 1
        final_filename = filename
        
        while (upload_dir / final_filename).exists():
            final_filename = f"{base_name}_{counter}{extension}"
            counter += 1
        
        # Save the file
        file_path = upload_dir / final_filename
        file.save(str(file_path))
        
        logger.info(f"File uploaded successfully: {final_filename}")
        
        # Return success response with file metadata
        return jsonify({
            'success': True,
            'file': {
                'filename': final_filename,
                'original_filename': filename,
                'size': file_size,
                'extension': file_ext,
                'upload_time': datetime.utcnow().isoformat()
            },
            'message': 'File uploaded successfully'
        })
        
    except Exception as e:
        logger.exception("File upload failed")
        error_response = create_error_response(
            error="Failed to upload file",
            code="UPLOAD_ERROR",
            details={"exception": str(e)}
        )
        return jsonify(error_response), 500


@api_v1.route('/files', methods=['GET'])
def list_files():
    """List all uploaded files with pagination"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        # Check multiple locations for files
        search_paths = [
            CFG.BASE_DIR / "uploads",
            CFG.DOCUMENTS_DIR,
            CFG.DOCUMENTS_DIR.parent,  # Check parent directory too (/home/erl/Documents)
            # Also check the DocAI uploads directory
            CFG.BASE_DIR.parent / "DocAI" / "uploads" / "documents"
        ]
        
        # Get all files from all locations
        all_files = []
        seen_filenames = set()  # Track filenames to avoid duplicates
        
        for search_dir in search_paths:
            if search_dir.exists() and search_dir.is_dir():
                logger.debug(f"Searching for files in: {search_dir}")
                
                for file_path in search_dir.iterdir():
                    # Decode filename for duplicate checking
                    decoded_name = unquote(file_path.name)
                    if file_path.is_file() and decoded_name not in seen_filenames:
                        # Check if filename matches search (use decoded name)
                        if search and search.lower() not in decoded_name.lower():
                            continue
                        
                        # Only include supported document types
                        if file_path.suffix.lower() in CFG.ALLOWED_EXTENSIONS:
                            # Get file stats
                            stats = file_path.stat()
                            # Decode URL-encoded filenames (e.g., "ERL-Offer%20Letter.docx" -> "ERL-Offer Letter.docx")
                            decoded_filename = unquote(file_path.name)
                            all_files.append({
                                'filename': decoded_filename,
                                'size': stats.st_size,
                                'extension': file_path.suffix.lower(),
                                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                                'created': datetime.fromtimestamp(stats.st_ctime).isoformat()
                            })
                            seen_filenames.add(decoded_filename)
        
        # Sort by modified date (newest first)
        all_files.sort(key=lambda x: x['modified'], reverse=True)
        
        # Calculate pagination
        total_files = len(all_files)
        total_pages = (total_files + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get files for current page
        page_files = all_files[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'files': page_files,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_files': total_files,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        logger.exception("Failed to list files")
        error_response = create_error_response(
            error="Failed to list files",
            code="LIST_ERROR",
            details={"exception": str(e)}
        )
        return jsonify(error_response), 500


@api_v1.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file"""
    try:
        # Secure the filename
        safe_filename = secure_filename(filename)
        if not safe_filename:
            error_response = create_error_response(
                error="Invalid filename",
                code="INVALID_FILENAME"
            )
            return jsonify(error_response), 400
        
        # Build file path
        file_path = CFG.BASE_DIR / "uploads" / safe_filename
        
        # Check if file exists
        if not file_path.exists():
            error_response = create_error_response(
                error="File not found",
                code="FILE_NOT_FOUND"
            )
            return jsonify(error_response), 404
        
        # Delete the file
        file_path.unlink()
        
        logger.info(f"File deleted: {safe_filename}")
        
        return jsonify({
            'success': True,
            'message': f'File {safe_filename} deleted successfully'
        })
        
    except Exception as e:
        logger.exception("Failed to delete file")
        error_response = create_error_response(
            error="Failed to delete file",
            code="DELETE_ERROR",
            details={"exception": str(e)}
        )
        return jsonify(error_response), 500


# Error handlers
@api_v1.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    error_response = create_error_response(
        error="Endpoint not found",
        code="NOT_FOUND"
    )
    return jsonify(error_response), 404


@api_v1.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    error_response = create_error_response(
        error="Method not allowed",
        code="METHOD_NOT_ALLOWED"
    )
    return jsonify(error_response), 405


@api_v1.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.exception("Internal server error")
    error_response = create_error_response(
        error="Internal server error",
        code="INTERNAL_ERROR"
    )
    return jsonify(error_response), 500