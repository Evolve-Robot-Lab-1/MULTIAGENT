"""
Custom exceptions for DocAI application.
Provides a hierarchy of exceptions for better error handling.
"""
from typing import Optional, Dict, Any


class DocAIException(Exception):
    """Base exception for all DocAI errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }


# Configuration Exceptions
class ConfigurationError(DocAIException):
    """Raised when configuration is invalid or missing."""
    pass


# Document Processing Exceptions
class DocumentException(DocAIException):
    """Base exception for document-related errors."""
    pass


class DocumentNotFoundError(DocumentException):
    """Raised when a document is not found."""
    
    def __init__(self, document_id: str):
        super().__init__(
            f"Document not found: {document_id}",
            {'document_id': document_id}
        )


class DocumentProcessingError(DocumentException):
    """Raised when document processing fails."""
    
    def __init__(self, filename: str, reason: str):
        super().__init__(
            f"Failed to process document '{filename}': {reason}",
            {'filename': filename, 'reason': reason}
        )


class UnsupportedFileTypeError(DocumentException):
    """Raised when file type is not supported."""
    
    def __init__(self, file_type: str, supported_types: list):
        super().__init__(
            f"Unsupported file type: {file_type}",
            {'file_type': file_type, 'supported_types': supported_types}
        )


class FileSizeLimitError(DocumentException):
    """Raised when file size exceeds limit."""
    
    def __init__(self, size: int, max_size: int):
        super().__init__(
            f"File size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)",
            {'size': size, 'max_size': max_size}
        )


# AI/Chat Exceptions
class AIException(DocAIException):
    """Base exception for AI-related errors."""
    pass


class AIProviderError(AIException):
    """Raised when AI provider fails."""
    
    def __init__(self, provider: str, reason: str):
        super().__init__(
            f"AI provider '{provider}' error: {reason}",
            {'provider': provider, 'reason': reason}
        )


class ChatException(AIException):
    """Base exception for chat-related errors."""
    pass


class ChatSessionNotFoundError(ChatException):
    """Raised when chat session is not found."""
    
    def __init__(self, session_id: str):
        super().__init__(
            f"Chat session not found: {session_id}",
            {'session_id': session_id}
        )


# RAG Exceptions
class RAGException(DocAIException):
    """Base exception for RAG-related errors."""
    pass


class VectorStoreError(RAGException):
    """Raised when vector store operation fails."""
    pass


class EmbeddingError(RAGException):
    """Raised when embedding generation fails."""
    pass


class QueryError(RAGException):
    """Raised when RAG query fails."""
    pass


# Agent Exceptions
class AgentException(DocAIException):
    """Base exception for agent-related errors."""
    pass


class AgentConnectionError(AgentException):
    """Raised when agent connection fails."""
    
    def __init__(self, agent_name: str, reason: str):
        super().__init__(
            f"Failed to connect to {agent_name} agent: {reason}",
            {'agent': agent_name, 'reason': reason}
        )


class AgentTimeoutError(AgentException):
    """Raised when agent operation times out."""
    
    def __init__(self, agent_name: str, timeout: int):
        super().__init__(
            f"{agent_name} agent timed out after {timeout} seconds",
            {'agent': agent_name, 'timeout': timeout}
        )


class AgentNotAvailableError(AgentException):
    """Raised when agent is not available."""
    
    def __init__(self, agent_name: str):
        super().__init__(
            f"{agent_name} agent is not available",
            {'agent': agent_name}
        )


# Validation Exceptions
class ValidationError(DocAIException):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, reason: str):
        super().__init__(
            f"Validation error for field '{field}': {reason}",
            {'field': field, 'reason': reason}
        )


class RequestValidationError(ValidationError):
    """Raised when request validation fails."""
    
    def __init__(self, errors: Dict[str, str]):
        message = "Request validation failed"
        super().__init__(message, errors)
        self.errors = errors


# Storage Exceptions
class StorageException(DocAIException):
    """Base exception for storage-related errors."""
    pass


class StorageFullError(StorageException):
    """Raised when storage is full."""
    
    def __init__(self, available: int, required: int):
        super().__init__(
            f"Insufficient storage: {required} bytes required, {available} bytes available",
            {'available': available, 'required': required}
        )


class FileOperationError(StorageException):
    """Raised when file operation fails."""
    
    def __init__(self, operation: str, file_path: str, reason: str):
        super().__init__(
            f"File {operation} failed for '{file_path}': {reason}",
            {'operation': operation, 'file_path': file_path, 'reason': reason}
        )