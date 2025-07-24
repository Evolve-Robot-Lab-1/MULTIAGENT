# Phase 2: Native LibreOffice Embedding Plan
**Date**: January 21, 2025  
**Prerequisites**: Phase 1 (LibreOffice UNO Service) must be working  
**Estimated Time**: 3 days

## GOAL: Embed LibreOffice Native Viewer in Central Container

**Target**: Replace HTML conversion with true LibreOffice embedding in `.chat-container` div
**Vision**: Users see actual LibreOffice interface within DocAI Native app
**Benefits**: 
- Full LibreOffice functionality (editing, formatting, etc.)
- Better fidelity than HTML conversion
- Native performance
- Advanced features like track changes, comments

## ARCHITECTURE OVERVIEW

### Current Flow (HTML Conversion)
```
File Selected → UNO Service → Convert to HTML → Display in chat-container
```

### Target Flow (Native Embedding)
```
File Selected → LibreOffice Process → Embed Window → Display in chat-container
```

### Platform-Specific Approaches

#### Linux (X11 Window Embedding)
```
PyWebView Window (X11) → Get Window ID → Launch LibreOffice with parent → Embed via X11
```

#### Windows (Win32 SetParent)  
```
PyWebView Window (HWND) → Launch LibreOffice → Find LibreOffice Window → SetParent to embed
```

#### macOS (NSView - Complex)
```
PyWebView NSWindow → Launch LibreOffice → Fallback to positioned window (embedding limited)
```

## IMPLEMENTATION PLAN

### 2.1: Enhanced Document Embedder Service

#### Current State Analysis
The existing `DocumentEmbedder` classes provide basic separate window launching. We need to enhance them for true embedding.

#### Linux Enhancement (Priority 1)
```python
class LinuxDocumentEmbedder(DocumentEmbedder):
    def embed_document_in_container(self, parent_window, document_path, container_id):
        """True X11 embedding in specified container"""
        
        # Get PyWebView X11 window ID
        x11_window_id = self.get_x11_window_id(parent_window)
        
        # Get container div coordinates via JavaScript
        container_info = parent_window.evaluate_js(f"""
            const container = document.getElementById('{container_id}');
            if (container) {{
                const rect = container.getBoundingClientRect();
                JSON.stringify({{
                    x: rect.left,
                    y: rect.top, 
                    width: rect.width,
                    height: rect.height
                }});
            }}
        """)
        
        if not container_info:
            return self._fallback_separate_window(document_path)
            
        # Launch LibreOffice with embedding parameters
        cmd = [
            'soffice',
            '--nologo',
            '--view',
            '--norestore', 
            f'--geometry={container_info["width"]}x{container_info["height"]}+{container_info["x"]}+{container_info["y"]}',
            document_path
        ]
        
        # For true embedding, need xembed or similar
        if self.supports_xembed():
            cmd.extend([f'--parent-window-id={x11_window_id}'])
            
        process = subprocess.Popen(cmd)
        
        # Monitor and manage embedded window
        self.manage_embedded_window(process, container_info)
        
        return {
            'success': True,
            'mode': 'embedded',
            'pid': process.pid,
            'window_id': x11_window_id,
            'container': container_id
        }
```

#### Advanced X11 Window Management
```python
def manage_embedded_window(self, process, container_info):
    """Manage embedded LibreOffice window"""
    
    # Wait for LibreOffice window to appear
    lo_window_id = self.wait_for_libreoffice_window(process)
    
    if lo_window_id:
        # Use xwininfo and xdotool to manage window
        self.resize_embedded_window(lo_window_id, container_info)
        self.hide_libreoffice_decorations(lo_window_id)
        
def wait_for_libreoffice_window(self, process, timeout=10):
    """Wait for LibreOffice window to appear and return its ID"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Find LibreOffice windows
            result = subprocess.run([
                'xdotool', 'search', '--onlyvisible', '--class', 'libreoffice'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                # Return newest window (likely ours)
                return window_ids[-1] 
                
        except Exception as e:
            logger.debug(f"Waiting for LibreOffice window: {e}")
            
        time.sleep(0.5)
    
    return None

def resize_embedded_window(self, window_id, container_info):
    """Resize and position LibreOffice window"""
    subprocess.run([
        'xdotool', 'windowsize', window_id, 
        str(container_info['width']), str(container_info['height'])
    ])
    
    subprocess.run([
        'xdotool', 'windowmove', window_id,
        str(container_info['x']), str(container_info['y'])
    ])
```

