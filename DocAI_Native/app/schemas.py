"""
Pydantic schemas for request validation
Ensures type safety and data validation
"""

from pydantic import BaseModel, Field, validator
from pathlib import Path
from typing import Optional, Dict, Any


class FileRequest(BaseModel):
    """Request to open a file"""
    path: str = Field(..., description="Absolute path to the file")
    
    @validator('path')
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Path cannot be empty')
        
        path = Path(v)
        if not path.is_absolute():
            raise ValueError('Path must be absolute')
        
        return v


class ProcessRequest(BaseModel):
    """Request to process a document"""
    path: str = Field(..., description="Absolute path to the file")
    mode: str = Field(default="native", description="Processing mode: native or html")
    
    @validator('path')
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Path cannot be empty')
        
        path = Path(v)
        if not path.is_absolute():
            raise ValueError('Path must be absolute')
        
        return v
    
    @validator('mode')
    def validate_mode(cls, v):
        if v not in ['native', 'html']:
            raise ValueError('Mode must be either "native" or "html"')
        return v


class ViewRequest(BaseModel):
    """Request to view a document"""
    path: str = Field(..., description="Absolute path to the file")
    container_id: Optional[str] = Field(None, description="Container ID for embedding")
    
    @validator('path')
    def validate_path(cls, v):
        if not v or not v.strip():
            raise ValueError('Path cannot be empty')
        
        path = Path(v)
        if not path.is_absolute():
            raise ValueError('Path must be absolute')
        
        return v


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: str
    version: str
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response format"""
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str


class ConfigResponse(BaseModel):
    """Configuration response"""
    app_name: str
    version: str
    supported_formats: list
    max_file_size: int
    libreoffice_available: bool