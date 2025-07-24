"""
Coordinate System for LibreOffice Overlay Positioning

This module tracks the container element position in screen coordinates,
accounting for browser chrome, zoom levels, and scrolling.
"""

import logging
import platform
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class ScreenPosition:
    """Represents an absolute screen position"""
    x: int
    y: int
    width: int
    height: int
    
    def __repr__(self):
        return f"ScreenPosition(x={self.x}, y={self.y}, w={self.width}, h={self.height})"


@dataclass
class BrowserOffsets:
    """Browser chrome offsets from window edge"""
    top: int = 0
    left: int = 0
    right: int = 0
    bottom: int = 0


class CoordinateSystem:
    """
    Tracks container element position and provides screen coordinates
    for LibreOffice window positioning.
    """
    
    def __init__(self):
        self.container_bounds: Optional[Dict[str, float]] = None
        self.window_position: Optional[Tuple[int, int]] = None
        self.browser_offsets = BrowserOffsets()
        self.zoom_level: float = 1.0
        self._last_position: Optional[ScreenPosition] = None
        
    def update_container_bounds(self, bounds: Dict[str, float]) -> None:
        """
        Update container element bounds from JavaScript.
        
        Args:
            bounds: Dict with keys: x, y, width, height, top, left, bottom, right
        """
        self.container_bounds = bounds
        logger.debug(f"Updated container bounds: {bounds}")
        
    def update_window_position(self, x: int, y: int) -> None:
        """
        Update PyWebView window position.
        
        Args:
            x: Window X coordinate
            y: Window Y coordinate
        """
        self.window_position = (x, y)
        logger.debug(f"Updated window position: ({x}, {y})")
        
    def update_browser_offsets(self, offsets: BrowserOffsets) -> None:
        """
        Update browser chrome offsets.
        
        Args:
            offsets: Browser chrome offsets
        """
        self.browser_offsets = offsets
        logger.debug(f"Updated browser offsets: {offsets}")
        
    def update_zoom_level(self, zoom: float) -> None:
        """
        Update browser zoom level.
        
        Args:
            zoom: Current zoom level (1.0 = 100%)
        """
        self.zoom_level = zoom
        logger.debug(f"Updated zoom level: {zoom}")
        
    def calculate_screen_position(self) -> Optional[ScreenPosition]:
        """
        Calculate absolute screen position for LibreOffice window.
        
        Returns:
            ScreenPosition or None if insufficient data
        """
        if not self.container_bounds or not self.window_position:
            logger.warning("Insufficient data for position calculation")
            return None
            
        # Get window position
        win_x, win_y = self.window_position
        
        # Apply browser offsets
        chrome_x = self.browser_offsets.left
        chrome_y = self.browser_offsets.top
        
        # Get container position relative to viewport
        container_x = self.container_bounds.get('x', 0)
        container_y = self.container_bounds.get('y', 0)
        container_width = self.container_bounds.get('width', 0)
        container_height = self.container_bounds.get('height', 0)
        
        # Apply zoom level
        container_x *= self.zoom_level
        container_y *= self.zoom_level
        container_width *= self.zoom_level
        container_height *= self.zoom_level
        
        # Calculate absolute screen position
        screen_x = int(win_x + chrome_x + container_x)
        screen_y = int(win_y + chrome_y + container_y)
        screen_width = int(container_width)
        screen_height = int(container_height)
        
        position = ScreenPosition(
            x=screen_x,
            y=screen_y,
            width=screen_width,
            height=screen_height
        )
        
        # Log if position changed significantly
        if self._last_position:
            delta_x = abs(position.x - self._last_position.x)
            delta_y = abs(position.y - self._last_position.y)
            if delta_x > 5 or delta_y > 5:
                logger.debug(f"Position changed: {position}")
                
        self._last_position = position
        return position
        
    def get_platform_specific_offsets(self) -> BrowserOffsets:
        """
        Get platform-specific browser chrome offsets.
        
        Returns:
            Platform-specific browser offsets
        """
        system = platform.system()
        
        if system == "Windows":
            # Windows typically has title bar and window borders
            return BrowserOffsets(top=30, left=8, right=8, bottom=8)
        elif system == "Linux":
            # Linux varies by window manager
            return BrowserOffsets(top=25, left=2, right=2, bottom=2)
        elif system == "Darwin":
            # macOS has different chrome
            return BrowserOffsets(top=22, left=0, right=0, bottom=0)
        else:
            # Default conservative offsets
            return BrowserOffsets(top=30, left=5, right=5, bottom=5)
            
    def calibrate_offsets(self, test_element_bounds: Dict[str, float]) -> None:
        """
        Calibrate browser offsets using a test element.
        
        Args:
            test_element_bounds: Known element bounds for calibration
        """
        # This would involve creating a test element at known position
        # and measuring the difference between expected and actual
        logger.info("Offset calibration requested - not implemented yet")
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert current state to dictionary.
        
        Returns:
            Dictionary representation of coordinate system state
        """
        position = self.calculate_screen_position()
        return {
            'container_bounds': self.container_bounds,
            'window_position': self.window_position,
            'browser_offsets': {
                'top': self.browser_offsets.top,
                'left': self.browser_offsets.left,
                'right': self.browser_offsets.right,
                'bottom': self.browser_offsets.bottom
            },
            'zoom_level': self.zoom_level,
            'screen_position': {
                'x': position.x,
                'y': position.y,
                'width': position.width,
                'height': position.height
            } if position else None
        }