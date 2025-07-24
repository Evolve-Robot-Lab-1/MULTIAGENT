"""
Unit tests for RAGService.
"""
import pytest
from unittest.mock import Mock, patch

from app.services.rag_service import RAGService


@pytest.fixture
async def rag_service(test_config):
    """Create RAG service instance."""
    service = RAGService(test_config)
    await service.initialize()
    return service


@pytest.mark.asyncio
class TestRAGService:
    """Test RAGService functionality."""
    
    async def test_initialize(self, rag_service):
        """Test service initialization."""
        assert rag_service.is_initialized
        assert len(rag_service._chunks) == 0
        assert len(rag_service._document_map) == 0
    
    async def test_index_document(self, rag_service):
        """Test document indexing."""
        doc_id = "test-doc-123"
        content = "This is a test document with some content that should be chunked properly."
        metadata = {"title": "Test Document"}
        
        result = await rag_service.index_document(doc_id, content, metadata)
        
        assert result.success
        assert result.data['document_id'] == doc_id
        assert result.data['chunk_count'] > 0
        
        # Verify chunks were created
        assert doc_id in rag_service._document_map
        assert len(rag_service._chunks) > 0
    
    async def test_index_document_long_content(self, rag_service):
        """Test indexing document with long content."""
        doc_id = "long-doc"
        # Create content longer than chunk size
        content = "Test content. " * 100  # Should create multiple chunks
        
        result = await rag_service.index_document(doc_id, content)
        
        assert result.success
        chunk_count = result.data['chunk_count']
        assert chunk_count > 1
        
        # Verify all chunks belong to document
        chunk_indices = rag_service._document_map[doc_id]
        assert len(chunk_indices) == chunk_count
    
    async def test_remove_document(self, rag_service):
        """Test document removal."""
        # First index a document
        doc_id = "remove-test"
        content = "Document to be removed"
        await rag_service.index_document(doc_id, content)
        
        # Remove it
        result = await rag_service.remove_document(doc_id)
        
        assert result.success
        assert doc_id not in rag_service._document_map
        
        # Verify chunks are marked as deleted
        for chunk in rag_service._chunks:
            if chunk.get('document_id') == doc_id:
                assert chunk.get('deleted') is True
    
    async def test_remove_nonexistent_document(self, rag_service):
        """Test removing non-existent document."""
        result = await rag_service.remove_document("non-existent")
        
        assert not result.success
        assert "not in index" in result.error
    
    async def test_search_basic(self, rag_service):
        """Test basic search functionality."""
        # Index some documents
        await rag_service.index_document("doc1", "Python programming is fun")
        await rag_service.index_document("doc2", "JavaScript is also fun")
        await rag_service.index_document("doc3", "Python is a great language")
        
        # Search for Python
        result = await rag_service.search("Python", limit=2)
        
        assert result.success
        assert len(result.data['results']) <= 2
        assert result.data['query'] == "Python"
        
        # Verify Python documents scored higher
        for res in result.data['results']:
            assert "python" in res['chunk']['content'].lower()
    
    async def test_search_with_document_filter(self, rag_service):
        """Test search with document ID filter."""
        # Index documents
        await rag_service.index_document("doc1", "Test content about Python")
        await rag_service.index_document("doc2", "Another test about Python")
        await rag_service.index_document("doc3", "Different content about Python")
        
        # Search only in specific documents
        result = await rag_service.search(
            "Python",
            document_ids=["doc1", "doc3"]
        )
        
        assert result.success
        # Results should only be from doc1 and doc3
        for res in result.data['results']:
            assert res['chunk']['document_id'] in ["doc1", "doc3"]
    
    async def test_search_no_results(self, rag_service):
        """Test search with no matching results."""
        # Index a document
        await rag_service.index_document("doc1", "Some content here")
        
        # Search for non-existent term
        result = await rag_service.search("nonexistentterm")
        
        assert result.success
        assert len(result.data['results']) == 0
    
    async def test_search_deleted_documents(self, rag_service):
        """Test that deleted documents don't appear in search."""
        # Index and then remove a document
        await rag_service.index_document("deleted-doc", "Content with Python")
        await rag_service.remove_document("deleted-doc")
        
        # Search should not return deleted chunks
        result = await rag_service.search("Python")
        
        assert result.success
        for res in result.data['results']:
            assert res['chunk']['document_id'] != "deleted-doc"
    
    async def test_get_status(self, rag_service):
        """Test getting service status."""
        # Index some documents
        await rag_service.index_document("doc1", "Content 1")
        await rag_service.index_document("doc2", "Content 2")
        
        status = await rag_service.get_status()
        
        assert status['total_documents'] == 2
        assert status['total_chunks'] >= 2
        assert status['embedding_model'] == test_config.rag.embedding_model
        assert status['chunk_size'] == test_config.rag.chunk_size
        assert status['initialized'] is True