"""
Window Tracker for LibreOffice Process

This module finds and tracks LibreOffice windows using multiple strategies
for different platforms and window managers.
"""

import logging
import platform
import subprocess
import time
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class WindowInfo:
    """Information about a window"""
    
    def __init__(self, window_id: int, pid: int, title: str, class_name: str):
        self.window_id = window_id
        self.pid = pid
        self.title = title
        self.class_name = class_name
        
    def __repr__(self):
        return f"WindowInfo(id={self.window_id}, pid={self.pid}, title='{self.title}', class='{self.class_name}')"


class WindowTracker:
    """
    Tracks LibreOffice windows across different platforms.
    Uses multiple search strategies to find windows reliably.
    """
    
    def __init__(self):
        self.platform = platform.system()
        self._last_window_id: Optional[int] = None
        self._search_strategies = self._get_search_strategies()
        
    def _get_search_strategies(self) -> List[str]:
        """
        Get platform-specific search strategies in order of preference.
        
        Returns:
            List of strategy names to try
        """
        if self.platform == "Linux":
            return ["xdotool", "wmctrl", "xwininfo", "xprop"]
        elif self.platform == "Windows":
            return ["win32gui", "powershell", "tasklist"]
        elif self.platform == "Darwin":
            return ["applescript", "accessibility"]
        else:
            return []
            
    def find_libreoffice_window(self, pid: int, timeout: float = 5.0) -> Optional[WindowInfo]:
        """
        Find LibreOffice window by process ID.
        
        Args:
            pid: LibreOffice process ID
            timeout: Maximum time to search
            
        Returns:
            WindowInfo if found, None otherwise
        """
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < timeout:
            attempt += 1
            logger.debug(f"Window search attempt {attempt}")
            
            for strategy in self._search_strategies:
                try:
                    window = self._find_window_with_strategy(strategy, pid)
                    if window:
                        logger.info(f"Found window using {strategy}: {window}")
                        self._last_window_id = window.window_id
                        return window
                except Exception as e:
                    logger.debug(f"Strategy {strategy} failed: {e}")
                    
            time.sleep(0.5)
            
        logger.warning(f"Could not find LibreOffice window for PID {pid}")
        return None
        
    def _find_window_with_strategy(self, strategy: str, pid: int) -> Optional[WindowInfo]:
        """
        Find window using specific strategy.
        
        Args:
            strategy: Search strategy name
            pid: Process ID to search for
            
        Returns:
            WindowInfo if found
        """
        if self.platform == "Linux":
            if strategy == "xdotool":
                return self._find_window_xdotool(pid)
            elif strategy == "wmctrl":
                return self._find_window_wmctrl(pid)
            elif strategy == "xwininfo":
                return self._find_window_xwininfo(pid)
            elif strategy == "xprop":
                return self._find_window_xprop(pid)
                
        elif self.platform == "Windows":
            if strategy == "win32gui":
                return self._find_window_win32gui(pid)
            elif strategy == "powershell":
                return self._find_window_powershell(pid)
                
        return None
        
    def _find_window_xdotool(self, pid: int) -> Optional[WindowInfo]:
        """Find window using xdotool (Linux)"""
        try:
            # Search by PID
            result = subprocess.run(
                ["xdotool", "search", "--pid", str(pid)],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                
                # Get info for each window
                for window_id in window_ids:
                    # Get window name
                    name_result = subprocess.run(
                        ["xdotool", "getwindowname", window_id],
                        capture_output=True,
                        text=True
                    )
                    
                    if name_result.returncode == 0:
                        window_name = name_result.stdout.strip()
                        
                        # Check if it's a LibreOffice window
                        if any(keyword in window_name.lower() for keyword in 
                               ["libreoffice", "writer", "calc", "impress", "draw"]):
                            return WindowInfo(
                                window_id=int(window_id),
                                pid=pid,
                                title=window_name,
                                class_name="libreoffice"
                            )
                            
        except Exception as e:
            logger.debug(f"xdotool search failed: {e}")
            
        return None
        
    def _find_window_wmctrl(self, pid: int) -> Optional[WindowInfo]:
        """Find window using wmctrl (Linux)"""
        try:
            result = subprocess.run(
                ["wmctrl", "-lp"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(None, 4)
                    if len(parts) >= 5:
                        win_id, desktop, win_pid, machine, title = parts
                        if int(win_pid) == pid:
                            if any(keyword in title.lower() for keyword in 
                                   ["libreoffice", "writer", "calc", "impress", "draw"]):
                                return WindowInfo(
                                    window_id=int(win_id, 16),  # wmctrl returns hex
                                    pid=pid,
                                    title=title,
                                    class_name="libreoffice"
                                )
                                
        except Exception as e:
            logger.debug(f"wmctrl search failed: {e}")
            
        return None
        
    def _find_window_xwininfo(self, pid: int) -> Optional[WindowInfo]:
        """Find window using xwininfo (Linux)"""
        try:
            # Get root window children
            result = subprocess.run(
                ["xwininfo", "-root", "-tree"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse output to find LibreOffice windows
                for line in result.stdout.split('\n'):
                    if any(keyword in line.lower() for keyword in 
                           ["libreoffice", "writer", "calc", "impress", "draw"]):
                        # Extract window ID from line
                        if "0x" in line:
                            win_id_str = line.split()[0]
                            if win_id_str.startswith("0x"):
                                return WindowInfo(
                                    window_id=int(win_id_str, 16),
                                    pid=pid,
                                    title=line,
                                    class_name="libreoffice"
                                )
                                
        except Exception as e:
            logger.debug(f"xwininfo search failed: {e}")
            
        return None
        
    def _find_window_xprop(self, pid: int) -> Optional[WindowInfo]:
        """Find window using xprop (Linux)"""
        try:
            # Get all window IDs
            result = subprocess.run(
                ["xprop", "-root", "_NET_CLIENT_LIST"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0 and "window id" in result.stdout:
                # Extract window IDs
                ids_part = result.stdout.split("#")[1].strip()
                window_ids = [id.strip() for id in ids_part.split(",")]
                
                for win_id in window_ids:
                    # Check each window's PID
                    pid_result = subprocess.run(
                        ["xprop", "-id", win_id, "_NET_WM_PID"],
                        capture_output=True,
                        text=True
                    )
                    
                    if pid_result.returncode == 0 and str(pid) in pid_result.stdout:
                        # Get window name
                        name_result = subprocess.run(
                            ["xprop", "-id", win_id, "WM_NAME"],
                            capture_output=True,
                            text=True
                        )
                        
                        if name_result.returncode == 0:
                            return WindowInfo(
                                window_id=int(win_id, 16) if win_id.startswith("0x") else int(win_id),
                                pid=pid,
                                title=name_result.stdout.strip(),
                                class_name="libreoffice"
                            )
                            
        except Exception as e:
            logger.debug(f"xprop search failed: {e}")
            
        return None
        
    def _find_window_win32gui(self, pid: int) -> Optional[WindowInfo]:
        """Find window using win32gui (Windows)"""
        try:
            import win32gui
            import win32process
            
            def enum_window_callback(hwnd, windows):
                try:
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        window_text = win32gui.GetWindowText(hwnd)
                        if window_text and any(keyword in window_text.lower() for keyword in 
                                             ["libreoffice", "writer", "calc", "impress", "draw"]):
                            windows.append(WindowInfo(
                                window_id=hwnd,
                                pid=pid,
                                title=window_text,
                                class_name="libreoffice"
                            ))
                except:
                    pass
                    
            windows = []
            win32gui.EnumWindows(enum_window_callback, windows)
            
            return windows[0] if windows else None
            
        except ImportError:
            logger.debug("win32gui not available")
        except Exception as e:
            logger.debug(f"win32gui search failed: {e}")
            
        return None
        
    def _find_window_powershell(self, pid: int) -> Optional[WindowInfo]:
        """Find window using PowerShell (Windows)"""
        try:
            script = f"""
            $windows = Get-Process -Id {pid} | Select-Object -ExpandProperty MainWindowHandle
            if ($windows) {{
                $title = Get-Process -Id {pid} | Select-Object -ExpandProperty MainWindowTitle
                Write-Output "$windows|$title"
            }}
            """
            
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                handle, title = result.stdout.strip().split('|', 1)
                return WindowInfo(
                    window_id=int(handle),
                    pid=pid,
                    title=title,
                    class_name="libreoffice"
                )
                
        except Exception as e:
            logger.debug(f"PowerShell search failed: {e}")
            
        return None
        
    def verify_window_exists(self, window_id: int) -> bool:
        """
        Verify that a window still exists.
        
        Args:
            window_id: Window ID to check
            
        Returns:
            True if window exists
        """
        if self.platform == "Linux":
            try:
                result = subprocess.run(
                    ["xdotool", "getwindowname", str(window_id)],
                    capture_output=True,
                    timeout=1
                )
                return result.returncode == 0
            except:
                return False
                
        elif self.platform == "Windows":
            try:
                import win32gui
                return win32gui.IsWindow(window_id)
            except:
                return False
                
        return False
        
    def get_window_geometry(self, window_id: int) -> Optional[Dict[str, int]]:
        """
        Get window position and size.
        
        Args:
            window_id: Window ID
            
        Returns:
            Dict with x, y, width, height or None
        """
        if self.platform == "Linux":
            try:
                result = subprocess.run(
                    ["xdotool", "getwindowgeometry", str(window_id)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Parse output
                    lines = result.stdout.strip().split('\n')
                    position_line = [l for l in lines if "Position:" in l][0]
                    geometry_line = [l for l in lines if "Geometry:" in l][0]
                    
                    # Extract values
                    pos = position_line.split()[1].split(',')
                    x = int(pos[0])
                    y = int(pos[1].split()[0])
                    
                    geo = geometry_line.split()[1].split('x')
                    width = int(geo[0])
                    height = int(geo[1])
                    
                    return {"x": x, "y": y, "width": width, "height": height}
                    
            except Exception as e:
                logger.debug(f"Failed to get window geometry: {e}")
                
        return None