"""
Text file converter implementation.
"""
from pathlib import Path
from typing import Optional
import chardet

from app.utils.converters.base import DocumentConverter, ConversionResult
from app.models.document import DocumentMetadata


class TextConverter(DocumentConverter):
    """
    Converter for plain text files.
    """
    
    async def convert(self, file_path: Path) -> ConversionResult:
        """
        Convert text file to standard format.
        
        Args:
            file_path: Path to text file
            
        Returns:
            ConversionResult
        """
        if not await self.validate_file(file_path):
            return ConversionResult(
                error=f"Invalid file: {file_path}"
            )
        
        try:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                detection = chardet.detect(raw_data)
                encoding = detection['encoding'] or 'utf-8'
            
            # Read file with detected encoding
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Extract metadata
            metadata = await self.extract_metadata(file_path)
            metadata.word_count = len(content.split())
            
            # Split into pages (3000 chars per page for display)
            pages = []
            page_size = 3000
            for i in range(0, len(content), page_size):
                pages.append(content[i:i + page_size])
            
            return ConversionResult(
                content=content,
                pages=pages,
                content_type="text/plain",
                metadata=metadata,
                formatting_preserved=False
            )
            
        except Exception as e:
            self.logger.error(
                f"Error converting text file {file_path}: {e}",
                exc_info=True
            )
            return ConversionResult(
                error=f"Conversion failed: {str(e)}"
            )
    
    async def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            DocumentMetadata
        """
        metadata = self._extract_basic_metadata(file_path)
        
        try:
            # Count lines
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # Extract title from first non-empty line
            for line in lines:
                line = line.strip()
                if line:
                    metadata.title = line[:100]  # First 100 chars
                    break
            
            # Set page count (lines / 50)
            metadata.page_count = max(1, len(lines) // 50)
            
        except Exception as e:
            self.logger.warning(
                f"Error extracting metadata from {file_path}: {e}"
            )
        
        return metadata