"""
PDF file converter implementation.
"""
from pathlib import Path
from typing import Optional, List
import PyPDF2
import pdfplumber

from app.utils.converters.base import DocumentConverter, ConversionResult
from app.models.document import DocumentMetadata


class PDFConverter(DocumentConverter):
    """
    Converter for PDF files.
    """
    
    async def convert(self, file_path: Path) -> ConversionResult:
        """
        Convert PDF file to standard format.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            ConversionResult
        """
        if not await self.validate_file(file_path):
            return ConversionResult(
                error=f"Invalid file: {file_path}"
            )
        
        try:
            # Try pdfplumber first (better text extraction)
            result = await self._convert_with_pdfplumber(file_path)
            if result and not result.error:
                return result
            
            # Fallback to PyPDF2
            return await self._convert_with_pypdf2(file_path)
            
        except Exception as e:
            self.logger.error(
                f"Error converting PDF file {file_path}: {e}",
                exc_info=True
            )
            return ConversionResult(
                error=f"Conversion failed: {str(e)}"
            )
    
    async def _convert_with_pdfplumber(self, file_path: Path) -> Optional[ConversionResult]:
        """Convert using pdfplumber library."""
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                # Extract text from all pages
                pages = []
                full_text = []
                
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                        full_text.append(text)
                
                # Extract metadata
                metadata = await self.extract_metadata(file_path)
                metadata.page_count = len(pdf.pages)
                
                # Extract tables if any
                tables = []
                for i, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        tables.append({
                            'page': i + 1,
                            'data': table
                        })
                
                return ConversionResult(
                    content='\n\n'.join(full_text),
                    pages=pages,
                    content_type="text/plain",
                    metadata=metadata,
                    formatting_preserved=False,
                    tables=tables if tables else None
                )
                
        except Exception as e:
            self.logger.warning(f"Pdfplumber conversion failed: {e}")
            return None
    
    async def _convert_with_pypdf2(self, file_path: Path) -> ConversionResult:
        """Convert using PyPDF2 library."""
        try:
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                
                # Extract text from all pages
                pages = []
                full_text = []
                
                for page_num in range(len(pdf.pages)):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                        full_text.append(text)
                
                # Extract metadata
                metadata = await self.extract_metadata(file_path)
                metadata.page_count = len(pdf.pages)
                
                return ConversionResult(
                    content='\n\n'.join(full_text),
                    pages=pages,
                    content_type="text/plain",
                    metadata=metadata,
                    formatting_preserved=False
                )
                
        except Exception as e:
            self.logger.error(f"PyPDF2 conversion failed: {e}")
            return ConversionResult(
                error=f"PyPDF2 conversion failed: {str(e)}"
            )
    
    async def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            DocumentMetadata
        """
        metadata = self._extract_basic_metadata(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                
                # Extract document info
                if pdf.metadata:
                    info = pdf.metadata
                    
                    if info.title:
                        metadata.title = info.title
                    if info.author:
                        metadata.author = info.author
                    if info.creation_date:
                        metadata.created_date = info.creation_date
                    if info.modification_date:
                        metadata.modified_date = info.modification_date
                    if info.subject:
                        metadata.keywords.append(info.subject)
                
                metadata.page_count = len(pdf.pages)
                
        except Exception as e:
            self.logger.warning(f"Error extracting PDF metadata: {e}")
        
        return metadata