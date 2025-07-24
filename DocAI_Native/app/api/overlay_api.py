"""
PyWebView API for LibreOffice Overlay System

This module provides the JavaScript-accessible API for controlling
the LibreOffice overlay positioning system.
"""

import logging
import os
from typing import Dict, Any, Optional

from app.services.overlay import LibreOfficeOverlayManager

logger = logging.getLogger(__name__)


class OverlayAPI:
    """
    PyWebView API for LibreOffice overlay control.
    
    This class follows the PyWebView pattern and provides methods
    that can be called from JavaScript.
    """
    
    def __init__(self):
        """Initialize overlay API."""
        self.overlay_manager = LibreOfficeOverlayManager()
        self._documents_dir = None
        
        # Set callbacks
        self.overlay_manager.set_callbacks(
            state_callback=self._on_state_change,
            error_callback=self._on_error
        )
        
        # State tracking for JS
        self._current_state = "idle"
        self._last_error = None
        
    def initialize(self, documents_dir: str) -> Dict[str, Any]:
        """
        Initialize overlay system.
        
        Args:
            documents_dir: Path to documents directory
            
        Returns:
            Initialization status
        """
        try:
            self._documents_dir = documents_dir
            logger.info(f"Overlay API initialized with documents dir: {documents_dir}")
            
            return {
                "success": True,
                "platform": self.overlay_manager.platform,
                "features": {
                    "decorations_removal": True,
                    "always_on_top": True,
                    "position_sync": True,
                    "smoothing": True,
                    "prediction": True
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize overlay API: {e}")
            return {"success": False, "error": str(e)}
            
    def load_document_overlay(self, filename: str, container_bounds: Dict[str, float]) -> Dict[str, Any]:
        """
        Load document with overlay positioning.
        
        Args:
            filename: Document filename
            container_bounds: Container element bounds (x, y, width, height)
            
        Returns:
            Load status
        """
        try:
            # Build full path
            if self._documents_dir:
                file_path = os.path.join(self._documents_dir, filename)
            else:
                file_path = filename
                
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"Document not found: {filename}"
                }
                
            # Load document
            success = self.overlay_manager.load_document(file_path, container_bounds)
            
            return {
                "success": success,
                "state": self._current_state,
                "error": self._last_error if not success else None
            }
            
        except Exception as e:
            logger.error(f"Failed to load document overlay: {e}")
            return {"success": False, "error": str(e)}
            
    def update_container_bounds(self, bounds: Dict[str, float]) -> Dict[str, Any]:
        """
        Update container bounds for repositioning.
        
        Args:
            bounds: New container bounds
            
        Returns:
            Update status
        """
        try:
            self.overlay_manager.update_container_bounds(bounds)
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to update bounds: {e}")
            return {"success": False, "error": str(e)}
            
    def update_window_position(self, x: int, y: int) -> Dict[str, Any]:
        """
        Update PyWebView window position.
        
        Args:
            x: Window X coordinate
            y: Window Y coordinate
            
        Returns:
            Update status
        """
        try:
            self.overlay_manager.update_window_position(x, y)
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to update window position: {e}")
            return {"success": False, "error": str(e)}
            
    def stop_overlay(self) -> Dict[str, Any]:
        """
        Stop overlay and close LibreOffice.
        
        Returns:
            Stop status
        """
        try:
            self.overlay_manager.stop()
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to stop overlay: {e}")
            return {"success": False, "error": str(e)}
            
    def get_overlay_status(self) -> Dict[str, Any]:
        """
        Get current overlay status.
        
        Returns:
            Status information
        """
        try:
            status = self.overlay_manager.get_status()
            status["success"] = True
            return status
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"success": False, "error": str(e)}
            
    def configure_sync_engine(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure position sync engine settings.
        
        Args:
            settings: Sync engine settings
                - enable_smoothing: bool
                - smoothing_factor: float (0-1)
                - enable_prediction: bool
                - min_fps: int
                - max_fps: int
                
        Returns:
            Configuration status
        """
        try:
            sync_engine = self.overlay_manager.sync_engine
            
            if "enable_smoothing" in settings:
                sync_engine.set_smoothing(
                    settings["enable_smoothing"],
                    settings.get("smoothing_factor", 0.3)
                )
                
            if "enable_prediction" in settings:
                sync_engine.set_prediction(settings["enable_prediction"])
                
            if "min_fps" in settings:
                sync_engine.min_fps = settings["min_fps"]
                
            if "max_fps" in settings:
                sync_engine.max_fps = settings["max_fps"]
                
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to configure sync engine: {e}")
            return {"success": False, "error": str(e)}
            
    def get_sync_metrics(self) -> Dict[str, Any]:
        """
        Get position sync performance metrics.
        
        Returns:
            Sync engine metrics
        """
        try:
            metrics = self.overlay_manager.sync_engine.get_metrics()
            metrics["success"] = True
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get sync metrics: {e}")
            return {"success": False, "error": str(e)}
            
    def calibrate_browser_offsets(self, test_bounds: Dict[str, float]) -> Dict[str, Any]:
        """
        Calibrate browser chrome offsets.
        
        Args:
            test_bounds: Known test element bounds
            
        Returns:
            Calibration status
        """
        try:
            self.overlay_manager.coordinate_system.calibrate_offsets(test_bounds)
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to calibrate offsets: {e}")
            return {"success": False, "error": str(e)}
            
    def set_overlay_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set overlay display options.
        
        Args:
            options: Display options
                - enable_decorations_removal: bool
                - enable_always_on_top: bool
                
        Returns:
            Options status
        """
        try:
            if "enable_decorations_removal" in options:
                self.overlay_manager.enable_decorations_removal = options["enable_decorations_removal"]
                
            if "enable_always_on_top" in options:
                self.overlay_manager.enable_always_on_top = options["enable_always_on_top"]
                
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to set overlay options: {e}")
            return {"success": False, "error": str(e)}
            
    def _on_state_change(self, state) -> None:
        """Handle state change from overlay manager."""
        self._current_state = state.value
        logger.info(f"Overlay state changed to: {self._current_state}")
        
    def _on_error(self, error: str) -> None:
        """Handle error from overlay manager."""
        self._last_error = error
        logger.error(f"Overlay error: {error}")