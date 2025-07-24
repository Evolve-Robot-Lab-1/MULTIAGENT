"""
Unit tests for DocumentService.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile

from app.services.document_service import DocumentService
from app.models.document import (
    Document, DocumentType, DocumentStatus,
    DocumentUploadRequest, DocumentUpdateRequest
)
from app.core.exceptions import (
    DocumentNotFoundError, DocumentProcessingError,
    UnsupportedFileTypeError, FileSizeLimitError
)


@pytest.fixture
async def document_service(test_config):
    """Create document service instance."""
    service = DocumentService(test_config)
    await service.initialize()
    return service


@pytest.mark.asyncio
class TestDocumentService:
    """Test DocumentService functionality."""
    
    async def test_initialize(self, document_service):
        """Test service initialization."""
        assert document_service.is_initialized
        assert len(document_service.converters) > 0
        assert DocumentType.PDF in document_service.converters
        assert DocumentType.DOCX in document_service.converters
        assert DocumentType.TXT in document_service.converters
    
    async def test_upload_document_success(self, document_service, sample_file):
        """Test successful document upload."""
        request = DocumentUploadRequest(
            process_immediately=False,
            custom_metadata={'test': 'value'}
        )
        
        result = await document_service.upload_document(sample_file, request)
        
        assert result.success
        assert result.data['filename']
        assert result.data['file_type'] == 'txt'
        assert result.data['file_size'] == 17  # "Test file content"
        assert result.metadata['document_count'] == 1
    
    async def test_upload_document_no_file(self, document_service):
        """Test upload with no file."""
        request = DocumentUploadRequest()
        
        result = await document_service.upload_document(None, request)
        
        assert not result.success
        assert "No file provided" in result.error
    
    async def test_upload_document_file_too_large(self, document_service, test_config):
        """Test upload with file exceeding size limit."""
        from werkzeug.datastructures import FileStorage
        from io import BytesIO
        
        # Create large file
        large_data = BytesIO(b"x" * (test_config.storage.max_content_length + 1))
        large_file = FileStorage(
            stream=large_data,
            filename="large.txt",
            content_type="text/plain"
        )
        
        request = DocumentUploadRequest()
        
        result = await document_service.upload_document(large_file, request)
        
        assert not result.success
        assert "exceeds maximum allowed size" in result.error
    
    async def test_upload_document_unsupported_type(self, document_service):
        """Test upload with unsupported file type."""
        from werkzeug.datastructures import FileStorage
        from io import BytesIO
        
        data = BytesIO(b"Test")
        file = FileStorage(
            stream=data,
            filename="test.xyz",
            content_type="application/octet-stream"
        )
        
        request = DocumentUploadRequest()
        
        result = await document_service.upload_document(file, request)
        
        assert not result.success
        assert "Unsupported file type" in result.error
    
    async def test_get_document_exists(self, document_service, sample_file):
        """Test getting existing document."""
        # Upload a document first
        request = DocumentUploadRequest(process_immediately=False)
        upload_result = await document_service.upload_document(sample_file, request)
        doc_id = upload_result.data['id']
        
        # Get the document
        result = await document_service.get_document(doc_id)
        
        assert result.success
        assert result.data['id'] == doc_id
        assert result.data['filename']
    
    async def test_get_document_not_found(self, document_service):
        """Test getting non-existent document."""
        with pytest.raises(DocumentNotFoundError):
            await document_service.get_document('non-existent-id')
    
    async def test_delete_document_success(self, document_service, sample_file):
        """Test successful document deletion."""
        # Upload a document first
        request = DocumentUploadRequest(process_immediately=False)
        upload_result = await document_service.upload_document(sample_file, request)
        doc_id = upload_result.data['id']
        
        # Delete the document
        result = await document_service.delete_document(doc_id)
        
        assert result.success
        assert result.metadata['document_count'] == 0
        
        # Verify it's deleted
        with pytest.raises(DocumentNotFoundError):
            await document_service.get_document(doc_id)
    
    async def test_list_documents(self, document_service, sample_file):
        """Test listing documents."""
        # Upload multiple documents
        request = DocumentUploadRequest(process_immediately=False)
        
        for i in range(3):
            sample_file.filename = f"test{i}.txt"
            await document_service.upload_document(sample_file, request)
        
        # List all documents
        result = await document_service.list_documents()
        
        assert result.success
        assert result.data['total'] == 3
        assert len(result.data['documents']) == 3
        
        # Test with pagination
        result = await document_service.list_documents(limit=2)
        assert len(result.data['documents']) == 2
        
        # Test with offset
        result = await document_service.list_documents(limit=2, offset=2)
        assert len(result.data['documents']) == 1
    
    async def test_update_document_metadata(self, document_service, sample_file):
        """Test updating document metadata."""
        # Upload a document
        request = DocumentUploadRequest(process_immediately=False)
        upload_result = await document_service.upload_document(sample_file, request)
        doc_id = upload_result.data['id']
        
        # Update metadata
        from app.models.document import DocumentMetadata
        update_request = DocumentUpdateRequest(
            metadata=DocumentMetadata(
                title="Updated Title",
                author="Test Author",
                keywords=["test", "document"]
            )
        )
        
        result = await document_service.update_document(doc_id, update_request)
        
        assert result.success
        assert result.data['metadata']['title'] == "Updated Title"
        assert result.data['metadata']['author'] == "Test Author"
    
    async def test_get_document_content_cached(self, document_service, sample_file):
        """Test getting document content from cache."""
        # Upload and process a document
        request = DocumentUploadRequest(process_immediately=True)
        
        # Mock the converter
        with patch.object(document_service.converters[DocumentType.TXT], 'convert') as mock_convert:
            mock_convert.return_value = AsyncMock(
                content="Test content",
                content_type="text/plain",
                pages=["Test content"],
                formatting_preserved=False
            )()
            
            upload_result = await document_service.upload_document(sample_file, request)
            doc_id = upload_result.data['id']
        
        # Get content (should use cache)
        result = await document_service.get_document_content(doc_id)
        
        assert result.success
        assert result.data['content'] == "Test content"
        assert result.data['content_type'] == "text/plain"
    
    async def test_export_document(self, document_service, sample_file):
        """Test document export."""
        # Upload a document
        request = DocumentUploadRequest(process_immediately=False)
        upload_result = await document_service.upload_document(sample_file, request)
        doc_id = upload_result.data['id']
        
        # Mock converter export
        from app.models.document import DocumentExportRequest
        export_request = DocumentExportRequest(
            document_id=doc_id,
            format="docx"
        )
        
        with patch.object(document_service.converters[DocumentType.TXT], 'export') as mock_export:
            mock_export.return_value = True
            
            result = await document_service.export_document(doc_id, export_request)
            
            assert result.success
            assert result.data['format'] == "docx"
            assert 'path' in result.data
    
    async def test_get_status(self, document_service, sample_file):
        """Test getting service status."""
        # Upload some documents
        request = DocumentUploadRequest(process_immediately=False)
        await document_service.upload_document(sample_file, request)
        
        status = await document_service.get_status()
        
        assert status['total_documents'] == 1
        assert status['initialized'] is True
        assert 'status_counts' in status
        assert status['status_counts']['pending'] == 1