#### Windows Enhancement
```python
class WindowsDocumentEmbedder(DocumentEmbedder):
    def embed_document_in_container(self, parent_window, document_path, container_id):
        """Win32 SetParent embedding"""
        
        try:
            import win32gui, win32con
            
            # Get PyWebView HWND
            parent_hwnd = self.get_pywebview_hwnd(parent_window)
            
            # Launch LibreOffice
            process = subprocess.Popen([
                str(self._find_soffice_exe()),
                '--view',
                '--nologo',
                document_path
            ])
            
            # Wait for LibreOffice window
            lo_hwnd = self.wait_for_libreoffice_hwnd(process)
            
            if lo_hwnd:
                # Remove window decorations
                style = win32gui.GetWindowLong(lo_hwnd, win32con.GWL_STYLE)
                style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
                win32gui.SetWindowLong(lo_hwnd, win32con.GWL_STYLE, style)
                
                # Embed window
                win32gui.SetParent(lo_hwnd, parent_hwnd)
                
                # Position within container
                self.position_in_container(lo_hwnd, container_id, parent_window)
                
                return {
                    'success': True,
                    'mode': 'embedded',
                    'pid': process.pid,
                    'hwnd': lo_hwnd
                }
                
        except Exception as e:
            logger.error(f"Win32 embedding failed: {e}")
            return self._fallback_separate_window(document_path)
```

### 2.2: Frontend Integration

#### JavaScript Container Management
```javascript
// Add to native-integration.js or new embedding-integration.js

class DocumentEmbeddingManager {
    constructor() {
        this.embeddedDocuments = new Map();
        this.currentContainer = null;
    }
    
    async embedDocument(filePath, containerId = 'chat-container') {
        console.log(`[Embedding] Embedding ${filePath} in ${containerId}`);
        
        // Prepare container for embedding
        this.prepareContainer(containerId);
        
        // Call native API
        try {
            const result = await pywebview.api.embedDocumentInContainer(filePath, containerId);
            
            if (result.success) {
                this.embeddedDocuments.set(filePath, {
                    containerId,
                    pid: result.pid,
                    mode: result.mode,
                    windowInfo: result
                });
                
                // Setup container event handlers
                this.setupContainerHandlers(containerId);
                
                // Add overlay controls
                this.addEmbeddingControls(containerId);
                
                return result;
            } else {
                throw new Error(result.error);
            }
            
        } catch (error) {
            console.error('[Embedding] Failed:', error);
            // Fallback to HTML view
            return this.fallbackToHtmlView(filePath, containerId);
        }
    }
    
    prepareContainer(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container ${containerId} not found`);
        }
        
        // Clear existing content
        container.innerHTML = '';
        
        // Add embedding class
        container.classList.add('document-embedding-container');
        
        // Set appropriate styles
        container.style.position = 'relative';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.overflow = 'hidden';
        
        // Add loading indicator
        const loading = document.createElement('div');
        loading.className = 'embedding-loading';
        loading.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Loading LibreOffice viewer...</p>
        `;
        container.appendChild(loading);
    }
    
    setupContainerHandlers(containerId) {
        const container = document.getElementById(containerId);
        
        // Handle resize events
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                this.handleContainerResize(containerId, entry.contentRect);
            }
        });
        resizeObserver.observe(container);
        
        // Handle focus events for embedded document
        container.addEventListener('click', () => {
            this.focusEmbeddedDocument(containerId);
        });
    }
    
    addEmbeddingControls(containerId) {
        const container = document.getElementById(containerId);
        
        // Create overlay controls
        const controls = document.createElement('div');
        controls.className = 'embedding-controls';
        controls.innerHTML = `
            <div class="control-bar">
                <button onclick="embeddingManager.toggleFullscreen('${containerId}')" title="Toggle Fullscreen">
                    <i class="fas fa-expand"></i>
                </button>
                <button onclick="embeddingManager.extractSelection()" title="Get Selected Text">
                    <i class="fas fa-quote-right"></i>
                </button>
                <button onclick="embeddingManager.closeDocument('${containerId}')" title="Close Document">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        container.appendChild(controls);
    }
    
    async handleContainerResize(containerId, rect) {
        // Notify native API of size change
        try {
            await pywebview.api.resizeEmbeddedDocument(rect.width, rect.height);
        } catch (error) {
            console.error('[Embedding] Resize failed:', error);
        }
    }
    
    async extractSelection() {
        try {
            const selectedText = await pywebview.api.extractTextSelection();
            if (selectedText) {
                // Send to AI chat
                this.sendToAIChat(selectedText);
            }
        } catch (error) {
            console.error('[Embedding] Text extraction failed:', error);
        }
    }
    
    sendToAIChat(text) {
        const chatInput = document.getElementById('userInput');
        if (chatInput) {
            chatInput.value = `Explain this: "${text}"`;
            chatInput.focus();
        }
    }
}

