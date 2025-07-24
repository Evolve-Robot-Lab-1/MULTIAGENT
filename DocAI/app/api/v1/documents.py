"""
Documents API v1 endpoints.
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.datastructures import FileStorage

from app.services.document_service import DocumentService
from app.services.base import inject
from app.models.document import (
    DocumentUploadRequest, DocumentUpdateRequest,
    DocumentSearchRequest, DocumentEdit, DocumentExportRequest
)
from app.models.api import APIResponse, PaginationParams, PaginatedResponse
from app.core.exceptions import DocAIException
from app.core.logging import get_logger


logger = get_logger(__name__)


def create_documents_blueprint() -> Blueprint:
    """Create documents API blueprint."""
    documents_bp = Blueprint('documents', __name__, url_prefix='/documents')
    
    @documents_bp.route('', methods=['GET'])
    async def list_documents():
        """List all documents with pagination."""
        try:
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status')
            
            # Get document service
            doc_service = current_app.container.get(DocumentService)
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get documents
            result = await doc_service.list_documents(
                status=status,
                limit=per_page,
                offset=offset
            )
            
            if result.success:
                docs_data = result.data
                paginated = PaginatedResponse(
                    items=docs_data['documents'],
                    total=docs_data['total'],
                    page=page,
                    per_page=per_page
                )
                
                response = APIResponse.success(paginated.model_dump())
                return jsonify(response.model_dump())
            else:
                response = APIResponse.error(result.error or "Failed to list documents")
                return jsonify(response.model_dump()), 500
                
        except Exception as e:
            logger.error(f"Error listing documents: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @documents_bp.route('', methods=['POST'])
    async def upload_document():
        """Upload a new document."""
        try:
            # Check for file
            if 'document' not in request.files:
                response = APIResponse.error("No document provided")
                return jsonify(response.model_dump()), 400
            
            file = request.files['document']
            if not file or not file.filename:
                response = APIResponse.error("No file selected")
                return jsonify(response.model_dump()), 400
            
            # Parse request parameters
            upload_request = DocumentUploadRequest(
                extract_metadata=request.form.get('extract_metadata', 'true').lower() == 'true',
                process_immediately=request.form.get('process_immediately', 'true').lower() == 'true',
                index_for_rag=request.form.get('index_for_rag', 'true').lower() == 'true'
            )
            
            # Get document service
            doc_service = current_app.container.get(DocumentService)
            
            # Upload document
            result = await doc_service.upload_document(file, upload_request)
            
            if result.success:
                response = APIResponse.success(
                    result.data,
                    message="Document uploaded successfully"
                )
                return jsonify(response.model_dump()), 201
            else:
                response = APIResponse.error(result.error or "Upload failed")
                return jsonify(response.model_dump()), 400
                
        except DocAIException as e:
            response = APIResponse.error(str(e), details=e.details)
            return jsonify(response.model_dump()), 400
        except Exception as e:
            logger.error(f"Error uploading document: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @documents_bp.route('/<document_id>', methods=['GET'])
    async def get_document(document_id: str):
        """Get document by ID."""
        try:
            doc_service = current_app.container.get(DocumentService)
            result = await doc_service.get_document(document_id)
            
            if result.success:
                response = APIResponse.success(result.data)
                return jsonify(response.model_dump())
            else:
                response = APIResponse.error(result.error or "Document not found")
                return jsonify(response.model_dump()), 404
                
        except Exception as e:
            logger.error(f"Error getting document: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @documents_bp.route('/<document_id>', methods=['PUT'])
    async def update_document(document_id: str):
        """Update document metadata."""
        try:
            # Parse request
            data = request.get_json()
            update_request = DocumentUpdateRequest(**data)
            
            doc_service = current_app.container.get(DocumentService)
            result = await doc_service.update_document(document_id, update_request)
            
            if result.success:
                response = APIResponse.success(
                    result.data,
                    message="Document updated successfully"
                )
                return jsonify(response.model_dump())
            else:
                response = APIResponse.error(result.error or "Update failed")
                return jsonify(response.model_dump()), 400
                
        except Exception as e:
            logger.error(f"Error updating document: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @documents_bp.route('/<document_id>', methods=['DELETE'])
    async def delete_document(document_id: str):
        """Delete a document."""
        try:
            doc_service = current_app.container.get(DocumentService)
            result = await doc_service.delete_document(document_id)
            
            if result.success:
                response = APIResponse.success(
                    None,
                    message="Document deleted successfully"
                )
                return jsonify(response.model_dump())
            else:
                response = APIResponse.error(result.error or "Delete failed")
                return jsonify(response.model_dump()), 400
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @documents_bp.route('/<document_id>/content', methods=['GET'])
    async def get_document_content(document_id: str):
        """Get document content."""
        try:
            format = request.args.get('format', 'text')
            
            doc_service = current_app.container.get(DocumentService)
            result = await doc_service.get_document_content(document_id, format)
            
            if result.success:
                response = APIResponse.success(result.data)
                return jsonify(response.model_dump())
            else:
                response = APIResponse.error(result.error or "Content not available")
                return jsonify(response.model_dump()), 404
                
        except Exception as e:
            logger.error(f"Error getting document content: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @documents_bp.route('/search', methods=['POST'])
    async def search_documents():
        """Search documents."""
        try:
            data = request.get_json()
            search_request = DocumentSearchRequest(**data)
            
            # This would integrate with RAG service
            response = APIResponse.success(
                {'results': [], 'query': search_request.query},
                message="Search functionality coming soon"
            )
            return jsonify(response.model_dump())
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @documents_bp.route('/rag/status', methods=['GET'])
    async def rag_status():
        """Get RAG status (legacy compatibility)."""
        try:
            doc_service = current_app.container.get(DocumentService)
            status = await doc_service.get_status()
            
            response = APIResponse.success(status)
            return jsonify(response.model_dump())
            
        except Exception as e:
            logger.error(f"Error getting RAG status: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    return documents_bp