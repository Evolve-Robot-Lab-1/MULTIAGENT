"""
API request and response models.
Provides consistent data structures for API communication.
"""
from typing import TypeVar, Generic, Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# Type variable for generic response data
T = TypeVar('T')


class APIStatus(str, Enum):
    """API response status codes."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper.
    
    Attributes:
        status: Response status
        data: Response data (generic type)
        error: Error details if status is error
        message: Optional message
        metadata: Additional metadata
        timestamp: Response timestamp
        request_id: Request ID for tracking
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    status: APIStatus
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    
    @classmethod
    def success(cls, data: T = None, message: str = None, **metadata) -> 'APIResponse[T]':
        """Create a success response."""
        return cls(
            status=APIStatus.SUCCESS,
            data=data,
            message=message,
            metadata=metadata
        )
    
    @classmethod
    def error(cls, error: str, details: Dict[str, Any] = None, 
             message: str = None, **metadata) -> 'APIResponse[None]':
        """Create an error response."""
        return cls(
            status=APIStatus.ERROR,
            error={'error': error, 'details': details or {}},
            message=message or error,
            metadata=metadata
        )
    
    @classmethod
    def warning(cls, data: T = None, message: str = None, **metadata) -> 'APIResponse[T]':
        """Create a warning response."""
        return cls(
            status=APIStatus.WARNING,
            data=data,
            message=message,
            metadata=metadata
        )


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.per_page


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response wrapper.
    
    Attributes:
        items: List of items
        total: Total number of items
        page: Current page
        per_page: Items per page
        pages: Total number of pages
    """
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate total pages
        if self.per_page > 0:
            self.pages = (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""
    status: APIStatus = APIStatus.ERROR
    message: str = "Validation failed"
    errors: List[ErrorDetail]


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    services: Dict[str, Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FileUploadResponse(BaseModel):
    """Response for file upload operations."""
    filename: str
    size: int
    content_type: str
    path: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProgressResponse(BaseModel):
    """Response for long-running operations."""
    task_id: str
    status: str
    progress: float = Field(0.0, ge=0.0, le=100.0)
    message: Optional[str] = None
    result: Optional[Any] = None
    started_at: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class StreamingResponse(BaseModel):
    """Model for Server-Sent Events streaming."""
    event: str
    data: Any
    id: Optional[str] = None
    retry: Optional[int] = None
    
    def to_sse(self) -> str:
        """Convert to SSE format."""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        if self.event:
            lines.append(f"event: {self.event}")
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        
        # Handle data serialization
        if isinstance(self.data, str):
            lines.append(f"data: {self.data}")
        else:
            import json
            lines.append(f"data: {json.dumps(self.data)}")
        
        return "\n".join(lines) + "\n\n"