// Global instance
window.embeddingManager = new DocumentEmbeddingManager();
```

#### Native API Extensions
```python
# Add to SimpleNativeAPI class

def embedDocumentInContainer(self, filePath, containerId="chat-container"):
    """Embed LibreOffice document in specified container"""
    logger.info(f"embedDocumentInContainer called: {filePath} in {containerId}")
    
    try:
        if not self.window:
            return {"success": False, "error": "Window reference not set"}
        
        # Get enhanced document embedder
        from app.services.document_embedder import get_document_embedder
        embedder = get_document_embedder()
        
        # Use enhanced embedding method
        if hasattr(embedder, 'embed_document_in_container'):
            result = embedder.embed_document_in_container(
                self.window, filePath, containerId
            )
        else:
            # Fallback to basic embedding
            result = embedder.embed_document(self.window, filePath)
            
        logger.info(f"Document embedding result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in embedDocumentInContainer: {e}")
        return {"success": False, "error": str(e)}

def resizeEmbeddedDocument(self, width, height):
    """Resize embedded LibreOffice document"""
    try:
        # Platform-specific resize logic
        embedder = get_document_embedder()
        if hasattr(embedder, 'resize_embedded_document'):
            return embedder.resize_embedded_document(width, height)
        return {"success": True, "message": "Resize not supported"}
        
    except Exception as e:
        logger.error(f"Error resizing embedded document: {e}")
        return {"success": False, "error": str(e)}

def extractTextSelection(self):
    """Extract selected text from embedded LibreOffice document"""
    try:
        # This requires UNO bridge integration
        from app.services.uno_bridge import get_uno_bridge
        bridge = get_uno_bridge()
        
        if bridge and hasattr(bridge, 'get_selection'):
            return bridge.get_selection()
            
        return {"success": False, "error": "Text selection not available"}
        
    except Exception as e:
        logger.error(f"Error extracting text selection: {e}")
        return {"success": False, "error": str(e)}
```

### 2.3: CSS Enhancements for Embedding

```css
/* Add to stylenew.css */

.document-embedding-container {
    position: relative;
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
}

.embedding-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    z-index: 1000;
}

.embedding-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 1001;
    opacity: 0;
    transition: opacity 0.3s;
}

.document-embedding-container:hover .embedding-controls {
    opacity: 1;
}

.control-bar {
    background: rgba(0, 0, 0, 0.7);
    border-radius: 4px;
    padding: 5px;
    display: flex;
    gap: 5px;
}

.control-bar button {
    background: transparent;
    border: none;
    color: white;
    padding: 8px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.control-bar button:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* Fullscreen mode */
.document-embedding-container.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 10000;
    border-radius: 0;
}
```

## TESTING PLAN

### Unit Tests
```python
class TestDocumentEmbedding(unittest.TestCase):
    def test_container_preparation(self):
        """Test container is properly prepared for embedding"""
        
    def test_libreoffice_window_detection(self):
        """Test LibreOffice window can be found and managed"""
        
    def test_embedding_fallback(self):
        """Test fallback to separate window when embedding fails"""
        
    def test_text_selection_extraction(self):
        """Test text selection can be extracted from embedded document"""
```

### Integration Tests
- Test embedding on Linux (X11)
- Test embedding on Windows (Win32)
- Test fallback behavior on macOS
- Test container resizing
- Test fullscreen toggle
- Test text selection for AI integration

## SUCCESS CRITERIA

✅ **LibreOffice Embedded**: Document appears inside central container, not separate window  
✅ **Responsive**: Embedded viewer resizes with container  
✅ **Interactive**: Can scroll, zoom, edit within embedded viewer  
✅ **Text Selection**: Can select text and send to AI chat  
✅ **Controls**: Overlay controls work (fullscreen, close, etc.)  
✅ **Stable**: No crashes or memory leaks with multiple documents  
✅ **Fallback**: Gracefully falls back to separate window if embedding fails  

## ROLLBACK PLAN

If embedding doesn't work reliably:
1. Keep enhanced document embedder for separate window mode
2. Fall back to HTML conversion (Phase 1)
3. Document specific embedding issues for future iteration
4. Focus on making separate window mode work well

This plan provides true native LibreOffice integration while maintaining fallback options for reliability.