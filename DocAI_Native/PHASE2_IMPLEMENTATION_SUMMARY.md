# Phase 2 Implementation Summary: LibreOffice Native Viewer

## Key Finding: True Window Embedding Not Possible

After extensive testing, we've confirmed that **LibreOffice does not support true X11 window embedding** on Linux. The `--parent-window-id` parameter that would enable this functionality is not implemented in LibreOffice.

## What We Learned

1. **X11 Embedding Works** - We successfully embedded Chrome browser using GTK Socket/Plug, proving the concept works
2. **LibreOffice Limitation** - LibreOffice lacks the necessary command-line parameters for embedding
3. **Window Positioning Challenges** - Automatic positioning is unreliable due to:
   - Window manager interference
   - Timing issues with window creation
   - LibreOffice's window behavior

## Viable Approaches for Phase 2

### Option 1: HTML Conversion (Current Implementation)
- **Status**: Already working in DocAI Native
- **Pros**: True integration, text selection works, responsive
- **Cons**: May lose some formatting

### Option 2: Iframe with LibreOffice Online
- **Requirement**: Deploy LibreOffice Online server
- **Pros**: Native rendering, true embedding
- **Cons**: Requires server infrastructure

### Option 3: Side-by-Side Windows
- **Implementation**: Open LibreOffice in separate window
- **Pros**: Full LibreOffice functionality
- **Cons**: Not integrated into UI

### Option 4: Custom Viewer Component
- **Implementation**: Use libraries like `python-uno` to render documents
- **Pros**: Full control over rendering
- **Cons**: Complex implementation

## Recommendation

For Phase 2, I recommend:

1. **Keep current HTML conversion as primary viewer**
2. **Add "Open in LibreOffice" button** for users who need native editing
3. **Consider LibreOffice Online** for future phases if true embedding is required

## Code for "Open in LibreOffice" Feature

```python
def open_in_libreoffice(self, file_path):
    """Open document in external LibreOffice window"""
    try:
        subprocess.Popen([
            'soffice',
            '--nologo',
            '--norestore',
            '--view',
            file_path
        ])
        return {"success": True, "message": "Opened in LibreOffice"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Conclusion

True window embedding of LibreOffice is not technically feasible on Linux without LibreOffice implementing the necessary X11 protocols. The overlay approach creates a poor user experience as the windows are not truly connected.

The best path forward is to enhance the current HTML viewer while providing an option to open documents in a separate LibreOffice window when needed.