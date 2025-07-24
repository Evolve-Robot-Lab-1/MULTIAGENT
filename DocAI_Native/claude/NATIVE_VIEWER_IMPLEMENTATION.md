# Native LibreOffice Viewer Implementation

## Overview

This implementation adds native LibreOffice document viewing capability to DocAI Native. Instead of converting documents to HTML, documents are displayed in a separate LibreOffice window that appears to be integrated with the main application.

## Architecture

### Components

1. **Window Manager Service** (`app/services/window_manager.py`)
   - Manages LibreOffice window lifecycle
   - Handles platform-specific window positioning
   - Tracks active document windows

2. **API Routes** (`app/api/v1.py`)
   - `/api/v1/view_document_native/<filename>` - Opens document in native viewer
   - `/api/v1/document/<doc_id>/zoom` - Controls zoom level
   - `/api/v1/document/<doc_id>/page` - Navigate to specific page
   - `/api/v1/document/<doc_id>/close` - Close document window
   - `/api/v1/document/<doc_id>/info` - Get document information

3. **Frontend Integration** (`frontend/static/js/viewer-mode.js`)
   - ViewerModeManager handles switching between HTML and native modes
   - Makes API calls to open documents in native viewer
   - Provides UI controls for zoom and page navigation

4. **UNO Bridge Enhancement** (`uno_bridge.py`)
   - Already implemented document loading via UNO API
   - Extracts window handles for positioning
   - Manages LibreOffice process lifecycle

## How It Works

1. User clicks on a document with viewer mode set to "Native"
2. Frontend sends request to `/api/v1/view_document_native/<filename>` with window position info
3. Backend:
   - Uses UNO bridge to load document in LibreOffice
   - Extracts window handle (X11 ID on Linux)
   - Positions window relative to main application window
   - Returns document ID and control endpoints
4. Frontend displays control panel with zoom/navigation buttons
5. User can control document through API calls

## Platform Support

### Linux (Implemented)
- Uses X11 window IDs
- Positioning via `xdotool` or python-xlib
- Full window manipulation support

### Windows (Planned)
- Will use Win32 API for window handles
- SetParent() for embedding
- DWM composition handling

### macOS (Planned)
- NSWindow manipulation via PyObjC
- Window collection behavior

## Testing

### Prerequisites
1. LibreOffice installed (`sudo apt-get install libreoffice`)
2. Python UNO module (`sudo apt-get install python3-uno`)
3. xdotool (optional, for better Linux positioning)

### Running Tests

1. **Start the application**:
   ```bash
   python main.py
   ```

2. **Test via UI**:
   - Upload or select a document
   - Click the viewer mode toggle to switch to "Native View"
   - Click on a document to open it

3. **Test via script**:
   ```bash
   python test_native_viewer.py --file test.pdf
   ```

### Expected Behavior

1. Document opens in separate LibreOffice window
2. Window is positioned near the main application window
3. Zoom controls change document zoom level
4. Page navigation works for multi-page documents
5. Close button closes both LibreOffice window and UI

## Configuration

The implementation respects existing configuration:
- `LIBREOFFICE_PATH` - Path to LibreOffice executable
- `UNO_PORT` - Port for UNO communication
- `ALLOWED_EXTENSIONS` - Supported file types

## Error Handling

1. **LibreOffice not available**: Falls back to HTML view
2. **UNO connection fails**: Retries with exponential backoff
3. **Window positioning fails**: Document still opens, just not positioned
4. **Document load fails**: Shows error with option to try HTML view

## Security Considerations

1. Documents open in separate process (LibreOffice)
2. No direct file system access from frontend
3. Validates file paths and extensions
4. Sandboxed LibreOffice execution

## Limitations

1. Cannot embed LibreOffice window directly in web view
2. Window positioning may vary by window manager
3. Some LibreOffice UI elements remain visible
4. Performance depends on LibreOffice startup time

## Future Enhancements

1. **Window State Synchronization**: Keep windows in sync during move/resize
2. **Preloading**: Start LibreOffice in background for faster opens
3. **Multi-document**: Support multiple documents open simultaneously
4. **Edit Mode**: Enable document editing in native viewer
5. **Better Integration**: Hide more LibreOffice UI elements

## Troubleshooting

### "Window manager not initialized"
- Check that UNO bridge started successfully
- Verify LibreOffice is installed
- Check logs for UNO connection errors

### Document doesn't appear
- Check if LibreOffice window is behind main window
- Look in taskbar for LibreOffice icon
- Verify file path is correct

### Position not working
- Install xdotool: `sudo apt-get install xdotool`
- Check X11 permissions
- Try different window manager

### Performance issues
- First document load is slow (LibreOffice startup)
- Subsequent loads are faster
- Consider keeping LibreOffice running