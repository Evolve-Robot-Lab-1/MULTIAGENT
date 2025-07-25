"""
Document processing service.
Handles document upload, processing, and management.
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime
import tempfile

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from app.services.base import BaseService, ServiceResult, CachedService
from app.models.document import (
    Document, DocumentType, DocumentStatus, DocumentMetadata,
    DocumentContent, DocumentUploadRequest, DocumentUpdateRequest,
    DocumentEdit, DocumentExportRequest
)
from app.core.config import Config
from app.core.exceptions import (
    DocumentNotFoundError, DocumentProcessingError,
    UnsupportedFileTypeError, FileSizeLimitError,
    FileOperationError
)
from app.utils.converters.base import DocumentConverter
from app.utils.converters.docx_converter import DocxConverter
from app.utils.converters.pdf_converter import PDFConverter
from app.utils.converters.text_converter import TextConverter


class DocumentService(CachedService):
    """
    Service for document management and processing.
    """
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        
        # Initialize converters
        self.converters: Dict[DocumentType, DocumentConverter] = {
            DocumentType.DOCX: DocxConverter(config),
            DocumentType.DOC: DocxConverter(config),  # Use same converter
            DocumentType.PDF: PDFConverter(config),
            DocumentType.TXT: TextConverter(config)
        }
        
        # Document storage (in-memory for now, replace with database)
        self._documents: Dict[str, Document] = {}
        
    async def initialize(self) -> None:
        """Initialize service and ensure directories exist."""
        await super().initialize()
        
        # Ensure upload directories exist
        self.config.storage.upload_folder.mkdir(parents=True, exist_ok=True)
        self.config.storage.documents_folder.mkdir(parents=True, exist_ok=True)
        self.config.storage.temp_folder.mkdir(parents=True, exist_ok=True)
    
    async def upload_document(
        self,
        file: FileStorage,
        request: DocumentUploadRequest
    ) -> ServiceResult:
        """
        Upload and process a document.
        
        Args:
            file: Uploaded file
            request: Upload request parameters
            
        Returns:
            ServiceResult with Document data
        """
        try:
            # Validate file
            if not file or not file.filename:
                return ServiceResult.fail("No file provided")
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > self.config.storage.max_content_length:
                raise FileSizeLimitError(
                    file_size,
                    self.config.storage.max_content_length
                )
            
            # Check file type
            filename = secure_filename(file.filename)
            file_ext = Path(filename).suffix.lower()
            doc_type = DocumentType.from_extension(file_ext)
            
            if not doc_type:
                raise UnsupportedFileTypeError(
                    file_ext,
                    list(self.config.storage.allowed_extensions)
                )
            
            # Generate document ID and paths
            doc_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            stored_filename = f"{timestamp}_{doc_id}_{filename}"
            file_path = self.config.storage.documents_folder / stored_filename
            
            # Save file
            file.save(str(file_path))
            self.logger.info(f"Document saved: {file_path}")
            
            # Create document record
            document = Document(
                id=doc_id,
                filename=stored_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_type=doc_type,
                file_size=file_size,
                file_hash=""  # Will be generated by validator
            )
            
            # Add custom metadata
            if request.custom_metadata:
                document.metadata.custom.update(request.custom_metadata)
            
            # Store document
            self._documents[doc_id] = document
            
            # Process if requested
            if request.process_immediately:
                await self._process_document(document, request)
            
            return ServiceResult.ok(
                document.to_dict(),
                document_count=len(self._documents)
            )
            
        except (FileSizeLimitError, UnsupportedFileTypeError) as e:
            self.logger.warning(f"Document upload validation failed: {e}")
            return ServiceResult.fail(str(e))
        except Exception as e:
            self.logger.error(f"Document upload failed: {e}", exc_info=True)
            return ServiceResult.fail(f"Upload failed: {str(e)}")
    
    async def _process_document(
        self,
        document: Document,
        request: DocumentUploadRequest
    ) -> None:
        """
        Process a document (extract content, metadata, etc).
        
        Args:
            document: Document to process
            request: Processing options
        """
        start_time = datetime.utcnow()
        
        try:
            document.status = DocumentStatus.PROCESSING
            
            # Get appropriate converter
            converter = self.converters.get(document.file_type)
            if not converter:
                raise DocumentProcessingError(
                    document.filename,
                    f"No converter for type {document.file_type}"
                )
            
            # Convert document
            result = await converter.convert(document.file_path)
            
            # Update document with results
            if request.extract_metadata and result.metadata:
                document.metadata = result.metadata
            
            # Cache content if needed
            if result.content:
                self.cache_set(f"content:{document.id}", result.content)
            
            # Update processing info
            document.status = DocumentStatus.COMPLETED
            document.processed_at = datetime.utcnow()
            document.processing_time = (
                datetime.utcnow() - start_time
            ).total_seconds()
            
            self.logger.info(
                f"Document processed successfully: {document.id} "
                f"in {document.processing_time:.2f}s"
            )
            
        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error = str(e)
            self.logger.error(
                f"Document processing failed: {document.id}",
                exc_info=True
            )
            raise DocumentProcessingError(document.filename, str(e))
    
    async def get_document(self, document_id: str) -> ServiceResult:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            ServiceResult with Document data
        """
        document = self._documents.get(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        
        return ServiceResult.ok(document.to_dict())
    
    async def get_document_content(
        self,
        document_id: str,
        format: str = "text"
    ) -> ServiceResult:
        """
        Get document content.
        
        Args:
            document_id: Document ID
            format: Content format ('text', 'html', 'pages')
            
        Returns:
            ServiceResult with DocumentContent
        """
        document = self._documents.get(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        
        # Check cache first
        cached_content = self.cache_get(f"content:{document_id}")
        if cached_content:
            content = DocumentContent(
                document_id=document_id,
                content_type="text/plain",
                content=cached_content
            )
            return ServiceResult.ok(content.model_dump())
        
        # Process if not cached
        if document.status != DocumentStatus.COMPLETED:
            return ServiceResult.fail("Document not yet processed")
        
        # Get converter and extract content
        converter = self.converters.get(document.file_type)
        if not converter:
            return ServiceResult.fail(f"No converter for type {document.file_type}")
        
        result = await converter.convert(document.file_path)
        
        # Cache for future use
        if result.content:
            self.cache_set(f"content:{document_id}", result.content)
        
        content = DocumentContent(
            document_id=document_id,
            content_type=result.content_type,
            content=result.content or "",
            pages=result.pages,
            formatting_preserved=result.formatting_preserved
        )
        
        return ServiceResult.ok(content.model_dump())
    
    async def update_document(
        self,
        document_id: str,
        request: DocumentUpdateRequest
    ) -> ServiceResult:
        """
        Update document metadata.
        
        Args:
            document_id: Document ID
            request: Update request
            
        Returns:
            ServiceResult with updated Document
        """
        document = self._documents.get(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        
        # Update metadata
        if request.metadata:
            document.metadata = request.metadata
        
        document.updated_at = datetime.utcnow()
        
        # Clear cache if reindexing
        if request.reindex:
            self.cache_delete(f"content:{document_id}")
            document.is_indexed = False
        
        return ServiceResult.ok(document.to_dict())
    
    async def delete_document(self, document_id: str) -> ServiceResult:
        """
        Delete a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            ServiceResult
        """
        document = self._documents.get(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        
        try:
            # Delete file
            if document.file_path.exists():
                document.file_path.unlink()
                self.logger.info(f"Deleted file: {document.file_path}")
            
            # Clear cache
            self.cache_delete(f"content:{document_id}")
            
            # Remove from storage
            del self._documents[document_id]
            
            return ServiceResult.ok(
                None,
                message="Document deleted successfully",
                document_count=len(self._documents)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to delete document: {e}", exc_info=True)
            return ServiceResult.fail(f"Delete failed: {str(e)}")
    
    async def list_documents(
        self,
        status: Optional[DocumentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> ServiceResult:
        """
        List documents with optional filtering.
        
        Args:
            status: Filter by status
            limit: Maximum number of results
            offset: Skip this many results
            
        Returns:
            ServiceResult with list of Documents
        """
        # Filter documents
        documents = list(self._documents.values())
        
        if status:
            documents = [d for d in documents if d.status == status]
        
        # Sort by created date (newest first)
        documents.sort(key=lambda d: d.created_at, reverse=True)
        
        # Apply pagination
        total = len(documents)
        documents = documents[offset:offset + limit]
        
        return ServiceResult.ok(
            {
                'documents': [d.to_dict() for d in documents],
                'total': total,
                'limit': limit,
                'offset': offset
            }
        )
    
    async def edit_document(
        self,
        document_id: str,
        edit: DocumentEdit
    ) -> ServiceResult:
        """
        Edit document content.
        
        Args:
            document_id: Document ID
            edit: Edit operation
            
        Returns:
            ServiceResult
        """
        document = self._documents.get(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        
        # Only support DOCX editing for now
        if document.file_type not in [DocumentType.DOCX, DocumentType.DOC]:
            return ServiceResult.fail(
                f"Editing not supported for {document.file_type} files"
            )
        
        try:
            # Get converter
            converter = self.converters[document.file_type]
            
            # Apply edit
            success = await converter.edit_document(
                document.file_path,
                edit.operation,
                edit.target,
                edit.replacement,
                edit.preserve_formatting
            )
            
            if success:
                # Clear cache
                self.cache_delete(f"content:{document_id}")
                document.updated_at = datetime.utcnow()
                
                return ServiceResult.ok(
                    None,
                    message="Document edited successfully"
                )
            else:
                return ServiceResult.fail("Edit operation failed")
                
        except Exception as e:
            self.logger.error(f"Document edit failed: {e}", exc_info=True)
            return ServiceResult.fail(f"Edit failed: {str(e)}")
    
    async def export_document(
        self,
        document_id: str,
        request: DocumentExportRequest
    ) -> ServiceResult:
        """
        Export document in specified format.
        
        Args:
            document_id: Document ID
            request: Export request
            
        Returns:
            ServiceResult with file path
        """
        document = self._documents.get(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)
        
        try:
            # Generate export filename
            export_filename = (
                f"{Path(document.original_filename).stem}"
                f"_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                f".{request.format}"
            )
            export_path = self.config.storage.temp_folder / export_filename
            
            # Get converter
            converter = self.converters.get(document.file_type)
            if not converter:
                return ServiceResult.fail(
                    f"No converter for type {document.file_type}"
                )
            
            # Export document
            success = await converter.export(
                document.file_path,
                export_path,
                request.format,
                include_metadata=request.include_metadata
            )
            
            if success:
                return ServiceResult.ok(
                    {
                        'filename': export_filename,
                        'path': str(export_path),
                        'format': request.format,
                        'size': export_path.stat().st_size
                    }
                )
            else:
                return ServiceResult.fail("Export failed")
                
        except Exception as e:
            self.logger.error(f"Document export failed: {e}", exc_info=True)
            return ServiceResult.fail(f"Export failed: {str(e)}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        status_counts = {}
        for status in DocumentStatus:
            count = sum(1 for d in self._documents.values() if d.status == status)
            status_counts[status.value] = count
        
        return {
            'total_documents': len(self._documents),
            'status_counts': status_counts,
            'cache_size': len(self._cache),
            'storage_used': sum(d.file_size for d in self._documents.values()),
            'initialized': self.is_initialized
        }