"""
LibreOffice Overlay Manager

Main orchestration class that coordinates all overlay positioning components
to display LibreOffice documents within the DocAI interface.
"""

import logging
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from enum import Enum

from .coordinates import CoordinateSystem, ScreenPosition
from .window_tracker import WindowTracker, WindowInfo
from .decorations import DecorationRemover
from .sync_engine import PositionSyncEngine

logger = logging.getLogger(__name__)


class OverlayState(Enum):
    """Overlay manager states"""
    IDLE = "idle"
    LAUNCHING = "launching"
    POSITIONING = "positioning"
    READY = "ready"
    ERROR = "error"
    STOPPING = "stopping"


class LibreOfficeOverlayManager:
    """
    Manages LibreOffice overlay positioning for document viewing.
    
    This class orchestrates:
    - LibreOffice process launching
    - Window finding and tracking
    - Decoration removal
    - Position synchronization
    - Clean shutdown
    """
    
    def __init__(self):
        """Initialize overlay manager."""
        self.platform = platform.system()
        
        # Components
        self.coordinate_system = CoordinateSystem()
        self.window_tracker = WindowTracker()
        self.decoration_remover = DecorationRemover()
        self.sync_engine = PositionSyncEngine(self._on_position_update)
        
        # State
        self.state = OverlayState.IDLE
        self._libreoffice_process: Optional[subprocess.Popen] = None
        self._window_info: Optional[WindowInfo] = None
        self._document_path: Optional[str] = None
        
        # Callbacks
        self._state_callback: Optional[Callable[[OverlayState], None]] = None
        self._error_callback: Optional[Callable[[str], None]] = None
        
        # Configuration
        self.launch_timeout = 10.0  # Seconds to wait for LibreOffice
        self.window_search_timeout = 5.0  # Seconds to search for window
        self.enable_decorations_removal = True
        self.enable_always_on_top = True
        
    def set_callbacks(self, 
                     state_callback: Optional[Callable[[OverlayState], None]] = None,
                     error_callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Set callback functions.
        
        Args:
            state_callback: Called when state changes
            error_callback: Called on errors
        """
        self._state_callback = state_callback
        self._error_callback = error_callback
        
    def _set_state(self, state: OverlayState) -> None:
        """Update state and notify callback."""
        old_state = self.state
        self.state = state
        logger.info(f"State change: {old_state.value} -> {state.value}")
        
        if self._state_callback:
            try:
                self._state_callback(state)
            except Exception as e:
                logger.error(f"State callback error: {e}")
                
    def _report_error(self, error: str) -> None:
        """Report error and update state."""
        logger.error(f"Overlay error: {error}")
        self._set_state(OverlayState.ERROR)
        
        if self._error_callback:
            try:
                self._error_callback(error)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")
                
    def load_document(self, document_path: str, container_bounds: Dict[str, float]) -> bool:
        """
        Load a document in LibreOffice with overlay positioning.
        
        Args:
            document_path: Path to document file
            container_bounds: Container element bounds (x, y, width, height)
            
        Returns:
            True if successful
        """
        if self.state != OverlayState.IDLE:
            self.stop()
            
        logger.info(f"Loading document: {document_path}")
        self._document_path = document_path
        
        # Validate document exists
        if not os.path.exists(document_path):
            self._report_error(f"Document not found: {document_path}")
            return False
            
        # Update container bounds
        self.coordinate_system.update_container_bounds(container_bounds)
        
        # Start loading process
        self._set_state(OverlayState.LAUNCHING)
        
        try:
            # Launch LibreOffice
            if not self._launch_libreoffice(document_path):
                self._report_error("Failed to launch LibreOffice")
                return False
                
            # Find window
            if not self._find_window():
                self._report_error("Failed to find LibreOffice window")
                return False
                
            # Position window
            self._set_state(OverlayState.POSITIONING)
            if not self._position_window():
                self._report_error("Failed to position window")
                return False
                
            # Start position sync
            self.sync_engine.start(self._window_info.window_id)
            
            self._set_state(OverlayState.READY)
            return True
            
        except Exception as e:
            self._report_error(f"Unexpected error: {e}")
            return False
            
    def _launch_libreoffice(self, document_path: str) -> bool:
        """
        Launch LibreOffice process.
        
        Args:
            document_path: Document to open
            
        Returns:
            True if successful
        """
        logger.info("Launching LibreOffice process")
        
        # Build command
        if self.platform == "Windows":
            libreoffice_cmd = self._find_libreoffice_windows()
        else:
            libreoffice_cmd = self._find_libreoffice_unix()
            
        if not libreoffice_cmd:
            logger.error("LibreOffice not found")
            return False
            
        # Launch command with minimal UI
        cmd = [
            libreoffice_cmd,
            "--nologo",
            "--norestore",
            "--view",  # Read-only mode
            "--nolockcheck",
            document_path
        ]
        
        try:
            self._libreoffice_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it time to start
            time.sleep(1.0)
            
            # Check if still running
            if self._libreoffice_process.poll() is not None:
                stdout, stderr = self._libreoffice_process.communicate()
                logger.error(f"LibreOffice exited immediately: {stderr.decode()}")
                return False
                
            logger.info(f"LibreOffice launched with PID: {self._libreoffice_process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch LibreOffice: {e}")
            return False
            
    def _find_libreoffice_windows(self) -> Optional[str]:
        """Find LibreOffice executable on Windows."""
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
                
        # Try registry or PATH
        try:
            result = subprocess.run(
                ["where", "soffice.exe"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
            
        return None
        
    def _find_libreoffice_unix(self) -> Optional[str]:
        """Find LibreOffice executable on Unix."""
        commands = ["libreoffice", "soffice", "ooffice"]
        
        for cmd in commands:
            try:
                result = subprocess.run(
                    ["which", cmd],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
                
        # Try common paths
        paths = [
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "/opt/libreoffice/program/soffice",
            "/usr/local/bin/libreoffice"
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
                
        return None
        
    def _find_window(self) -> bool:
        """Find LibreOffice window."""
        logger.info("Searching for LibreOffice window")
        
        if not self._libreoffice_process:
            return False
            
        window = self.window_tracker.find_libreoffice_window(
            self._libreoffice_process.pid,
            timeout=self.window_search_timeout
        )
        
        if not window:
            return False
            
        self._window_info = window
        logger.info(f"Found window: {window}")
        return True
        
    def _position_window(self) -> bool:
        """Position window according to container."""
        if not self._window_info:
            return False
            
        logger.info("Positioning LibreOffice window")
        
        # Remove decorations if enabled
        if self.enable_decorations_removal:
            if not self.decoration_remover.remove_decorations(self._window_info.window_id):
                logger.warning("Failed to remove window decorations")
                
        # Set always on top if enabled
        if self.enable_always_on_top:
            self.decoration_remover.set_always_on_top(self._window_info.window_id, True)
            
        # Calculate screen position
        position = self.coordinate_system.calculate_screen_position()
        if not position:
            logger.warning("No screen position available")
            return False
            
        # Apply initial position
        self._apply_position(position)
        
        return True
        
    def _apply_position(self, position: ScreenPosition) -> None:
        """Apply position to window."""
        if not self._window_info:
            return
            
        logger.debug(f"Applying position: {position}")
        
        if self.platform == "Linux":
            try:
                # Move window
                subprocess.run(
                    ["xdotool", "windowmove", str(self._window_info.window_id),
                     str(position.x), str(position.y)],
                    timeout=1
                )
                
                # Resize window
                subprocess.run(
                    ["xdotool", "windowsize", str(self._window_info.window_id),
                     str(position.width), str(position.height)],
                    timeout=1
                )
            except Exception as e:
                logger.error(f"Failed to position window: {e}")
                
        elif self.platform == "Windows":
            try:
                import win32gui
                win32gui.MoveWindow(
                    self._window_info.window_id,
                    position.x, position.y,
                    position.width, position.height,
                    True
                )
            except Exception as e:
                logger.error(f"Failed to position window: {e}")
                
    def update_container_bounds(self, bounds: Dict[str, float]) -> None:
        """
        Update container bounds and reposition window.
        
        Args:
            bounds: New container bounds
        """
        self.coordinate_system.update_container_bounds(bounds)
        
        if self.state == OverlayState.READY:
            position = self.coordinate_system.calculate_screen_position()
            if position:
                self.sync_engine.update_position(
                    position.x, position.y,
                    position.width, position.height
                )
                
    def update_window_position(self, x: int, y: int) -> None:
        """
        Update PyWebView window position.
        
        Args:
            x: Window X coordinate
            y: Window Y coordinate
        """
        self.coordinate_system.update_window_position(x, y)
        
        if self.state == OverlayState.READY:
            position = self.coordinate_system.calculate_screen_position()
            if position:
                self.sync_engine.update_position(
                    position.x, position.y,
                    position.width, position.height
                )
                
    def _on_position_update(self, x: int, y: int, width: int, height: int) -> None:
        """Called by sync engine after position update."""
        pass  # Can be used for logging or metrics
        
    def stop(self) -> None:
        """Stop overlay and clean up."""
        if self.state == OverlayState.IDLE:
            return
            
        logger.info("Stopping overlay manager")
        self._set_state(OverlayState.STOPPING)
        
        # Stop position sync
        self.sync_engine.stop()
        
        # Restore window decorations
        if self._window_info and self.decoration_remover:
            self.decoration_remover.restore_decorations(self._window_info.window_id)
            
        # Terminate LibreOffice
        if self._libreoffice_process:
            try:
                self._libreoffice_process.terminate()
                self._libreoffice_process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                logger.warning("LibreOffice didn't terminate, killing")
                self._libreoffice_process.kill()
            except Exception as e:
                logger.error(f"Error terminating LibreOffice: {e}")
                
        # Reset state
        self._libreoffice_process = None
        self._window_info = None
        self._document_path = None
        self._set_state(OverlayState.IDLE)
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status.
        
        Returns:
            Status dictionary
        """
        return {
            "state": self.state.value,
            "document": self._document_path,
            "libreoffice_pid": self._libreoffice_process.pid if self._libreoffice_process else None,
            "window_id": self._window_info.window_id if self._window_info else None,
            "coordinates": self.coordinate_system.to_dict(),
            "sync_metrics": self.sync_engine.get_metrics() if self.state == OverlayState.READY else None
        }
        
    def __del__(self):
        """Cleanup on deletion."""
        self.stop()