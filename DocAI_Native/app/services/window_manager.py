"""
Native Window Manager Service
Handles LibreOffice window positioning and lifecycle management
"""

import logging
import platform
import subprocess
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import threading
import json

logger = logging.getLogger(__name__)


class NativeWindowManager:
    """Manages native LibreOffice windows for document viewing"""
    
    def __init__(self, uno_bridge):
        self.uno_bridge = uno_bridge
        self.active_windows = {}  # doc_id -> window_info mapping
        self.platform = platform.system()
        self._lock = threading.Lock()
        
        # Platform-specific imports
        if self.platform == "Linux":
            try:
                global Display, Window, X
                from Xlib import Display as XDisplay, X
                from Xlib.display import Display
                from Xlib.protocol.event import ClientMessage
                from Xlib.xobject.drawable import Window
                self.x11_available = True
                logger.info("X11 libraries loaded successfully")
            except ImportError:
                self.x11_available = False
                logger.warning("python-xlib not available - window embedding will be limited")
        
        logger.info(f"NativeWindowManager initialized for platform: {self.platform}")
    
    def open_document_window(self, filename: str, parent_window_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Open a document in a native LibreOffice window
        
        Args:
            filename: Path to the document file
            parent_window_info: Information about the parent window for positioning
            
        Returns:
            Dict containing window information and status
        """
        try:
            # Ensure UNO connection
            if not self.uno_bridge.ensure_connection():
                return {
                    'success': False,
                    'error': 'Failed to establish UNO connection'
                }
            
            # Load document via UNO
            logger.info(f"Loading document for native viewing: {filename}")
            result = self.uno_bridge.load_document(filename, {'hidden': False})
            
            if not result['success']:
                return result
            
            doc_id = result['doc_id']
            window_handle = result.get('window')
            
            # Store window information
            with self._lock:
                self.active_windows[doc_id] = {
                    'doc_id': doc_id,
                    'filename': filename,
                    'window_handle': window_handle,
                    'parent_info': parent_window_info,
                    'created_at': time.time()
                }
            
            # Position window relative to parent (platform-specific)
            if window_handle and parent_window_info:
                position_result = self._position_window(doc_id, parent_window_info)
                result['positioning'] = position_result
            
            # Add control interface information
            result['controls'] = {
                'zoom_endpoint': f'/api/v1/document/{doc_id}/zoom',
                'page_endpoint': f'/api/v1/document/{doc_id}/page',
                'close_endpoint': f'/api/v1/document/{doc_id}/close'
            }
            
            logger.info(f"Document window opened successfully: {doc_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to open document window: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _position_window(self, doc_id: str, parent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Position LibreOffice window relative to parent"""
        try:
            window_info = self.active_windows.get(doc_id)
            if not window_info or not window_info.get('window_handle'):
                return {'success': False, 'error': 'No window handle available'}
            
            if self.platform == "Linux":
                return self._position_window_linux(window_info['window_handle'], parent_info)
            elif self.platform == "Windows":
                return self._position_window_windows(window_info['window_handle'], parent_info)
            elif self.platform == "Darwin":
                return self._position_window_macos(window_info['window_handle'], parent_info)
            else:
                return {'success': False, 'error': f'Unsupported platform: {self.platform}'}
                
        except Exception as e:
            logger.error(f"Window positioning failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _position_window_linux(self, window_handle: Dict[str, Any], parent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Position window on Linux using X11"""
        if not self.x11_available:
            return {'success': False, 'error': 'X11 libraries not available'}
        
        try:
            if window_handle['type'] != 'x11':
                return {'success': False, 'error': 'Invalid window handle type for Linux'}
            
            x11_id = window_handle['handle']
            
            # Calculate position relative to parent
            parent_x = parent_info.get('x', 100)
            parent_y = parent_info.get('y', 100)
            parent_width = parent_info.get('width', 1200)
            parent_height = parent_info.get('height', 800)
            
            # Position LibreOffice window to overlap with document area
            # Assuming document area is center of parent window
            doc_x = parent_x + int(parent_width * 0.25)  # 25% from left
            doc_y = parent_y + 50  # Account for header
            doc_width = int(parent_width * 0.5)  # 50% of parent width
            doc_height = parent_height - 100  # Leave space for header/footer
            
            # Use xdotool for window manipulation (more reliable than python-xlib for positioning)
            try:
                # Check if xdotool is available
                xdotool_check = subprocess.run(['which', 'xdotool'], capture_output=True)
                if xdotool_check.returncode != 0:
                    logger.warning("xdotool not found. Install with: sudo apt-get install xdotool")
                    return self._position_window_linux_xlib(x11_id, doc_x, doc_y, doc_width, doc_height)
                
                # Move and resize window
                subprocess.run([
                    'xdotool', 'windowmove', str(x11_id), str(doc_x), str(doc_y)
                ], check=True, capture_output=True)
                
                subprocess.run([
                    'xdotool', 'windowsize', str(x11_id), str(doc_width), str(doc_height)
                ], check=True, capture_output=True)
                
                # Remove window decorations for embedded appearance
                subprocess.run([
                    'xdotool', 'set_window', '--name', 'LibreOffice Document Viewer', str(x11_id)
                ], check=True, capture_output=True)
                
                logger.info(f"Positioned X11 window {x11_id} at ({doc_x}, {doc_y}) size ({doc_width}x{doc_height})")
                
                return {
                    'success': True,
                    'position': {'x': doc_x, 'y': doc_y},
                    'size': {'width': doc_width, 'height': doc_height}
                }
                
            except subprocess.CalledProcessError as e:
                logger.warning(f"xdotool command failed: {e}")
                # Fallback to python-xlib if xdotool fails
                return self._position_window_linux_xlib(x11_id, doc_x, doc_y, doc_width, doc_height)
            except FileNotFoundError:
                logger.warning("xdotool not found. Install with: sudo apt-get install xdotool")
                return self._position_window_linux_xlib(x11_id, doc_x, doc_y, doc_width, doc_height)
                
        except Exception as e:
            logger.error(f"Linux window positioning failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _position_window_linux_xlib(self, window_id: int, x: int, y: int, width: int, height: int) -> Dict[str, Any]:
        """Fallback positioning using python-xlib"""
        try:
            display = Display()
            window = display.create_resource_object('window', window_id)
            
            # Configure window
            window.configure(
                x=x,
                y=y,
                width=width,
                height=height
            )
            
            # Remove decorations by setting window type
            # This makes it appear more embedded
            wm_window_type = display.intern_atom('_NET_WM_WINDOW_TYPE')
            wm_window_type_dialog = display.intern_atom('_NET_WM_WINDOW_TYPE_DIALOG')
            atom_type = display.intern_atom('ATOM')
            
            window.change_property(
                wm_window_type,
                atom_type,
                32,
                [wm_window_type_dialog]
            )
            
            display.sync()
            
            return {
                'success': True,
                'position': {'x': x, 'y': y},
                'size': {'width': width, 'height': height},
                'method': 'xlib'
            }
            
        except Exception as e:
            logger.error(f"Xlib positioning failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _position_window_windows(self, window_handle: Dict[str, Any], parent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Position window on Windows"""
        # TODO: Implement Windows positioning using win32api
        logger.warning("Windows positioning not yet implemented")
        return {'success': False, 'error': 'Windows positioning not implemented'}
    
    def _position_window_macos(self, window_handle: Dict[str, Any], parent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Position window on macOS"""
        # TODO: Implement macOS positioning using PyObjC
        logger.warning("macOS positioning not yet implemented")
        return {'success': False, 'error': 'macOS positioning not implemented'}
    
    def update_window_position(self, doc_id: str, position: Dict[str, int]) -> Dict[str, Any]:
        """Update position of an existing window"""
        with self._lock:
            if doc_id not in self.active_windows:
                return {'success': False, 'error': 'Document window not found'}
            
            window_info = self.active_windows[doc_id]
            
        # Update position using platform-specific method
        result = self._position_window(doc_id, position)
        
        if result['success']:
            with self._lock:
                window_info['last_position_update'] = time.time()
        
        return result
    
    def close_window(self, doc_id: str) -> Dict[str, Any]:
        """Close a document window"""
        try:
            with self._lock:
                if doc_id not in self.active_windows:
                    return {'success': False, 'error': 'Document window not found'}
                
                window_info = self.active_windows[doc_id]
            
            # Close via UNO bridge
            result = self.uno_bridge.close_document(doc_id)
            
            if result['success']:
                with self._lock:
                    del self.active_windows[doc_id]
                logger.info(f"Closed document window: {doc_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to close window: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_window_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a document window"""
        with self._lock:
            return self.active_windows.get(doc_id)
    
    def list_active_windows(self) -> Dict[str, Dict[str, Any]]:
        """List all active document windows"""
        with self._lock:
            return dict(self.active_windows)
    
    def close_all_windows(self) -> Dict[str, Any]:
        """Close all active windows"""
        errors = []
        closed_count = 0
        
        # Get list of windows to close
        with self._lock:
            doc_ids = list(self.active_windows.keys())
        
        for doc_id in doc_ids:
            result = self.close_window(doc_id)
            if result['success']:
                closed_count += 1
            else:
                errors.append(f"{doc_id}: {result.get('error', 'Unknown error')}")
        
        return {
            'success': len(errors) == 0,
            'closed': closed_count,
            'errors': errors
        }
    
    def handle_window_event(self, doc_id: str, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle window events like focus, resize, etc."""
        with self._lock:
            if doc_id not in self.active_windows:
                return {'success': False, 'error': 'Document window not found'}
            
            window_info = self.active_windows[doc_id]
            window_info['last_event'] = {
                'type': event_type,
                'data': event_data,
                'timestamp': time.time()
            }
        
        logger.debug(f"Window event for {doc_id}: {event_type}")
        return {'success': True}


def create_window_manager(uno_bridge) -> NativeWindowManager:
    """Factory function to create window manager"""
    return NativeWindowManager(uno_bridge)