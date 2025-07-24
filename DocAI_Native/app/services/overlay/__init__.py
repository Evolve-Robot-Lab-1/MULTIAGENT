"""
LibreOffice Overlay Positioning System

This module implements an overlay positioning approach for displaying LibreOffice
within the DocAI Native application. Instead of true embedding (which failed),
this system positions LibreOffice windows to appear embedded.

Components:
- coordinates.py: Container position tracking
- window_tracker.py: LibreOffice window finding
- decorations.py: Window decoration removal
- sync_engine.py: High-performance position synchronization
- manager.py: Main orchestration class
"""

from .manager import LibreOfficeOverlayManager

__all__ = ['LibreOfficeOverlayManager']