"""
Native API Bridge - Unified API for PyWebView
Combines file operations and overlay functionality
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NativeAPIBridge:
    """
    Bridge pattern to expose all native functionality through a clean API.
    This solves the PyWebView compatibility issues while maintaining modularity.
    """
    
    def __init__(self):
        # Import here to avoid circular imports
        from native_api_fixed import FixedAPI
        
        # Core functionality that we know works
        self._file_api = FixedAPI()
        self._overlay_api = None  # Lazy initialization
        self._window = None
        
        # Feature flags for progressive rollout
        self._features = {
            'overlay_enabled': True,
            'native_viewer': True,
            'debug_mode': True
        }
        
        logger.info("NativeAPIBridge initialized")
        
    def set_window(self, window):
        """Set PyWebView window reference"""
        self._window = window
        self._file_api.set_window(window)
        logger.info("Window reference set in bridge")
        
    # File operations (delegate to FixedAPI)
    def pickFile(self):
        """Native file picker - delegated to FixedAPI"""
        return self._file_api.pickFile()
        
    def ping(self):
        """API connectivity test"""
        return self._file_api.ping()
        
    def checkLibreOffice(self):
        """Check LibreOffice availability"""
        return self._file_api.checkLibreOffice()
        
    def embedDocument(self, document_path):
        """Legacy embed document method"""
        return self._file_api.embedDocument(document_path)
        
    # Overlay operations (lazy loaded)
    def _ensure_overlay(self):
        """Lazy initialize overlay API"""
        if not self._overlay_api and self._features['overlay_enabled']:
            try:
                from app.api.overlay_api import OverlayAPI
                self._overlay_api = OverlayAPI()
                logger.info("Overlay API initialized")
            except Exception as e:
                logger.error(f"Failed to initialize overlay: {e}")
                self._features['overlay_enabled'] = False
                
    def initializeOverlay(self, documents_dir: str) -> Dict[str, Any]:
        """Initialize overlay system"""
        self._ensure_overlay()
        if self._overlay_api:
            return self._overlay_api.initialize(documents_dir)
        return {"success": False, "error": "Overlay not available"}
        
    def loadDocumentOverlay(self, filename: str, bounds: Dict[str, Any]) -> Dict[str, Any]:
        """Load document with overlay positioning"""
        self._ensure_overlay()
        if self._overlay_api:
            return self._overlay_api.load_document_overlay(filename, bounds)
        return {"success": False, "error": "Overlay not available"}
        
    def updateContainerBounds(self, bounds: Dict[str, Any]) -> Dict[str, Any]:
        """Update overlay container bounds"""
        self._ensure_overlay()
        if self._overlay_api:
            return self._overlay_api.update_container_bounds(bounds)
        return {"success": False, "error": "Overlay not available"}
        
    def stopOverlay(self) -> Dict[str, Any]:
        """Stop overlay and close LibreOffice"""
        if self._overlay_api:
            return self._overlay_api.stop_overlay()
        return {"success": True}  # Nothing to stop
        
    def getOverlayStatus(self) -> Dict[str, Any]:
        """Get overlay system status"""
        self._ensure_overlay()
        if self._overlay_api:
            return self._overlay_api.get_overlay_status()
        return {"success": False, "available": False}
        
    def updateWindowPosition(self, x: int, y: int) -> Dict[str, Any]:
        """Update window position for overlay tracking"""
        if self._overlay_api:
            return self._overlay_api.update_window_position(x, y)
        return {"success": False, "error": "Overlay not available"}
        
    def configureSyncEngine(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Configure overlay sync engine"""
        if self._overlay_api:
            return self._overlay_api.configure_sync_engine(settings)
        return {"success": False, "error": "Overlay not available"}
        
    def getSyncMetrics(self) -> Dict[str, Any]:
        """Get overlay sync metrics"""
        if self._overlay_api:
            return self._overlay_api.get_sync_metrics()
        return {"success": False, "error": "Overlay not available"}
        
    # Feature detection for frontend
    def getFeatures(self) -> Dict[str, Any]:
        """Get available features for frontend"""
        return {
            "success": True,
            "features": {
                "file_picker": True,
                "overlay_viewer": self._features['overlay_enabled'],
                "native_viewer": self._features['native_viewer'],
                "debug_mode": self._features['debug_mode']
            }
        }
        
    def setFeature(self, feature: str, enabled: bool) -> Dict[str, Any]:
        """Enable/disable features at runtime"""
        if feature in self._features:
            self._features[feature] = enabled
            logger.info(f"Feature '{feature}' set to {enabled}")
            return {"success": True}
        return {"success": False, "error": f"Unknown feature: {feature}"}