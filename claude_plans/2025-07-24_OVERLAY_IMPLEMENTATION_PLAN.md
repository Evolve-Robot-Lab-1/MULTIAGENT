# LibreOffice Overlay Implementation Plan
**Date**: July 24, 2025
**Status**: Ready to Execute
**Approach**: Overlay Positioning (not embedding)

## Why Overlay Instead of Embedding
- All 6 embedding tests failed
- LibreOffice doesn't support true embedding
- Window managers prevent reparenting
- Overlay positioning proven to work

## Implementation Steps
1. Create overlay manager class
2. Implement window tracking
3. Add decoration removal
4. Create position sync system
5. Integrate with PyWebView
6. Add fallback mechanisms

## Key Components

### 1. CoordinateSystem
- Tracks container element position
- Handles browser chrome offsets
- Accounts for zoom levels
- Provides absolute screen coordinates

### 2. WindowTracker
- Finds LibreOffice window by PID
- Multiple search strategies
- Platform-specific implementations
- Verifies window validity

### 3. DecorationRemover
- Removes window title bar and borders
- Multiple methods for compatibility
- Platform-specific approaches
- Makes window appear embedded

### 4. PositionSyncEngine
- High-performance position tracking
- Adaptive FPS (20-60 Hz)
- Position smoothing
- Movement prediction
- Performance metrics

### 5. LibreOfficeOverlayManager
- Orchestrates all components
- Manages LibreOffice process
- Handles state transitions
- Provides clean shutdown

## Testing Strategy
1. Test coordinate calculation
2. Test window finding
3. Test decoration removal
4. Test position synchronization
5. Integration testing

## Success Metrics
- Launch time < 3 seconds
- Position lag < 50ms
- Smooth movement tracking
- Clean process management
- Reliable fallback to HTML