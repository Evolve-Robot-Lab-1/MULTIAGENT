"""
Dictionary-based Native API for PyWebView
PyWebView sometimes has issues with class-based APIs, so this uses a simple dict approach
"""

import os
import logging
import time
from pathlib import Path
import webview

logger = logging.getLogger(__name__)

# Global window reference
_window_ref = None

def set_window(window):
    """Set the window reference"""
    global _window_ref
    _window_ref = window
    logger.info("Window reference set in dict API")

def pickFile():
    """Native file picker dialog"""
    logger.info("pickFile called from dict API")
    
    if not _window_ref:
        logger.error("Window not set")
        return None
        
    file_types = (
        'Document files (*.docx;*.doc;*.odt;*.pdf;*.txt)',
        'All files (*.*)'
    )
    
    try:
        result = _window_ref.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types
        )
        
        if result and len(result) > 0:
            file_path = str(Path(result[0]).resolve())
            logger.info(f"File selected: {file_path}")
            return file_path
        
        logger.info("No file selected")
        return None
        
    except Exception as e:
        logger.error(f"Error in pickFile: {e}", exc_info=True)
        return None

def pick_file():
    """Snake case version for compatibility"""
    return pickFile()

def getAvailableMethods():
    """Return list of available methods"""
    return ["pickFile", "pick_file", "getAvailableMethods", "embedDocument", "checkLibreOffice"]

def embedDocument(document_path):
    """Embed document using LibreOffice native viewer"""
    logger.info(f"embedDocument called for: {document_path}")
    
    try:
        # Import here to avoid circular dependencies
        from app.services.document_embedder import get_document_embedder
        
        if not _window_ref:
            logger.error("Window not set for document embedding")
            return {"success": False, "error": "Window reference not set"}
        
        embedder = get_document_embedder()
        result = embedder.embed_document(_window_ref, document_path)
        
        logger.info(f"Document embedding result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error embedding document: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

def checkLibreOffice():
    """Check if LibreOffice is available for embedding"""
    logger.info("Checking LibreOffice availability")
    
    try:
        from app.services.document_embedder import get_document_embedder
        embedder = get_document_embedder()
        available = embedder.can_embed()
        
        return {
            "available": available,
            "platform": os.name,
            "embedder": embedder.__class__.__name__
        }
        
    except Exception as e:
        logger.error(f"Error checking LibreOffice: {e}")
        return {
            "available": False,
            "error": str(e)
        }

# Create the API dictionary
api_dict = {
    "pickFile": pickFile,
    "pick_file": pick_file,
    "getAvailableMethods": getAvailableMethods,
    "set_window": set_window,
    "embedDocument": embedDocument,
    "checkLibreOffice": checkLibreOffice
}

logger.info(f"Dict API created with methods: {list(api_dict.keys())}")