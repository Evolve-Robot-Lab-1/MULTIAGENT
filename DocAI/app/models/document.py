"""
Document-related models and data structures.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, validator, field_validator
import hashlib

from app.utils.validators import validate_filename, validate_uuid


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    
    @classmethod
    def from_extension(cls, extension: str) -> Optional['DocumentType']:
        """Get document type from file extension."""
        ext = extension.lower().lstrip('.')
        try:
            return cls(ext)
        except ValueError:
            return None


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentMetadata(BaseModel):
    """Document metadata."""
    title: Optional[str] = None
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    custom: Dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """
    Document model representing a processed document.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    filename: str
    original_filename: str
    file_path: Path
    file_type: DocumentType
    file_size: int
    file_hash: str
    status: DocumentStatus = DocumentStatus.PENDING
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    
    # Processing information
    processed_at: Optional[datetime] = None
    processing_time: Optional[float] = None  # seconds
    error: Optional[str] = None
    
    # RAG information
    is_indexed: bool = False
    chunk_count: Optional[int] = None
    embedding_model: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('file_hash', pre=True, always=True)
    def generate_file_hash(cls, v, values):
        """Generate file hash if not provided."""
        if v:
            return v
        
        file_path = values.get('file_path')
        if file_path and isinstance(file_path, Path) and file_path.exists():
            return cls._calculate_file_hash(file_path)
        
        # Generate from filename and timestamp
        filename = values.get('filename', '')
        timestamp = datetime.utcnow().isoformat()
        return hashlib.sha256(f"{filename}{timestamp}".encode()).hexdigest()[:16]
    
    @staticmethod
    def _calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()[:16]  # Use first 16 chars
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type.value,
            'file_size': self.file_size,
            'status': self.status.value,
            'metadata': self.metadata.model_dump(),
            'is_indexed': self.is_indexed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    extract_metadata: bool = Field(True, description="Extract document metadata")
    process_immediately: bool = Field(True, description="Process document immediately after upload")
    index_for_rag: bool = Field(True, description="Index document for RAG search")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata to attach")
    
    @field_validator('custom_metadata')
    @classmethod
    def validate_metadata(cls, v):
        """Ensure metadata is serializable."""
        if v:
            try:
                import json
                json.dumps(v)
            except (TypeError, ValueError):
                raise ValueError("Custom metadata must be JSON serializable")
        return v


class DocumentUpdateRequest(BaseModel):
    """Request model for document update."""
    metadata: Optional[DocumentMetadata] = None
    reindex: bool = False


class DocumentContent(BaseModel):
    """Document content after processing."""
    document_id: str
    content_type: str = "text/plain"
    content: str
    pages: Optional[List[str]] = None  # For multi-page documents
    extracted_text: Optional[str] = None
    formatting_preserved: bool = False


class DocumentChunk(BaseModel):
    """A chunk of document for RAG processing."""
    id: str
    document_id: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class DocumentSearchRequest(BaseModel):
    """Request model for document search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    document_ids: Optional[List[str]] = Field(None, description="Filter by document IDs")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    include_content: bool = Field(False, description="Include document content in results")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Additional filters")
    
    @field_validator('document_ids')
    @classmethod
    def validate_document_ids(cls, v):
        """Validate document IDs."""
        if v:
            validated = []
            for doc_id in v:
                try:
                    validated.append(validate_uuid(doc_id))
                except Exception:
                    raise ValueError(f"Invalid document ID: {doc_id}")
            return validated
        return v
    
    @field_validator('query')
    @classmethod
    def clean_query(cls, v):
        """Clean and validate query."""
        # Remove excessive whitespace
        cleaned = ' '.join(v.split())
        if not cleaned:
            raise ValueError("Query cannot be empty")
        return cleaned


class DocumentSearchResult(BaseModel):
    """Result from document search."""
    document_id: str
    filename: str
    score: float
    highlights: List[str] = Field(default_factory=list)
    content_preview: Optional[str] = None
    metadata: DocumentMetadata


class DocumentEdit(BaseModel):
    """Model for document edit operations."""
    document_id: str
    operation: str  # 'replace', 'insert', 'delete'
    target: str  # Original text or position
    replacement: Optional[str] = None  # New text
    preserve_formatting: bool = True


class DocumentExportRequest(BaseModel):
    """Request model for document export."""
    document_id: str
    format: str = "docx"  # 'docx', 'pdf', 'txt', 'html'
    include_metadata: bool = False
    include_annotations: bool = False