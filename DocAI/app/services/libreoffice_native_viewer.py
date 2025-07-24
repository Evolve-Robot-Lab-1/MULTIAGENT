"""
LibreOffice Native Viewer Service
Handles native document viewing using LibreOffice headless mode
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LibreOfficeNativeViewer:
    """Service for native document viewing using LibreOffice"""
    
    def __init__(self, libreoffice_path: str = '/usr/bin/libreoffice'):
        """
        Initialize the LibreOffice Native Viewer
        
        Args:
            libreoffice_path: Path to LibreOffice executable
        """
        self.libreoffice_path = libreoffice_path
        self.temp_dir = tempfile.mkdtemp(prefix='libreoffice_native_')
        logger.info(f"LibreOffice Native Viewer initialized with temp dir: {self.temp_dir}")
        
        # Check if LibreOffice is available
        self.available = self._check_libreoffice_available()
    
    def _check_libreoffice_available(self) -> bool:
        """Check if LibreOffice is installed and available"""
        try:
            result = subprocess.run(
                [self.libreoffice_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"LibreOffice found: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"LibreOffice not found or error: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error checking LibreOffice availability: {str(e)}")
            return False
    
    def convert_to_pdf(self, input_file: str) -> Optional[str]:
        """
        Convert document to PDF for native viewing
        
        Args:
            input_file: Path to input document
            
        Returns:
            Path to converted PDF file or None if conversion failed
        """
        if not self.available:
            logger.error("LibreOffice not available for conversion")
            return None
            
        try:
            # Ensure input file exists
            if not os.path.exists(input_file):
                logger.error(f"Input file not found: {input_file}")
                return None
            
            # Prepare conversion command
            cmd = [
                self.libreoffice_path,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', self.temp_dir,
                input_file
            ]
            
            logger.info(f"Running conversion command: {' '.join(cmd)}")
            
            # Execute conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Conversion failed: {result.stderr}")
                return None
            
            # Find the output PDF
            input_name = Path(input_file).stem
            pdf_path = os.path.join(self.temp_dir, f"{input_name}.pdf")
            
            if os.path.exists(pdf_path):
                logger.info(f"Successfully converted to PDF: {pdf_path}")
                return pdf_path
            else:
                logger.error(f"PDF output not found at expected path: {pdf_path}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Document conversion timed out")
            return None
        except Exception as e:
            logger.error(f"PDF conversion error: {str(e)}")
            return None
    
    def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a document
        
        Args:
            file_path: Path to document
            
        Returns:
            Dictionary with document information
        """
        info = {
            'filename': os.path.basename(file_path),
            'size': 0,
            'format': Path(file_path).suffix.lower(),
            'native_viewer_compatible': False
        }
        
        try:
            if os.path.exists(file_path):
                info['size'] = os.path.getsize(file_path)
                
                # Check if format is compatible with native viewer
                compatible_formats = ['.doc', '.docx', '.odt', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx']
                info['native_viewer_compatible'] = info['format'] in compatible_formats
                
        except Exception as e:
            logger.error(f"Error getting document info: {str(e)}")
            
        return info
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {str(e)}")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()