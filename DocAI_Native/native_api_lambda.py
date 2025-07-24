"""
Lambda-based Native API for PyWebView
Using simple lambdas for better compatibility
"""

import os
import logging
import time
from pathlib import Path
import platform

# Import webview only if available (for module testing)
try:
    import webview
except ImportError:
    webview = None

logger = logging.getLogger(__name__)

# Import the class-based API for functionality
from native_api_simple import SimpleNativeAPI

# Global instance and window ref
_api_instance = None
_window_ref = None

def get_api():
    """Get or create the API instance"""
    global _api_instance
    if _api_instance is None:
        _api_instance = SimpleNativeAPI()
    return _api_instance

def set_window_ref(window):
    """Set window reference"""
    global _window_ref
    _window_ref = window
    get_api().set_window(window)

# Create lambda-based API dict for PyWebView
lambda_api = {
    # File operations
    "pickFile": lambda: get_api().pickFile(),
    "pickMultipleFiles": lambda: get_api().pickMultipleFiles(),
    "pickFolder": lambda: get_api().pickFolder(),
    "saveFile": lambda suggested_name="document.docx": get_api().saveFile(suggested_name),
    
    # System operations
    "showMessage": lambda title, message: get_api().showMessage(title, message),
    "getPlatformInfo": lambda: get_api().getPlatformInfo(),
    
    # Test operations
    "ping": lambda: get_api().ping(),
    "getAvailableMethods": lambda: [
        "pickFile", "pickMultipleFiles", "pickFolder", "saveFile",
        "showMessage", "getPlatformInfo", "ping", "getAvailableMethods",
        "checkLibreOffice", "embedDocument"
    ],
    
    # LibreOffice operations
    "checkLibreOffice": lambda: get_api().checkLibreOffice(),
    "embedDocument": lambda document_path: get_api().embedDocument(document_path),
    
    # Window management
    "set_window": lambda window: set_window_ref(window)
}

# Log API creation
logger.info("Lambda-based API created")
for name in lambda_api:
    logger.info(f"  {name}: lambda function")