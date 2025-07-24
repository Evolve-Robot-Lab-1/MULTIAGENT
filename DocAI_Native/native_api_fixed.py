"""
Fixed Native API for PyWebView
A working API that PyWebView can properly expose
"""

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Global window reference
_window = None

def set_window(window):
    """Set the window reference"""
    global _window
    _window = window
    logger.info("Window reference set in fixed API")

def pickFile():
    """Native file picker dialog"""
    logger.info("pickFile called (fixed API)")
    
    if not _window:
        logger.error("Window not set")
        return None
    
    try:
        import webview
        file_types = (
            'Document files (*.docx;*.doc;*.odt;*.pdf;*.txt)',
            'All files (*.*)'
        )
        
        result = _window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types
        )
        
        if result and len(result) > 0:
            file_path = result[0]
            logger.info(f"File selected: {file_path}")
            return file_path
        
        logger.info("No file selected")
        return None
        
    except Exception as e:
        logger.error(f"Error in pickFile: {e}", exc_info=True)
        return None

def ping():
    """Simple ping to test API connectivity"""
    logger.info("ping called")
    return {"pong": True, "timestamp": time.time()}

def checkLibreOffice():
    """Check if LibreOffice is available"""
    logger.info("checkLibreOffice called")
    return {
        "available": False,
        "message": "LibreOffice check not implemented yet"
    }

def embedDocument(document_path):
    """Embed document (placeholder)"""
    logger.info(f"embedDocument called for: {document_path}")
    return {
        "success": False,
        "message": "Document embedding not implemented yet"
    }

# Create the API object that PyWebView expects
class FixedAPI:
    """Fixed API class for PyWebView"""
    
    def __init__(self):
        # Expose all module functions as methods
        self.set_window = set_window
        self.pickFile = pickFile
        self.ping = ping
        self.checkLibreOffice = checkLibreOffice
        self.embedDocument = embedDocument
        logger.info("FixedAPI initialized with all methods")