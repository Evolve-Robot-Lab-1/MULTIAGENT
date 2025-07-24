"""
Base converter interface for document processing.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from app.core.config import Config
from app.core.logging import get_logger
from app.models.document import DocumentMetadata


@dataclass
class ConversionResult:
    """Result of document conversion."""
    content: Optional[str] = None
    pages: Optional[List[str]] = None
    content_type: str = "text/plain"
    metadata: Optional[DocumentMetadata] = None
    formatting_preserved: bool = False
    images: Optional[List[Dict[str, Any]]] = None
    tables: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class DocumentConverter(ABC):
    """
    Abstract base class for document converters.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize converter.
        
        Args:
            config: Application configuration
        """
        from app.core.config import get_config
        self.config = config or get_config()
        self.logger = get_logger(self.__class__.__module__)
    
    @abstractmethod
    async def convert(self, file_path: Path) -> ConversionResult:
        """
        Convert document to text/structured format.
        
        Args:
            file_path: Path to document file
            
        Returns:
            ConversionResult with extracted content
        """
        pass
    
    @abstractmethod
    async def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from document.
        
        Args:
            file_path: Path to document file
            
        Returns:
            DocumentMetadata
        """
        pass
    
    async def validate_file(self, file_path: Path) -> bool:
        """
        Validate that file exists and is readable.
        
        Args:
            file_path: Path to document file
            
        Returns:
            True if valid, False otherwise
        """
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
        
        if not file_path.is_file():
            self.logger.error(f"Not a file: {file_path}")
            return False
        
        if not os.access(file_path, os.R_OK):
            self.logger.error(f"File not readable: {file_path}")
            return False
        
        return True
    
    async def edit_document(
        self,
        file_path: Path,
        operation: str,
        target: str,
        replacement: Optional[str] = None,
        preserve_formatting: bool = True
    ) -> bool:
        """
        Edit document content (optional - override in subclasses).
        
        Args:
            file_path: Path to document
            operation: Edit operation ('replace', 'insert', 'delete')
            target: Target text or position
            replacement: Replacement text
            preserve_formatting: Whether to preserve formatting
            
        Returns:
            True if successful
        """
        self.logger.warning(
            f"Edit not implemented for {self.__class__.__name__}"
        )
        return False
    
    async def export(
        self,
        source_path: Path,
        target_path: Path,
        format: str,
        include_metadata: bool = False
    ) -> bool:
        """
        Export document to different format (optional - override in subclasses).
        
        Args:
            source_path: Source document path
            target_path: Target path for exported file
            format: Target format
            include_metadata: Whether to include metadata
            
        Returns:
            True if successful
        """
        self.logger.warning(
            f"Export not implemented for {self.__class__.__name__}"
        )
        return False
    
    def _extract_basic_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract basic metadata from file system.
        
        Args:
            file_path: Path to file
            
        Returns:
            DocumentMetadata with basic info
        """
        stat = file_path.stat()
        
        return DocumentMetadata(
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime)
        )


import os