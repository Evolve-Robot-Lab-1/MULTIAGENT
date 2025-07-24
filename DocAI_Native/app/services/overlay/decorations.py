"""
Window Decoration Remover for LibreOffice Overlay

This module removes window decorations (title bar, borders) from LibreOffice
windows to make them appear embedded.
"""

import logging
import platform
import subprocess
import time
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class DecorationRemover:
    """
    Removes window decorations from LibreOffice windows using
    platform-specific methods.
    """
    
    def __init__(self):
        self.platform = platform.system()
        self._removal_methods = self._get_removal_methods()
        self._removed_windows: Dict[int, Dict[str, Any]] = {}
        
    def _get_removal_methods(self) -> List[str]:
        """
        Get platform-specific decoration removal methods.
        
        Returns:
            List of method names to try
        """
        if self.platform == "Linux":
            return ["motif_hints", "gtk_decorations", "xprop_hints", "wmctrl_decorations"]
        elif self.platform == "Windows":
            return ["win32_style", "windows_dwm"]
        elif self.platform == "Darwin":
            return ["cocoa_style"]
        else:
            return []
            
    def remove_decorations(self, window_id: int) -> bool:
        """
        Remove decorations from a window.
        
        Args:
            window_id: Window ID to modify
            
        Returns:
            True if successful
        """
        logger.info(f"Removing decorations from window {window_id}")
        
        # Try each method until one succeeds
        for method in self._removal_methods:
            try:
                if self._apply_removal_method(method, window_id):
                    logger.info(f"Successfully removed decorations using {method}")
                    self._removed_windows[window_id] = {
                        "method": method,
                        "timestamp": time.time()
                    }
                    return True
            except Exception as e:
                logger.debug(f"Method {method} failed: {e}")
                
        logger.warning(f"Failed to remove decorations from window {window_id}")
        return False
        
    def _apply_removal_method(self, method: str, window_id: int) -> bool:
        """
        Apply specific decoration removal method.
        
        Args:
            method: Method name
            window_id: Window ID
            
        Returns:
            True if successful
        """
        if self.platform == "Linux":
            if method == "motif_hints":
                return self._remove_motif_hints(window_id)
            elif method == "gtk_decorations":
                return self._remove_gtk_decorations(window_id)
            elif method == "xprop_hints":
                return self._remove_xprop_hints(window_id)
            elif method == "wmctrl_decorations":
                return self._remove_wmctrl_decorations(window_id)
                
        elif self.platform == "Windows":
            if method == "win32_style":
                return self._remove_win32_style(window_id)
            elif method == "windows_dwm":
                return self._remove_windows_dwm(window_id)
                
        return False
        
    def _remove_motif_hints(self, window_id: int) -> bool:
        """Remove decorations using Motif WM hints (Linux)"""
        try:
            # Set _MOTIF_WM_HINTS to remove decorations
            motif_hints = "2, 0, 0, 0, 0"  # No decorations
            
            result = subprocess.run(
                ["xprop", "-id", str(window_id), "-format", "_MOTIF_WM_HINTS", "32c",
                 "-set", "_MOTIF_WM_HINTS", motif_hints],
                capture_output=True,
                timeout=2
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"Motif hints removal failed: {e}")
            return False
            
    def _remove_gtk_decorations(self, window_id: int) -> bool:
        """Remove decorations using GTK hints (Linux)"""
        try:
            # Use xdotool to set window type
            result = subprocess.run(
                ["xdotool", "windowstate", "--add", "ABOVE", str(window_id)],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode == 0:
                # Remove decorations
                result = subprocess.run(
                    ["xdotool", "set_window", "--name", "", str(window_id)],
                    capture_output=True,
                    timeout=2
                )
                
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"GTK decorations removal failed: {e}")
            return False
            
    def _remove_xprop_hints(self, window_id: int) -> bool:
        """Remove decorations using xprop window type (Linux)"""
        try:
            # Set window type to dock or splash to remove decorations
            result = subprocess.run(
                ["xprop", "-id", str(window_id), "-format", "_NET_WM_WINDOW_TYPE", "32a",
                 "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_DOCK"],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode != 0:
                # Try splash type instead
                result = subprocess.run(
                    ["xprop", "-id", str(window_id), "-format", "_NET_WM_WINDOW_TYPE", "32a",
                     "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_SPLASH"],
                    capture_output=True,
                    timeout=2
                )
                
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"xprop hints removal failed: {e}")
            return False
            
    def _remove_wmctrl_decorations(self, window_id: int) -> bool:
        """Remove decorations using wmctrl (Linux)"""
        try:
            # Convert window ID to hex for wmctrl
            hex_id = f"0x{window_id:08x}"
            
            # Remove decorations
            result = subprocess.run(
                ["wmctrl", "-i", "-r", hex_id, "-b", "add,above,sticky"],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode == 0:
                # Set window type
                result = subprocess.run(
                    ["wmctrl", "-i", "-r", hex_id, "-b", "add,skip_taskbar,skip_pager"],
                    capture_output=True,
                    timeout=2
                )
                
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"wmctrl decorations removal failed: {e}")
            return False
            
    def _remove_win32_style(self, window_id: int) -> bool:
        """Remove decorations using Win32 API (Windows)"""
        try:
            import win32gui
            import win32con
            
            # Get current window style
            style = win32gui.GetWindowLong(window_id, win32con.GWL_STYLE)
            
            # Remove caption and border
            style &= ~(win32con.WS_CAPTION | win32con.WS_BORDER | 
                      win32con.WS_THICKFRAME | win32con.WS_MINIMIZE |
                      win32con.WS_MAXIMIZE | win32con.WS_SYSMENU)
            
            # Apply new style
            win32gui.SetWindowLong(window_id, win32con.GWL_STYLE, style)
            
            # Force redraw
            win32gui.SetWindowPos(
                window_id, 0, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
            )
            
            return True
            
        except Exception as e:
            logger.debug(f"Win32 style removal failed: {e}")
            return False
            
    def _remove_windows_dwm(self, window_id: int) -> bool:
        """Remove decorations using DWM API (Windows)"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Load DWM API
            dwmapi = ctypes.windll.dwmapi
            
            # Disable non-client rendering
            DWMNCRP_DISABLED = 1
            dwmapi.DwmSetWindowAttribute(
                window_id,
                2,  # DWMWA_NCRENDERING_POLICY
                ctypes.byref(ctypes.c_int(DWMNCRP_DISABLED)),
                ctypes.sizeof(ctypes.c_int)
            )
            
            return True
            
        except Exception as e:
            logger.debug(f"DWM removal failed: {e}")
            return False
            
    def restore_decorations(self, window_id: int) -> bool:
        """
        Restore decorations to a window.
        
        Args:
            window_id: Window ID to restore
            
        Returns:
            True if successful
        """
        if window_id not in self._removed_windows:
            logger.warning(f"Window {window_id} was not modified")
            return False
            
        logger.info(f"Restoring decorations to window {window_id}")
        
        if self.platform == "Linux":
            try:
                # Restore normal window type
                result = subprocess.run(
                    ["xprop", "-id", str(window_id), "-remove", "_MOTIF_WM_HINTS"],
                    capture_output=True,
                    timeout=2
                )
                
                # Reset window type
                subprocess.run(
                    ["xprop", "-id", str(window_id), "-format", "_NET_WM_WINDOW_TYPE", "32a",
                     "-set", "_NET_WM_WINDOW_TYPE", "_NET_WM_WINDOW_TYPE_NORMAL"],
                    capture_output=True,
                    timeout=2
                )
                
                del self._removed_windows[window_id]
                return True
                
            except Exception as e:
                logger.error(f"Failed to restore decorations: {e}")
                
        elif self.platform == "Windows":
            try:
                import win32gui
                import win32con
                
                # Restore normal window style
                style = (win32con.WS_OVERLAPPEDWINDOW | 
                        win32con.WS_VISIBLE | win32con.WS_CLIPSIBLINGS)
                
                win32gui.SetWindowLong(window_id, win32con.GWL_STYLE, style)
                
                # Force redraw
                win32gui.SetWindowPos(
                    window_id, 0, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                    win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
                )
                
                del self._removed_windows[window_id]
                return True
                
            except Exception as e:
                logger.error(f"Failed to restore decorations: {e}")
                
        return False
        
    def set_always_on_top(self, window_id: int, on_top: bool = True) -> bool:
        """
        Set window always-on-top state.
        
        Args:
            window_id: Window ID
            on_top: True to set on top
            
        Returns:
            True if successful
        """
        if self.platform == "Linux":
            try:
                action = "add" if on_top else "remove"
                result = subprocess.run(
                    ["wmctrl", "-i", "-r", f"0x{window_id:08x}", "-b", f"{action},above"],
                    capture_output=True,
                    timeout=2
                )
                return result.returncode == 0
            except:
                pass
                
        elif self.platform == "Windows":
            try:
                import win32gui
                import win32con
                
                hwnd_flag = win32con.HWND_TOPMOST if on_top else win32con.HWND_NOTOPMOST
                win32gui.SetWindowPos(
                    window_id, hwnd_flag, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
                )
                return True
            except:
                pass
                
        return False
        
    def make_window_transparent(self, window_id: int, opacity: float = 0.95) -> bool:
        """
        Make window slightly transparent (optional enhancement).
        
        Args:
            window_id: Window ID
            opacity: Opacity level (0.0 - 1.0)
            
        Returns:
            True if successful
        """
        if self.platform == "Linux":
            try:
                # Use xprop to set opacity
                opacity_value = int(opacity * 0xFFFFFFFF)
                result = subprocess.run(
                    ["xprop", "-id", str(window_id), "-format", "_NET_WM_WINDOW_OPACITY",
                     "32c", "-set", "_NET_WM_WINDOW_OPACITY", str(opacity_value)],
                    capture_output=True,
                    timeout=2
                )
                return result.returncode == 0
            except:
                pass
                
        return False