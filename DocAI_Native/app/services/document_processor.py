"""
Document Processor Service
Handles document processing with clean separation of concerns
"""

import logging
from pathlib import Path
from typing import Dict, Any

from config import CFG
from .interfaces import IDocumentProcessor

logger = logging.getLogger(__name__)

class DocumentProcessor(IDocumentProcessor):
    """Main document processor implementation"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("Document processor initialized")
    
    def get_supported_formats(self) -> set:
        """Get supported file extensions"""
        return CFG.ALLOWED_EXTENSIONS
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate file before processing"""
        try:
            # Check existence
            if not file_path.exists():
                return {
                    'valid': False,
                    'error': 'File not found',
                    'code': 'FILE_NOT_FOUND'
                }
            
            # Check if it's a file
            if not file_path.is_file():
                return {
                    'valid': False,
                    'error': 'Path is not a file',
                    'code': 'NOT_A_FILE'
                }
            
            # Check size
            size = file_path.stat().st_size
            if size > CFG.MAX_FILE_SIZE:
                return {
                    'valid': False,
                    'error': f'File too large: {size} bytes (max: {CFG.MAX_FILE_SIZE})',
                    'code': 'FILE_TOO_LARGE',
                    'size': size,
                    'max_size': CFG.MAX_FILE_SIZE
                }
            
            # Check extension
            extension = file_path.suffix.lower()
            if extension not in self.get_supported_formats():
                return {
                    'valid': False,
                    'error': f'Unsupported file type: {extension}',
                    'code': 'UNSUPPORTED_FORMAT',
                    'extension': extension,
                    'supported': list(self.get_supported_formats())
                }
            
            # All checks passed
            return {
                'valid': True,
                'size': size,
                'extension': extension,
                'name': file_path.name
            }
            
        except Exception as e:
            self.logger.exception(f"Error validating file {file_path}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}',
                'code': 'VALIDATION_ERROR'
            }
    
    def process_native(self, file_path: Path) -> Dict[str, Any]:
        """Process document for native viewing"""
        try:
            self.logger.info(f"Processing document for native view: {file_path}")
            
            # Validate file first
            validation = self.validate_file(file_path)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error'],
                    'code': validation['code']
                }
            
            extension = file_path.suffix.lower()
            
            if extension in ['.doc', '.docx', '.odt']:
                return self._process_office_document(file_path, 'native')
            elif extension == '.pdf':
                return self._process_pdf_document(file_path, 'native')
            elif extension == '.txt':
                return self._process_text_document(file_path, 'native')
            else:
                return {
                    'success': False,
                    'error': f'No native processor for {extension}',
                    'code': 'NO_NATIVE_PROCESSOR'
                }
                
        except Exception as e:
            self.logger.exception(f"Error processing document natively: {file_path}")
            return {
                'success': False,
                'error': str(e),
                'code': 'PROCESSING_ERROR'
            }
    
    def process_html(self, file_path: Path) -> Dict[str, Any]:
        """Process document for HTML viewing"""
        try:
            self.logger.info(f"Processing document for HTML view: {file_path}")
            
            # Validate file first
            validation = self.validate_file(file_path)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error'],
                    'code': validation['code']
                }
            
            extension = file_path.suffix.lower()
            
            if extension in ['.doc', '.docx', '.odt']:
                return self._process_office_document(file_path, 'html')
            elif extension == '.pdf':
                return self._process_pdf_document(file_path, 'html')
            elif extension == '.txt':
                return self._process_text_document(file_path, 'html')
            else:
                return {
                    'success': False,
                    'error': f'No HTML processor for {extension}',
                    'code': 'NO_HTML_PROCESSOR'
                }
                
        except Exception as e:
            self.logger.exception(f"Error processing document for HTML: {file_path}")
            return {
                'success': False,
                'error': str(e),
                'code': 'PROCESSING_ERROR'
            }
    
    def _process_office_document(self, file_path: Path, mode: str) -> Dict[str, Any]:
        """Process Office documents (DOC, DOCX, ODT)"""
        try:
            result = {
                'success': True,
                'type': 'office',
                'format': file_path.suffix.lower(),
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'mode': mode
            }
            
            if mode == 'native':
                result.update({
                    'requires_libreoffice': True,
                    'embedding_available': True,
                    'message': 'Document ready for LibreOffice native viewing'
                })
            else:  # HTML mode
                # TODO: Integrate with existing DocAI HTML conversion
                result.update({
                    'content': '<p>HTML conversion would go here</p>',
                    'pages': ['<p>Page 1 content</p>'],
                    'total_pages': 1,
                    'message': 'Document converted to HTML (placeholder)'
                })
            
            self.logger.info(f"Office document processed: {file_path.name} in {mode} mode")
            return result
            
        except Exception as e:
            self.logger.exception(f"Error processing office document: {file_path}")
            return {
                'success': False,
                'error': str(e),
                'code': 'OFFICE_PROCESSING_ERROR'
            }
    
    def _process_pdf_document(self, file_path: Path, mode: str) -> Dict[str, Any]:
        """Process PDF documents"""
        try:
            result = {
                'success': True,
                'type': 'pdf',
                'format': '.pdf',
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'mode': mode
            }
            
            if mode == 'native':
                result.update({
                    'direct_view': True,
                    'message': 'PDF ready for direct viewing'
                })
            else:  # HTML mode
                result.update({
                    'content': '<embed src="' + str(file_path) + '" type="application/pdf">',
                    'message': 'PDF embedded in HTML'
                })
            
            self.logger.info(f"PDF document processed: {file_path.name} in {mode} mode")
            return result
            
        except Exception as e:
            self.logger.exception(f"Error processing PDF: {file_path}")
            return {
                'success': False,
                'error': str(e),
                'code': 'PDF_PROCESSING_ERROR'
            }
    
    def _process_text_document(self, file_path: Path, mode: str) -> Dict[str, Any]:
        """Process text documents"""
        try:
            # Read text content
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            result = {
                'success': True,
                'type': 'text',
                'format': '.txt',
                'path': str(file_path),
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'mode': mode,
                'content': content,
                'lines': len(content.splitlines()),
                'chars': len(content)
            }
            
            if mode == 'html':
                # Convert to HTML format
                html_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_content = html_content.replace('\n', '<br>')
                result['html_content'] = f'<pre>{html_content}</pre>'
            
            self.logger.info(f"Text document processed: {file_path.name} ({len(content)} chars)")
            return result
            
        except UnicodeDecodeError as e:
            self.logger.error(f"Text encoding error: {file_path} - {e}")
            return {
                'success': False,
                'error': 'Text file encoding not supported',
                'code': 'ENCODING_ERROR'
            }
        except Exception as e:
            self.logger.exception(f"Error processing text document: {file_path}")
            return {
                'success': False,
                'error': str(e),
                'code': 'TEXT_PROCESSING_ERROR'
            }

# Factory function for dependency injection
def create_document_processor() -> IDocumentProcessor:
    """Create document processor instance"""
    return DocumentProcessor()