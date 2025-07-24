"""
Native API Bridge
Exposes native functionality to JavaScript frontend
"""

import os
import logging
import time
from pathlib import Path
import webview
import platform

from config import CFG
from app.api.overlay_api import OverlayAPI

logger = logging.getLogger(__name__)

class NativeAPI:
    """API exposed to JavaScript frontend"""
    
    def __init__(self, uno_bridge, startup_file=None):
        # Store uno_bridge as private to avoid pywebview introspection issues
        self._uno_bridge = uno_bridge
        self.window = None
        self.startup_file = startup_file
        self._platform_info = None  # Cache platform info
        
        # Initialize overlay API
        self.overlay = OverlayAPI()
        
        logger.info(f"Native API initialized with startup_file: {startup_file}")
    
    def set_window(self, window):
        """Set the webview window reference"""
        self.window = window
        logger.info("Window reference set in Native API")
    
    # File Operations
    def pick_file(self):
        """Native file picker dialog"""
        try:
            file_types = (
                'Document files (*.docx;*.doc;*.odt;*.pdf;*.txt)',
                'Word documents (*.docx;*.doc)',
                'PDF files (*.pdf)',
                'Text files (*.txt)',
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
            logger.error(f"Error in pick_file: {e}")
            return None
    
    def pick_multiple_files(self):
        """Pick multiple files"""
        try:
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
            logger.error(f"Error in pick_multiple_files: {e}")
            return []
    
    def open_file(self, file_path):
        """Open a specific file programmatically"""
        try:
            if not file_path:
                logger.error("No file path provided to open_file")
                return False
                
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File does not exist: {file_path}")
                return False
                
            logger.info(f"Opening file programmatically: {file_path}")
            
            # TODO: Integrate with frontend to display the file
            # For now, just log the action
            return True
            
        except Exception as e:
            logger.error(f"Error in open_file: {e}")
            return False
    
    def pick_folder(self):
        """Native folder picker dialog"""
        try:
            result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
            if result and len(result) > 0:
                folder_path = str(Path(result[0]).resolve())
                logger.info(f"Folder selected: {folder_path}")
                return folder_path
            
            logger.info("No folder selected")
            return None
            
        except Exception as e:
            logger.error(f"Error in pick_folder: {e}")
            return None
    
    def save_file(self, suggested_name="document.docx"):
        """Native save dialog"""
        try:
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
            logger.error(f"Error in save_file: {e}")
            return None
    
    # File System Operations
    def get_file_info(self, file_path):
        """Get file information"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": "File not found"}
            
            stat = path.stat()
            return {
                "name": path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": path.suffix,
                "is_file": path.is_file(),
                "is_dir": path.is_dir()
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {"error": str(e)}
    
    def check_file_exists(self, file_path):
        """Check if file exists"""
        try:
            return Path(file_path).exists()
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False
    
    # LibreOffice Integration
    def embed_libreoffice(self, container_id, file_path):
        """Embed LibreOffice in container"""
        try:
            if not self._uno_bridge:
                logger.warning("UNO bridge not available")
                return {"error": "LibreOffice integration not available"}
            
            logger.info(f"Embedding LibreOffice for file: {file_path}")
            result = self._uno_bridge.embed_document(file_path, container_id)
            logger.info(f"Embed result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error embedding LibreOffice: {e}")
            return {"error": str(e)}
    
    def start_libreoffice_server(self):
        """Start LibreOffice UNO server"""
        try:
            if not self._uno_bridge:
                logger.warning("UNO bridge not available")
                return {"error": "LibreOffice integration not available"}
            
            result = self._uno_bridge.start_libreoffice_server()
            logger.info(f"LibreOffice server start result: {result}")
            return {"success": result}
        except Exception as e:
            logger.error(f"Error starting LibreOffice server: {e}")
            return {"error": str(e)}
    
    # System Integration
    def show_message(self, title, message, type="info"):
        """Show native message box"""
        try:
            if type == "info":
                self.window.create_confirmation_dialog(title, message)
            elif type == "error":
                # Use system notification for errors
                logger.error(f"{title}: {message}")
            elif type == "warning":
                logger.warning(f"{title}: {message}")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error showing message: {e}")
            return {"error": str(e)}
    
    def show_notification(self, title, message):
        """Show system notification"""
        try:
            # This would require additional dependencies for cross-platform notifications
            logger.info(f"Notification: {title} - {message}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
            return {"error": str(e)}
    
    # Platform Information
    def get_platform_info(self):
        """Get platform information"""
        try:
            return {
                "system": platform.system(),
                "version": platform.version(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
                "app_version": CFG.VERSION
            }
        except Exception as e:
            logger.error(f"Error getting platform info: {e}")
            return {"error": str(e)}
    
    def get_app_info(self):
        """Get application information"""
        return {
            "name": CFG.APP_NAME,
            "version": CFG.VERSION,
            "debug": CFG.DEBUG,
            "paths": {
                "documents": str(CFG.DOCUMENTS_DIR),
                "cache": str(CFG.CACHE_DIR),
                "config": str(CFG.CONFIG_DIR)
            },
            "features": {
                "native_libreoffice": True,
                "overlay_positioning": True
            }
        }
    
    def get_window_info(self):
        """Get current window position and size"""
        try:
            if self.window:
                # Get window bounds
                return {
                    "x": self.window.x if hasattr(self.window, 'x') else 100,
                    "y": self.window.y if hasattr(self.window, 'y') else 100,
                    "width": self.window.width if hasattr(self.window, 'width') else 1200,
                    "height": self.window.height if hasattr(self.window, 'height') else 800
                }
            return {"x": 100, "y": 100, "width": 1200, "height": 800}
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return {"x": 100, "y": 100, "width": 1200, "height": 800}
    
    # Configuration
    def get_config(self, key=None):
        """Get configuration value(s)"""
        try:
            if key:
                return getattr(CFG, key, None)
            else:
                # Return safe config values (no secrets)
                return {
                    "app_name": CFG.APP_NAME,
                    "version": CFG.VERSION,
                    "debug": CFG.DEBUG,
                    "window_width": CFG.WINDOW_WIDTH,
                    "window_height": CFG.WINDOW_HEIGHT
                }
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return None
    
    def set_config(self, key, value):
        """Set configuration value"""
        try:
            # Only allow certain config changes
            allowed_keys = {
                'WINDOW_WIDTH', 'WINDOW_HEIGHT', 'DEBUG'
            }
            
            if key in allowed_keys:
                setattr(CFG, key, value)
                logger.info(f"Config updated: {key} = {value}")
                return {"success": True}
            else:
                return {"error": f"Config key '{key}' is not modifiable"}
                
        except Exception as e:
            logger.error(f"Error setting config: {e}")
            return {"error": str(e)}
    
    # Utility Methods
    def log_message(self, level, message):
        """Log message from frontend"""
        try:
            getattr(logger, level.lower())(f"Frontend: {message}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Error logging message: {e}")
            return {"error": str(e)}
    
    def ping(self):
        """Simple ping to test API connectivity"""
        return {"pong": True, "timestamp": time.time()}
    
    # Shutdown
    def shutdown(self):
        """Graceful shutdown"""
        try:
            logger.info("Shutdown requested from frontend")
            
            # Stop overlay if running
            if self.overlay:
                self.overlay.stop_overlay()
                
            if self._uno_bridge:
                self._uno_bridge.shutdown()
            # The window closing will trigger the main shutdown sequence
            if self.window:
                self.window.destroy()
            return {"success": True}
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return {"error": str(e)}