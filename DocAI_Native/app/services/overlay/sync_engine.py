"""
Position Synchronization Engine for LibreOffice Overlay

This module provides high-performance position tracking and synchronization
between the container element and LibreOffice window.
"""

import logging
import platform
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
from queue import Queue, Empty

logger = logging.getLogger(__name__)


@dataclass
class PositionUpdate:
    """Position update data"""
    x: int
    y: int
    width: int
    height: int
    timestamp: float
    
    def differs_from(self, other: 'PositionUpdate', threshold: int = 2) -> bool:
        """Check if position differs significantly from another"""
        if not other:
            return True
        return (abs(self.x - other.x) > threshold or
                abs(self.y - other.y) > threshold or
                abs(self.width - other.width) > threshold or
                abs(self.height - other.height) > threshold)


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    updates_per_second: float = 0.0
    average_latency_ms: float = 0.0
    missed_updates: int = 0
    total_updates: int = 0
    last_reset: float = 0.0
    
    def reset(self):
        """Reset metrics"""
        self.updates_per_second = 0.0
        self.average_latency_ms = 0.0
        self.missed_updates = 0
        self.total_updates = 0
        self.last_reset = time.time()


class PositionSyncEngine:
    """
    High-performance position synchronization engine.
    Tracks container position and updates LibreOffice window accordingly.
    """
    
    def __init__(self, update_callback: Optional[Callable[[int, int, int, int], None]] = None):
        """
        Initialize sync engine.
        
        Args:
            update_callback: Function to call with position updates (x, y, width, height)
        """
        self.platform = platform.system()
        self.update_callback = update_callback
        
        # Threading
        self._sync_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._position_queue = Queue(maxsize=10)
        
        # State
        self._current_position: Optional[PositionUpdate] = None
        self._last_applied_position: Optional[PositionUpdate] = None
        self._window_id: Optional[int] = None
        
        # Performance tuning
        self.min_fps = 20  # Minimum updates per second
        self.max_fps = 60  # Maximum updates per second
        self.current_fps = 30  # Current target FPS
        self._adaptive_fps = True
        
        # Smoothing
        self._enable_smoothing = True
        self._smoothing_factor = 0.3  # 0-1, higher = more smoothing
        
        # Prediction
        self._enable_prediction = True
        self._velocity_x = 0.0
        self._velocity_y = 0.0
        
        # Metrics
        self.metrics = PerformanceMetrics()
        
    def start(self, window_id: int) -> None:
        """
        Start position synchronization.
        
        Args:
            window_id: LibreOffice window ID to track
        """
        if self._sync_thread and self._sync_thread.is_alive():
            logger.warning("Sync engine already running")
            return
            
        logger.info(f"Starting position sync for window {window_id}")
        self._window_id = window_id
        self._stop_event.clear()
        self.metrics.reset()
        
        self._sync_thread = threading.Thread(
            target=self._sync_loop,
            name="PositionSyncEngine",
            daemon=True
        )
        self._sync_thread.start()
        
    def stop(self) -> None:
        """Stop position synchronization."""
        logger.info("Stopping position sync")
        self._stop_event.set()
        
        if self._sync_thread:
            self._sync_thread.join(timeout=2.0)
            self._sync_thread = None
            
        # Clear queue
        while not self._position_queue.empty():
            try:
                self._position_queue.get_nowait()
            except Empty:
                break
                
    def update_position(self, x: int, y: int, width: int, height: int) -> None:
        """
        Queue a position update.
        
        Args:
            x: X coordinate
            y: Y coordinate
            width: Width
            height: Height
        """
        update = PositionUpdate(
            x=x, y=y, width=width, height=height,
            timestamp=time.time()
        )
        
        # Drop old updates if queue is full
        if self._position_queue.full():
            try:
                self._position_queue.get_nowait()
                self.metrics.missed_updates += 1
            except Empty:
                pass
                
        try:
            self._position_queue.put_nowait(update)
        except:
            logger.debug("Failed to queue position update")
            
    def _sync_loop(self) -> None:
        """Main synchronization loop."""
        logger.info("Position sync loop started")
        frame_time = 1.0 / self.current_fps
        next_frame_time = time.time()
        
        while not self._stop_event.is_set():
            try:
                # Adaptive timing
                current_time = time.time()
                if current_time >= next_frame_time:
                    self._process_updates()
                    
                    # Adjust FPS if needed
                    if self._adaptive_fps:
                        self._adjust_fps()
                        
                    # Calculate next frame time
                    frame_time = 1.0 / self.current_fps
                    next_frame_time = current_time + frame_time
                    
                # Small sleep to prevent CPU spinning
                sleep_time = max(0.001, next_frame_time - time.time())
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                time.sleep(0.1)
                
        logger.info("Position sync loop stopped")
        
    def _process_updates(self) -> None:
        """Process queued position updates."""
        # Get latest position from queue
        latest_update = None
        updates_processed = 0
        
        while not self._position_queue.empty():
            try:
                latest_update = self._position_queue.get_nowait()
                updates_processed += 1
            except Empty:
                break
                
        if not latest_update:
            return
            
        # Update metrics
        self.metrics.total_updates += updates_processed
        
        # Apply smoothing if enabled
        if self._enable_smoothing and self._current_position:
            latest_update = self._apply_smoothing(latest_update)
            
        # Apply prediction if enabled
        if self._enable_prediction:
            latest_update = self._apply_prediction(latest_update)
            
        # Check if position changed significantly
        if latest_update.differs_from(self._last_applied_position):
            # Apply position update
            if self._apply_position_update(latest_update):
                self._last_applied_position = latest_update
                
        self._current_position = latest_update
        
    def _apply_smoothing(self, update: PositionUpdate) -> PositionUpdate:
        """
        Apply position smoothing.
        
        Args:
            update: New position update
            
        Returns:
            Smoothed position update
        """
        if not self._current_position:
            return update
            
        factor = self._smoothing_factor
        smoothed = PositionUpdate(
            x=int(self._current_position.x * factor + update.x * (1 - factor)),
            y=int(self._current_position.y * factor + update.y * (1 - factor)),
            width=int(self._current_position.width * factor + update.width * (1 - factor)),
            height=int(self._current_position.height * factor + update.height * (1 - factor)),
            timestamp=update.timestamp
        )
        
        return smoothed
        
    def _apply_prediction(self, update: PositionUpdate) -> PositionUpdate:
        """
        Apply movement prediction.
        
        Args:
            update: Current position update
            
        Returns:
            Predicted position update
        """
        if not self._current_position:
            return update
            
        # Calculate velocity
        dt = update.timestamp - self._current_position.timestamp
        if dt > 0:
            new_velocity_x = (update.x - self._current_position.x) / dt
            new_velocity_y = (update.y - self._current_position.y) / dt
            
            # Smooth velocity
            alpha = 0.3
            self._velocity_x = alpha * new_velocity_x + (1 - alpha) * self._velocity_x
            self._velocity_y = alpha * new_velocity_y + (1 - alpha) * self._velocity_y
            
            # Predict next position
            prediction_time = 1.0 / self.current_fps  # Predict one frame ahead
            predicted_x = int(update.x + self._velocity_x * prediction_time)
            predicted_y = int(update.y + self._velocity_y * prediction_time)
            
            return PositionUpdate(
                x=predicted_x,
                y=predicted_y,
                width=update.width,
                height=update.height,
                timestamp=update.timestamp
            )
            
        return update
        
    def _apply_position_update(self, update: PositionUpdate) -> bool:
        """
        Apply position update to window.
        
        Args:
            update: Position update to apply
            
        Returns:
            True if successful
        """
        if not self._window_id:
            return False
            
        start_time = time.time()
        
        if self.platform == "Linux":
            success = self._move_window_linux(update)
        elif self.platform == "Windows":
            success = self._move_window_windows(update)
        else:
            success = False
            
        # Update metrics
        if success:
            latency = (time.time() - start_time) * 1000  # Convert to ms
            self.metrics.average_latency_ms = (
                self.metrics.average_latency_ms * 0.9 + latency * 0.1
            )
            
        # Call update callback if provided
        if success and self.update_callback:
            self.update_callback(update.x, update.y, update.width, update.height)
            
        return success
        
    def _move_window_linux(self, update: PositionUpdate) -> bool:
        """Move window on Linux."""
        try:
            # Use xdotool for moving and resizing
            result = subprocess.run(
                ["xdotool", "windowmove", str(self._window_id),
                 str(update.x), str(update.y)],
                capture_output=True,
                timeout=0.1  # Fast timeout
            )
            
            if result.returncode == 0:
                # Resize window
                result = subprocess.run(
                    ["xdotool", "windowsize", str(self._window_id),
                     str(update.width), str(update.height)],
                    capture_output=True,
                    timeout=0.1
                )
                
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.debug("Window move timed out")
            return False
        except Exception as e:
            logger.debug(f"Failed to move window: {e}")
            return False
            
    def _move_window_windows(self, update: PositionUpdate) -> bool:
        """Move window on Windows."""
        try:
            import win32gui
            
            win32gui.MoveWindow(
                self._window_id,
                update.x, update.y,
                update.width, update.height,
                True  # Repaint
            )
            return True
            
        except Exception as e:
            logger.debug(f"Failed to move window: {e}")
            return False
            
    def _adjust_fps(self) -> None:
        """Adjust FPS based on performance metrics."""
        if self.metrics.average_latency_ms > 50:
            # Reduce FPS if latency is high
            self.current_fps = max(self.min_fps, self.current_fps - 5)
        elif self.metrics.average_latency_ms < 20 and self.metrics.missed_updates < 5:
            # Increase FPS if performance is good
            self.current_fps = min(self.max_fps, self.current_fps + 5)
            
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary of metrics
        """
        elapsed = time.time() - self.metrics.last_reset
        updates_per_second = self.metrics.total_updates / elapsed if elapsed > 0 else 0
        
        return {
            "updates_per_second": updates_per_second,
            "average_latency_ms": self.metrics.average_latency_ms,
            "missed_updates": self.metrics.missed_updates,
            "total_updates": self.metrics.total_updates,
            "current_fps": self.current_fps,
            "smoothing_enabled": self._enable_smoothing,
            "prediction_enabled": self._enable_prediction
        }
        
    def set_smoothing(self, enabled: bool, factor: float = 0.3) -> None:
        """
        Configure position smoothing.
        
        Args:
            enabled: Enable/disable smoothing
            factor: Smoothing factor (0-1)
        """
        self._enable_smoothing = enabled
        self._smoothing_factor = max(0.0, min(1.0, factor))
        logger.info(f"Smoothing {'enabled' if enabled else 'disabled'}, factor: {factor}")
        
    def set_prediction(self, enabled: bool) -> None:
        """
        Configure movement prediction.
        
        Args:
            enabled: Enable/disable prediction
        """
        self._enable_prediction = enabled
        logger.info(f"Prediction {'enabled' if enabled else 'disabled'}")