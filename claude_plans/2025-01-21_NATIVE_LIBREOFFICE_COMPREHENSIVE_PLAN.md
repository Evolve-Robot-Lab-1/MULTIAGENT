# Comprehensive Native LibreOffice Viewer Implementation Plan
**Date**: January 21, 2025  
**Project**: DocAI Native - Complete LibreOffice Integration

## Executive Summary
Fix LibreOffice startup issues and implement true native LibreOffice embedding in the central container for DOCX viewing with AI integration, as originally envisioned for the DocAI Native application.

## Current State Analysis

### Architecture Overview
- **DocAI Native**: PyWebView-based native application 
- **Current HTML Viewer**: Uses LibreOffice UNO converter to HTML (BROKEN - service won't start)
- **Target**: Native LibreOffice embedding in central container with AI integration
- **Blocking Issue**: "LibreOffice process died: Failed to start LibreOffice server after all attempts"

### Critical Path
1. **LibreOffice UNO Service** → Must work before ANY document functionality
2. **Document Display** → HTML conversion as foundation
3. **Native Embedding** → Direct LibreOffice integration
4. **AI Integration** → Text selection and chat bridge

## Phase 1: Fix LibreOffice UNO Service Issues (Days 1-2) - CRITICAL

### 1.1 Root Cause Analysis
**Problem**: `ImprovedLibreOfficeConverter._start_libreoffice_service()` fails consistently

**Issues Identified**:
- Overly complex LibreOffice startup command
- Aggressive process killing interfering with service
- Rigid port allocation (fixed 2002)
- Long timeout with poor error reporting
- Environment variable conflicts

### 1.2 Surgical Fixes (Minimal Changes for Maximum Impact)

#### Fix 1: Simplify LibreOffice Command
**Current (Complex)**:
```python
cmd = [
    'libreoffice', '--headless', '--invisible', '--nodefault',
    '--nolockcheck', '--nologo', '--norestore', '--nofirststartwizard',
    f'--accept=socket,host=localhost,port={self.port};urp;StarOffice.ServiceManager'
]
```

**New (Minimal)**:
```python
cmd = [
    'soffice',  # More reliable than 'libreoffice'
    '--headless',
    '--nologo', 
    f'--accept=socket,host=localhost,port={self.port};urp;'
]
```

#### Fix 2: Skip Process Killing
Comment out `self._kill_existing_libreoffice()` to prevent interference with existing processes.

#### Fix 3: Better Port Management
```python
def _find_free_port(self):
    """Enhanced port finding with wider range"""
    for port in range(2002, 2020):  # Expanded range
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None  # Let OS assign port
```

#### Fix 4: Faster Startup Detection
```python
# Reduce from 30 seconds to 5 seconds
for i in range(25):  # 5 seconds / 0.2s intervals
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        sock.connect(('localhost', self.port))
        sock.close()
        return True
    except socket.error:
        time.sleep(0.2)
```

#### Fix 5: Enhanced Error Logging
```python
# Log exact command and output
logger.error(f"LibreOffice command: {' '.join(cmd)}")
if self.lo_process.poll() is not None:
    stdout, stderr = self.lo_process.communicate()
    logger.error(f"LibreOffice stdout: {stdout.decode()}")
    logger.error(f"LibreOffice stderr: {stderr.decode()}")
    logger.error(f"Exit code: {self.lo_process.returncode}")
```

### 1.3 Testing Protocol
1. Test with one document: `python3 -c "from app.services.libreoffice_uno_converter_improved import render_document_with_uno_images; print(render_document_with_uno_images('/path/to/test.docx'))"`
2. Verify no "process died" error
3. Confirm HTML output generated

## Phase 2: Native LibreOffice Embedding Architecture (Days 3-5)

### 2.1 Central Container Integration
**Target**: Embed LibreOffice directly in `.chat-container` div
**Approach**: Platform-specific window embedding using enhanced document embedder

### 2.2 Platform-Specific Embedding

#### Linux (X11 Embedding)
```python
def embed_document_x11(self, parent_window, document_path):
    # Get PyWebView window ID
    window_id = self.get_x11_window_id(parent_window)
    
    # Launch LibreOffice with embedding
    cmd = [
        'soffice',
        '--nologo',
        '--view', 
        '--norestore',
        f'--parent-window-id={window_id}',
        document_path
    ]
```

#### Windows (Win32 Embedding)
```python
def embed_document_win32(self, parent_window, document_path):
    import win32gui, win32con
    
    # Get PyWebView HWND
    hwnd = parent_window.get_hwnd()
    
    # Launch LibreOffice and reparent window
    process = subprocess.Popen(['soffice', '--view', document_path])
    
    # Find LibreOffice window and reparent
    lo_hwnd = self.find_libreoffice_window(document_path)
    win32gui.SetParent(lo_hwnd, hwnd)
```

### 2.3 Enhanced Native API Methods
```python
# Add to SimpleNativeAPI
def embedDocumentInContainer(self, filePath, containerId="chat-container"):
    """Embed LibreOffice document in specified container"""
    
def resizeEmbeddedDocument(self, width, height):
    """Resize embedded document viewer"""
    
def extractTextSelection(self):
    """Get selected text from LibreOffice for AI integration"""
    
def toggleDocumentFullscreen(self):
    """Toggle fullscreen mode for embedded document"""
```

## Phase 3: Document-to-AI Workflow (Days 6-7)

### 3.1 Text Selection & Extraction
```python
# UNO-based text selection
def get_selected_text(self, doc_id):
    """Extract selected text from LibreOffice document"""
    doc = self.loaded_documents[doc_id]
    selection = doc.controller.getSelection()
    return selection.getString()
```

### 3.2 AI Chat Integration
```javascript
// Frontend integration
function sendSelectionToAI() {
    const selectedText = await pywebview.api.extractTextSelection();
    if (selectedText) {
        document.getElementById('userInput').value = `Explain this: "${selectedText}"`;
        // Send to AI chat
    }
}
```

### 3.3 Context Menu Integration
```javascript
// Add context menu for text selection
document.addEventListener('contextmenu', function(e) {
    if (isInEmbeddedDocument(e.target)) {
        showDocumentContextMenu(e.pageX, e.pageY);
    }
});
```

## Phase 4: Enhanced File Operations (Day 8)

### 4.1 Fix Current File Display Issues
Based on SESSION_STATE_END.md findings:
- Fix FileReader issues in PyWebView
- Resolve file container display problems
- Implement proper error feedback

### 4.2 Multi-Format Support
- **DOCX**: Primary native LibreOffice embedding
- **PDF**: LibreOffice or embedded PDF viewer  
- **ODT**: Native LibreOffice support
- **TXT/MD**: HTML fallback with syntax highlighting

## Phase 5: Advanced Features & Polish (Days 9-10)

### 5.1 Document Management
- Multiple document tabs in central container
- Document comparison mode
- Auto-save functionality
- Version history integration

### 5.2 Performance Optimization
- Lazy loading for large documents
- Memory management for embedded viewers
- Background document processing
- Intelligent caching

### 5.3 User Experience Enhancements
- Loading states and progress indicators
- Smooth transitions between view modes
- Keyboard shortcuts for navigation
- Full accessibility support

## Phase 6: Error Handling & Fallbacks (Day 11)

### 6.1 Comprehensive Fallback Chain
1. **Primary**: Native LibreOffice embedding in container
2. **Secondary**: LibreOffice separate window
3. **Tertiary**: HTML conversion via UNO
4. **Fallback**: System default application

### 6.2 Error Recovery Systems
```python
class LibreOfficeHealthMonitor:
    """Monitors and recovers LibreOffice service health"""
    
    def __init__(self):
        self.health_check_interval = 30
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
    
    def monitor_health(self):
        """Background health monitoring thread"""
        
    def recover_service(self):
        """Automatic service recovery"""
```

## Implementation Strategy

### Critical Path Dependencies
1. **LibreOffice Service** → Must be 100% stable before any embedding
2. **Document Embedder** → Platform-specific implementation
3. **Container Integration** → UI modifications for embedded viewer
4. **AI Integration** → Text selection and chat bridge

### Success Metrics
- LibreOffice UNO service: 99% uptime
- Document load time: <3 seconds
- Memory usage: <200MB per document
- Text selection accuracy: >95%
- Cross-platform compatibility: Linux, Windows, macOS

### Risk Mitigation
- **Primary**: Maintain HTML conversion as always-available fallback
- **Platform Issues**: Graceful degradation to separate window mode
- **Performance**: Resource limits and cleanup procedures
- **User Experience**: Clear error messages and recovery options

## Testing Strategy

### Unit Testing
```python
class TestLibreOfficeService(unittest.TestCase):
    def test_service_startup(self):
        """Test LibreOffice service starts successfully"""
        
    def test_document_conversion(self):
        """Test document conversion to HTML"""
        
    def test_error_recovery(self):
        """Test service recovery after failures"""
```

### Integration Testing
- End-to-end document loading workflow
- AI integration with text selection
- Multi-platform embedding verification
- Performance testing with large documents

### Platform-Specific Testing
- Linux: X11 embedding and window management
- Windows: Win32 API integration
- macOS: Cocoa/NSView compatibility

## Rollback Plan

### If Implementation Fails
1. **Keep existing HTML conversion** as primary method
2. **Document all blocking issues** for future iterations
3. **Implement partial features** that work reliably
4. **Maintain user workflow** with fallback modes

### Feature Flags
```python
NATIVE_EMBEDDING_FEATURES = {
    'use_native_embedding': False,  # Can disable if issues
    'enable_ai_integration': False, # Independent AI features
    'use_advanced_selection': False # Enhanced text selection
}
```

## Success Definition

The implementation is successful when:
1. ✅ LibreOffice UNO service starts reliably (Phase 1)
2. ✅ Documents display in central container (Phase 2) 
3. ✅ Text selection works with AI chat (Phase 3)
4. ✅ File operations work smoothly (Phase 4)
5. ✅ Advanced features enhance workflow (Phase 5)
6. ✅ Error handling is robust (Phase 6)

## Next Steps After Completion

1. **Collaborative Features**: Multi-user document editing
2. **Advanced AI**: Document analysis and suggestions  
3. **Cloud Integration**: Document synchronization
4. **Mobile Support**: Responsive design for tablets
5. **Plugin System**: Extensible document processing

---

This comprehensive plan delivers the original vision of native LibreOffice integration while maintaining a practical, phased approach that ensures stability at each step.