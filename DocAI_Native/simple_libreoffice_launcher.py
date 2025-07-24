#!/usr/bin/env python3
"""
Simple LibreOffice Launcher for DocAI Native
Adds "Open in LibreOffice" functionality
"""

import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LibreOfficeLauncher:
    """Simple launcher for opening documents in LibreOffice"""
    
    @staticmethod
    def check_libreoffice():
        """Check if LibreOffice is installed"""
        try:
            result = subprocess.run(['which', 'soffice'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def open_document(file_path, mode='view'):
        """
        Open document in LibreOffice
        
        Args:
            file_path: Path to the document
            mode: 'view' for read-only, 'edit' for editing
        
        Returns:
            dict with success status and message
        """
        try:
            if not LibreOfficeLauncher.check_libreoffice():
                return {
                    "success": False,
                    "error": "LibreOffice not installed"
                }
            
            # Ensure file exists
            file_path = Path(file_path)
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            # Build command
            cmd = [
                'soffice',
                '--nologo',
                '--norestore'
            ]
            
            if mode == 'view':
                cmd.append('--view')
            
            cmd.append(str(file_path.absolute()))
            
            # Launch LibreOffice
            process = subprocess.Popen(cmd)
            logger.info(f"Launched LibreOffice for {file_path.name} (PID: {process.pid})")
            
            return {
                "success": True,
                "message": f"Opened in LibreOffice ({mode} mode)",
                "pid": process.pid
            }
            
        except Exception as e:
            logger.error(f"Error launching LibreOffice: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_supported_formats():
        """Get list of formats that can be opened in LibreOffice"""
        return [
            '.odt', '.ods', '.odp', '.odg',  # OpenDocument
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Microsoft
            '.rtf', '.txt', '.csv',  # Text formats
            '.pdf'  # PDF (view only)
        ]


# Example usage for integration into DocAI Native
def add_to_docai_native_api():
    """
    Add this to your native API class in DocAI Native:
    """
    
    def open_in_libreoffice(self, file_path, mode='view'):
        """Open document in external LibreOffice window"""
        return LibreOfficeLauncher.open_document(file_path, mode)
    
    # Add to your HTML/JavaScript:
    """
    <button onclick="openInLibreOffice()">Open in LibreOffice</button>
    
    <script>
    async function openInLibreOffice() {
        const currentFile = getCurrentFileName(); // Your method to get current file
        const result = await pywebview.api.open_in_libreoffice(currentFile, 'view');
        
        if (result.success) {
            showNotification(result.message);
        } else {
            showError(result.error);
        }
    }
    </script>
    """


if __name__ == '__main__':
    # Test the launcher
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = LibreOfficeLauncher.open_document(file_path)
        print(f"Result: {result}")
    else:
        print("Usage: python simple_libreoffice_launcher.py <file_path>")
        print(f"Supported formats: {', '.join(LibreOfficeLauncher.get_supported_formats())}")
        print(f"LibreOffice installed: {LibreOfficeLauncher.check_libreoffice()}")