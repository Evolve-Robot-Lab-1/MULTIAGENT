"""
Simple Native API Bridge
Minimal API to avoid pywebview introspection issues
"""

import os
import logging
import time
from pathlib import Path
import webview
import platform

logger = logging.getLogger(__name__)

class SimpleNativeAPI:
    """Simplified API exposed to JavaScript frontend"""
    
    def __init__(self):
        self.window = None
        logger.info("SimpleNativeAPI initialized (v1.7 with camelCase methods)")
        # Log available methods on init
        methods = [m for m in dir(self) if not m.startswith('_') and callable(getattr(self, m, None))]
        logger.info(f"Available API methods: {methods}")
    
    def set_window(self, window):
        """Set the webview window reference"""
        self.window = window
        logger.info("Window reference set in SimpleNativeAPI")
    
    # File Operations
    def pick_file(self):
        """Native file picker dialog"""
        try:
            logger.info("pick_file called")
            
            if not self.window:
                logger.error("Window not set")
                return None
                
            file_types = (
                'Document files (*.docx;*.doc;*.odt;*.pdf;*.txt)',
                'All files (*.*)'
            )
            
            result = self.window.create_file_dialog(
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
            logger.error(f"Error in pick_file: {e}", exc_info=True)
            return None
    
    def pick_multiple_files(self):
        """Pick multiple files"""
        try:
            logger.info("pick_multiple_files called")
            
            if not self.window:
                logger.error("Window not set")
                return []
                
            file_types = (
                'Document files (*.docx;*.doc;*.odt;*.pdf;*.txt)',
                'All files (*.*)'
            )
            
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=file_types
            )
            
            if result:
                file_paths = [str(Path(f).resolve()) for f in result]
                logger.info(f"Multiple files selected: {len(file_paths)} files")
                return file_paths
            
            return []
            
        except Exception as e:
            logger.error(f"Error in pick_multiple_files: {e}", exc_info=True)
            return []
    
    def pick_folder(self):
        """Native folder picker dialog"""
        try:
            logger.info("pick_folder called")
            
            if not self.window:
                logger.error("Window not set")
                return None
                
            result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
            
            if result and len(result) > 0:
                folder_path = str(Path(result[0]).resolve())
                logger.info(f"Folder selected: {folder_path}")
                return folder_path
            
            logger.info("No folder selected")
            return None
            
        except Exception as e:
            logger.error(f"Error in pick_folder: {e}", exc_info=True)
            return None
    
    def save_file(self, suggested_name="document.docx"):
        """Native save dialog"""
        try:
            logger.info(f"save_file called with suggested_name: {suggested_name}")
            
            if not self.window:
                logger.error("Window not set")
                return None
                
            result = self.window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested_name
            )
            
            if result:
                save_path = str(Path(result).resolve())
                logger.info(f"Save location selected: {save_path}")
                return save_path
            
            logger.info("Save cancelled")
            return None
            
        except Exception as e:
            logger.error(f"Error in save_file: {e}", exc_info=True)
            return None
    
    def show_message(self, title, message):
        """Show native message box"""
        try:
            logger.info(f"show_message called: {title}")
            
            if not self.window:
                logger.error("Window not set")
                return False
                
            self.window.create_confirmation_dialog(title, message)
            return True
            
        except Exception as e:
            logger.error(f"Error showing message: {e}", exc_info=True)
            return False
    
    def get_platform_info(self):
        """Get platform information"""
        try:
            return {
                "system": platform.system(),
                "version": platform.version(),
                "machine": platform.machine(),
                "python_version": platform.python_version()
            }
        except Exception as e:
            logger.error(f"Error getting platform info: {e}", exc_info=True)
            return {"error": str(e)}
    
    def ping(self):
        """Simple ping to test API connectivity"""
        logger.info("ping called")
        return {"pong": True, "timestamp": time.time()}
    
    def log_message(self, level, message):
        """Log message from frontend"""
        try:
            getattr(logger, level.lower())(f"Frontend: {message}")
            return True
        except Exception as e:
            logger.error(f"Error logging message: {e}", exc_info=True)
            return False
    
    # CamelCase wrapper methods for PyWebView compatibility
    def pickFile(self):
        """Camel case version for PyWebView compatibility"""
        logger.info("pickFile called (camelCase wrapper)")
        return self.pick_file()
    
    def pickMultipleFiles(self):
        """Camel case version for PyWebView compatibility"""
        logger.info("pickMultipleFiles called (camelCase wrapper)")
        return self.pick_multiple_files()
    
    def pickFolder(self):
        """Camel case version for PyWebView compatibility"""
        logger.info("pickFolder called (camelCase wrapper)")
        return self.pick_folder()
    
    def saveFile(self, suggested_name="document.docx"):
        """Camel case version for PyWebView compatibility"""
        logger.info(f"saveFile called with {suggested_name} (camelCase wrapper)")
        return self.save_file(suggested_name)
    
    def showMessage(self, title, message):
        """Camel case version for PyWebView compatibility"""
        logger.info("showMessage called (camelCase wrapper)")
        return self.show_message(title, message)
    
    def getPlatformInfo(self):
        """Camel case version for PyWebView compatibility"""
        logger.info("getPlatformInfo called (camelCase wrapper)")
        return self.get_platform_info()
    
    def logMessage(self, level, message):
        """Camel case version for PyWebView compatibility"""
        return self.log_message(level, message)
    
    def getAvailableMethods(self):
        """Return list of available API methods for debugging"""
        methods = []
        for method in dir(self):
            if not method.startswith('_') and callable(getattr(self, method)):
                methods.append(method)
        logger.info(f"Available API methods: {methods}")
        return methods
    
    # LibreOffice Integration Methods
    def checkLibreOffice(self):
        """Check if LibreOffice is available for embedding"""
        logger.info("checkLibreOffice called")
        
        try:
            from app.services.document_embedder import get_document_embedder
            embedder = get_document_embedder()
            available = embedder.can_embed()
            
            result = {
                "available": available,
                "platform": platform.system(),
                "embedder": embedder.__class__.__name__
            }
            logger.info(f"LibreOffice check result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking LibreOffice: {e}", exc_info=True)
            return {
                "available": False,
                "error": str(e)
            }
    
    def embedDocument(self, document_path):
        """Embed document using LibreOffice native viewer"""
        logger.info(f"embedDocument called for: {document_path}")
        
        try:
            if not self.window:
                logger.error("Window not set for document embedding")
                return {"success": False, "error": "Window reference not set"}
            
            from app.services.document_embedder import get_document_embedder
            embedder = get_document_embedder()
            result = embedder.embed_document(self.window, document_path)
            
            logger.info(f"Document embedding result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error embedding document: {e}", exc_info=True)
            return {"success": False, "error": str(e)}