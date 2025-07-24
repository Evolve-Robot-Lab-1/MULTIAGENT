"""
Hybrid Native API Bridge
Combines class functionality with dict-based exposure for PyWebView compatibility
"""

import os
import logging
import time
from pathlib import Path
import webview
import platform

logger = logging.getLogger(__name__)

# Import the class-based API
from native_api_simple import SimpleNativeAPI

# Global instance
_api_instance = None
_window_ref = None

def get_api_instance():
    """Get or create the API instance"""
    global _api_instance
    if _api_instance is None:
        _api_instance = SimpleNativeAPI()
        logger.info("Created SimpleNativeAPI instance for hybrid API")
    return _api_instance

def set_window(window):
    """Set the window reference"""
    global _window_ref
    _window_ref = window
    api = get_api_instance()
    api.set_window(window)
    logger.info("Window reference set in hybrid API")

# Wrapper functions that delegate to the class instance
def pickFile():
    """Native file picker dialog"""
    logger.info("pickFile called (hybrid)")
    api = get_api_instance()
    return api.pickFile()

def pick_file():
    """Snake case version for compatibility"""
    return pickFile()

def pickMultipleFiles():
    """Pick multiple files"""
    logger.info("pickMultipleFiles called (hybrid)")
    api = get_api_instance()
    return api.pickMultipleFiles()

def pickFolder():
    """Native folder picker dialog"""
    logger.info("pickFolder called (hybrid)")
    api = get_api_instance()
    return api.pickFolder()

def saveFile(suggested_name="document.docx"):
    """Native save dialog"""
    logger.info(f"saveFile called (hybrid) with {suggested_name}")
    api = get_api_instance()
    return api.saveFile(suggested_name)

def showMessage(title, message):
    """Show native message box"""
    logger.info("showMessage called (hybrid)")
    api = get_api_instance()
    return api.showMessage(title, message)

def getPlatformInfo():
    """Get platform information"""
    logger.info("getPlatformInfo called (hybrid)")
    api = get_api_instance()
    return api.getPlatformInfo()

def ping():
    """Simple ping to test API connectivity"""
    logger.info("ping called (hybrid)")
    api = get_api_instance()
    return api.ping()

def getAvailableMethods():
    """Return list of available API methods"""
    methods = [
        "pickFile", "pick_file", "pickMultipleFiles", "pickFolder",
        "saveFile", "showMessage", "getPlatformInfo", "ping",
        "getAvailableMethods", "checkLibreOffice", "embedDocument"
    ]
    logger.info(f"Available methods (hybrid): {methods}")
    return methods

def checkLibreOffice():
    """Check if LibreOffice is available for embedding"""
    logger.info("checkLibreOffice called (hybrid)")
    api = get_api_instance()
    return api.checkLibreOffice()

def embedDocument(document_path):
    """Embed document using LibreOffice native viewer"""
    logger.info(f"embedDocument called (hybrid) for: {document_path}")
    api = get_api_instance()
    return api.embedDocument(document_path)

# Create the hybrid API dictionary
hybrid_api = {
    "pickFile": pickFile,
    "pick_file": pick_file,
    "pickMultipleFiles": pickMultipleFiles,
    "pickFolder": pickFolder,
    "saveFile": saveFile,
    "showMessage": showMessage,
    "getPlatformInfo": getPlatformInfo,
    "ping": ping,
    "getAvailableMethods": getAvailableMethods,
    "checkLibreOffice": checkLibreOffice,
    "embedDocument": embedDocument,
    "set_window": set_window
}

# Debug: Verify all methods are callable
logger.info("Hybrid API created with dict-based method exposure")
for name, method in hybrid_api.items():
    if callable(method):
        logger.info(f"✓ {name} is callable")
    else:
        logger.error(f"✗ {name} is NOT callable: {type(method)}")