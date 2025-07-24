"""
Service Interfaces for DocAI Native
Defines contracts for swappable implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path

class IDocumentProcessor(ABC):
    """Interface for document processing implementations"""
    
    @abstractmethod
    def process_native(self, file_path: Path) -> Dict[str, Any]:
        """Process document for native viewing"""
        pass
    
    @abstractmethod
    def process_html(self, file_path: Path) -> Dict[str, Any]:
        """Process document for HTML viewing"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> set:
        """Get set of supported file extensions"""
        pass
    
    @abstractmethod
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate file before processing"""
        pass