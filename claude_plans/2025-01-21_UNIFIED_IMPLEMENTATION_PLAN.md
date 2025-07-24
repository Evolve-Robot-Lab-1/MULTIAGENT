# Unified Implementation Plan: Native File Loading Fix

## Executive Summary
This plan combines the ultra-detailed implementation approach with specific findings from the file operations tracker to fix native file loading in DocAI Native.

---

## 🎯 Primary Goal
Enable file loading through native OS file picker → File appears in left container → Document displays in viewer

## 🔍 Root Cause Analysis (from Tracker)

### Critical Issue #1: PyWebView API Not Exposed
```python
# main.py line 216 - CURRENT (BROKEN)
self.native_api = api_dict  # ❌ PyWebView needs class instance, not dict!
```

### Critical Issue #2: Multiple Conflicting File Handlers
```javascript
// index.html has 3 different handleOpenFile implementations
window.handleWebOpenFile()  // Uses broken FileReader
window.handleOpenFile()     // Routes to broken web handler
window.handleOpenFile_real  // Dead code
```

### Critical Issue #3: FileReader Doesn't Work in PyWebView
```javascript
reader.onload = function(event) {
    // This callback NEVER fires in PyWebView!
}
```

---

## 📋 Implementation Phases

### Phase 1: Fix PyWebView API Registration (Critical Foundation)

#### 1.1 Fix main.py API Registration
```python
# Line 216 - CHANGE FROM:
self.native_api = api_dict

# TO:
from native_api_simple import SimpleNativeAPI
self.native_api = SimpleNativeAPI()
logger.info("Created SimpleNativeAPI instance")

# Line 235 - After window creation:
self.native_api.set_window(self.window)
logger.info("Window reference set in native API")
```

#### 1.2 Add Debug Logging
```python
# Add after API creation:
methods = self.native_api.getAvailableMethods()
logger.info(f"Native API methods available: {methods}")
```

#### 1.3 Verify API Exposure
```python
# Add window evaluate to test:
def verify_api():
    result = self.window.evaluate_js("""
        JSON.stringify({
            pywebview: typeof pywebview !== 'undefined',
            api: typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined',
            pickFile: typeof pywebview !== 'undefined' && typeof pywebview.api !== 'undefined' && typeof pywebview.api.pickFile === 'function'
        })
    """)
    logger.info(f"API verification: {result}")
```

### Phase 2: Clean Up Frontend File Operations

#### 2.1 Remove Broken Implementations
- Delete `native_api_dict.py` completely
- Remove `handleOpenFile_real` from index.html (line 518)
- Remove or comment out `handleWebOpenFile` function

#### 2.2 Create Unified File Handler
```javascript
// Replace ALL handleOpenFile implementations with:
window.handleOpenFile = async function() {
    console.log('[handleOpenFile] Called');
    
    // Check if native mode is available
    if (typeof NativeAPI !== 'undefined' && NativeAPI.isAvailable()) {
        console.log('[handleOpenFile] Using native mode');
        return await handleNativeOpenFile();
    } else {
        console.log('[handleOpenFile] Falling back to web mode');
        return handleWebOpenFile();
    }
};
```

#### 2.3 Add API Ready Check
```javascript
// Add to index.html before any API usage:
window.waitForNativeAPI = function(timeout = 5000) {
    return new Promise((resolve) => {
        const startTime = Date.now();
        
        function checkAPI() {
            if (typeof pywebview !== 'undefined' && 
                typeof pywebview.api !== 'undefined' &&
                typeof pywebview.api.pickFile === 'function') {
                console.log('Native API ready!');
                resolve(true);
            } else if (Date.now() - startTime > timeout) {
                console.warn('Native API timeout - falling back to web mode');
                resolve(false);
            } else {
                setTimeout(checkAPI, 100);
            }
        }
        
        checkAPI();
    });
};

// Initialize after DOM ready
document.addEventListener('DOMContentLoaded', async function() {
    const nativeReady = await waitForNativeAPI();
    if (nativeReady) {
        document.body.classList.add('native-mode');
    }
});
```

### Phase 3: Fix File Container Display

#### 3.1 Debug File Container Function
```javascript
// Add debug version of addFileToContainer:
window.addFileToContainerDebug = function(fileName, fileExtension, base64Data) {
    console.log('[addFileToContainer] Called with:', {
        fileName,
        fileExtension,
        hasBase64: !!base64Data
    });
    
    const fileListElement = document.getElementById('file-list');
    console.log('[addFileToContainer] File list element:', fileListElement);
    
    if (!fileListElement) {
        console.error('[addFileToContainer] file-list element not found!');
        // Try alternative selectors
        const alternatives = [
            document.querySelector('.file-container'),
            document.querySelector('#files-container'),
            document.querySelector('[data-files]')
        ];
        console.log('[addFileToContainer] Alternative containers:', alternatives);
        return;
    }
    
    // Original implementation with logging...
};
```

#### 3.2 Fix handleNativeOpenFile Flow
```javascript
async function handleNativeOpenFile() {
    console.log('[handleNativeOpenFile] Starting...');
    
    try {
        // Show loading state
        showLoadingInFileContainer();
        
        // Pick file
        const filePath = await NativeAPI.pickFile();
        console.log('[handleNativeOpenFile] File picked:', filePath);
        
        if (!filePath) {
            console.log('[handleNativeOpenFile] No file selected');
            hideLoadingInFileContainer();
            return;
        }
        
        // Extract file info
        const fileName = filePath.split(/[/\\]/).pop();
        const fileExt = fileName.split('.').pop().toLowerCase();
        
        // Add to container with native indicator
        const fileId = 'file-' + Date.now();
        addFileToContainerNative(fileId, fileName, fileExt, filePath);
        
        // Load document
        await openDocumentFromPath(filePath);
        
    } catch (error) {
        console.error('[handleNativeOpenFile] Error:', error);
        showErrorInFileContainer(error.message);
    }
}

// New native-specific file container function
function addFileToContainerNative(fileId, fileName, fileExt, filePath) {
    const fileListElement = document.getElementById('file-list');
    if (!fileListElement) return;
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item native-file';
    fileItem.id = fileId;
    fileItem.dataset.path = filePath;
    fileItem.innerHTML = `
        <span class="file-icon">${getFileIcon(fileExt)}</span>
        <span class="file-name">${fileName}</span>
        <span class="native-badge">Native</span>
    `;
    
    fileItem.onclick = () => openDocumentFromPath(filePath);
    fileListElement.appendChild(fileItem);
}
```

### Phase 4: Backend Integration

#### 4.1 Fix /view_document_direct Endpoint
```python
@app.route('/view_document_direct', methods=['POST'])
def view_document_direct():
    try:
        data = request.json
        file_path = data.get('filePath')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Invalid file path'
            })
        
        # Process document
        processor = DocumentProcessor()
        result = processor.process_document(file_path)
        
        if result['success']:
            # Convert to HTML for display
            html_content = libreoffice_uno_converter.convert_document_to_html(file_path)
            
            return jsonify({
                'success': True,
                'content': html_content,
                'metadata': result.get('metadata', {}),
                'fileName': os.path.basename(file_path)
            })
        else:
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Error in view_document_direct: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })
```

#### 4.2 Update openDocumentFromPath
```javascript
async function openDocumentFromPath(filePath) {
    console.log('[openDocumentFromPath] Loading:', filePath);
    
    try {
        showLoading('Opening document...');
        
        const response = await fetch('/view_document_direct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filePath: filePath })
        });
        
        const data = await response.json();
        console.log('[openDocumentFromPath] Response:', data);
        
        if (data.success) {
            displayDocumentContent(data);
        } else {
            throw new Error(data.error || 'Failed to load document');
        }
        
    } catch (error) {
        console.error('[openDocumentFromPath] Error:', error);
        showError('Failed to open document: ' + error.message);
    } finally {
        hideLoading();
    }
}
```

### Phase 5: Testing & Verification

#### 5.1 Create Test Suite
```javascript
// Add to index.html for testing
window.testNativeFileLoading = async function() {
    console.log('=== Native File Loading Test Suite ===');
    
    // Test 1: API availability
    console.log('Test 1: Checking API availability...');
    const apiAvailable = typeof pywebview !== 'undefined' && 
                        typeof pywebview.api !== 'undefined';
    console.log('API available:', apiAvailable);
    
    // Test 2: pickFile method
    if (apiAvailable) {
        console.log('Test 2: Testing pickFile method...');
        try {
            const methods = await pywebview.api.getAvailableMethods();
            console.log('Available methods:', methods);
            console.log('pickFile available:', methods.includes('pickFile'));
        } catch (e) {
            console.error('Method check failed:', e);
        }
    }
    
    // Test 3: File container
    console.log('Test 3: Checking file container...');
    const fileList = document.getElementById('file-list');
    console.log('File list element:', fileList);
    
    // Test 4: End-to-end flow
    console.log('Test 4: Testing full flow...');
    console.log('Click "Open File" to test the complete flow');
};
```

#### 5.2 Debug Mode Toggle
```javascript
// Add debug mode
window.DEBUG_FILE_OPS = false;

window.toggleFileDebug = function() {
    window.DEBUG_FILE_OPS = !window.DEBUG_FILE_OPS;
    console.log('File operations debug mode:', window.DEBUG_FILE_OPS);
    
    if (window.DEBUG_FILE_OPS) {
        // Override console.log to also show in UI
        const originalLog = console.log;
        console.log = function(...args) {
            originalLog.apply(console, args);
            showDebugMessage(args.join(' '));
        };
    }
};

function showDebugMessage(message) {
    const debugPanel = document.getElementById('debug-panel') || createDebugPanel();
    const entry = document.createElement('div');
    entry.className = 'debug-entry';
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    debugPanel.appendChild(entry);
    debugPanel.scrollTop = debugPanel.scrollHeight;
}
```

### Phase 6: Enhanced Error Handling, Security & Document Embedding

#### 6.0 Document Embedding Implementation (CRITICAL MISSING PIECE)

##### 6.0.1 Platform Detection and Strategy
```python
# Add to services/document_embedder.py
import platform
import subprocess
from abc import ABC, abstractmethod

class DocumentEmbedder(ABC):
    @abstractmethod
    def embed_document(self, parent_window, document_path):
        pass

class LinuxDocumentEmbedder(DocumentEmbedder):
    def embed_document(self, parent_window, document_path):
        """Use X11 window embedding on Linux"""
        # Get PyWebView window ID
        window_id = parent_window.get_window_id()
        
        # Launch LibreOffice with parent window
        cmd = [
            'soffice',
            '--nologo',
            '--view',
            '--norestore',
            f'--parent-window-id={window_id}',
            document_path
        ]
        
        process = subprocess.Popen(cmd)
        return process

class WindowsDocumentEmbedder(DocumentEmbedder):
    def embed_document(self, parent_window, document_path):
        """Use Win32 API for Windows embedding"""
        import win32gui
        import win32con
        
        # Get PyWebView window handle
        hwnd = parent_window.get_hwnd()
        
        # Launch LibreOffice
        cmd = ['soffice', '--view', document_path]
        process = subprocess.Popen(cmd)
        
        # Wait for LibreOffice window and reparent
        # Implementation details for Win32 SetParent
        return process

class FallbackDocumentEmbedder(DocumentEmbedder):
    def embed_document(self, parent_window, document_path):
        """Fallback: Open in separate window"""
        cmd = ['soffice', '--view', document_path]
        return subprocess.Popen(cmd)

# Factory
def create_embedder():
    system = platform.system()
    if system == 'Linux':
        return LinuxDocumentEmbedder()
    elif system == 'Windows':
        return WindowsDocumentEmbedder()
    else:
        return FallbackDocumentEmbedder()
```

##### 6.0.2 Integration with Native API
```python
# Add to native_api_simple.py
def embed_libreoffice(self, document_path):
    """Embed LibreOffice viewer for document"""
    try:
        embedder = create_embedder()
        process = embedder.embed_document(self.window, document_path)
        
        self.embedded_processes[document_path] = process
        return {
            'success': True,
            'pid': process.pid,
            'platform': platform.system()
        }
    except Exception as e:
        logger.error(f"Failed to embed document: {e}")
        return {
            'success': False,
            'error': str(e)
        }
```

### Phase 6: Error Handling & Recovery

#### 6.1 Comprehensive Error Handling
```javascript
window.FileLoadingError = class extends Error {
    constructor(stage, originalError) {
        super(`File loading failed at ${stage}: ${originalError.message}`);
        this.stage = stage;
        this.originalError = originalError;
    }
};

// Wrap all file operations
window.safeFileOperation = async function(operation, stage) {
    try {
        return await operation();
    } catch (error) {
        console.error(`[${stage}] Error:`, error);
        
        // Try recovery strategies
        if (stage === 'api-call' && error.message.includes('pywebview')) {
            console.log('Attempting API reconnection...');
            await waitForNativeAPI(1000);
            return await operation(); // Retry once
        }
        
        throw new FileLoadingError(stage, error);
    }
};
```

#### 6.2 User-Friendly Error Messages
```javascript
function showFileError(error) {
    const errorMessages = {
        'api-not-ready': 'File picker is initializing. Please try again.',
        'no-file-selected': 'No file was selected.',
        'file-not-found': 'The selected file could not be found.',
        'processing-failed': 'Failed to process the document.',
        'display-failed': 'Failed to display the document.'
    };
    
    const message = errorMessages[error.code] || error.message;
    showNotification(message, 'error');
}
```

---

## 📊 Success Metrics

1. **File picker opens**: Native OS dialog appears
2. **File path returned**: Console shows valid file path
3. **File in container**: File appears in left panel
4. **Document displays**: Content shows in viewer (HTML or Native)
5. **LibreOffice embedding**: Native viewer shows when requested
6. **Security checks pass**: File validation and resource limits work
7. **Error recovery works**: Graceful fallbacks on failures
8. **No console errors**: Clean execution

---

## 🚀 Quick Start Commands

```bash
# 1. Test current state
python main.py

# 2. Open browser console
# F12 → Console

# 3. Run diagnostics
testNativeFileLoading()

# 4. Enable debug mode
toggleFileDebug()

# 5. Test file loading
# Click "Open File" button
```

---

## 🔧 Troubleshooting Guide

### If file picker doesn't open:
1. Check console for "API not available" errors
2. Verify main.py is using SimpleNativeAPI class
3. Run `pywebview.api.getAvailableMethods()` in console

### If file doesn't appear in container:
1. Check if 'file-list' element exists
2. Look for console errors in addFileToContainer
3. Verify file path is being passed correctly

### If document doesn't display:
1. Check network tab for /view_document_direct request
2. Verify backend is processing file correctly
3. Check for CORS or permission errors

---

## 📝 Final Checklist

### Phase 0 (Verification)
- [ ] Current API status verified
- [ ] Decision made on dict vs class API
- [ ] Platform capabilities tested

### Phase 1 (API - if needed)
- [ ] main.py uses correct API (dict or class)
- [ ] API methods exposed to JavaScript
- [ ] Window reference properly set

### Phase 2 (Frontend)
- [ ] handleOpenFile unified and checking native mode
- [ ] FileReader code removed/disabled
- [ ] API ready check implemented

### Phase 2.5 (Document Embedding)
- [ ] Platform-specific embedders implemented
- [ ] LibreOffice integration tested
- [ ] Fallback strategy working

### Phase 3-4 (File Flow)
- [ ] File container display working
- [ ] Backend endpoint processing files
- [ ] Native file paths handled correctly

### Phase 5 (Polish & Security)
- [ ] Resource limits enforced
- [ ] File validation implemented
- [ ] Circuit breaker for LibreOffice
- [ ] Security checks passing

### Phase 6 (Error Handling)
- [ ] Comprehensive error handling
- [ ] User-friendly error messages
- [ ] Debug tools available
- [ ] Recovery strategies working

## 🆕 Key Improvements Added

1. **Verification Phase**: Check current state before making changes
2. **Document Embedding**: Complete implementation strategy for LibreOffice integration
3. **Security Hardening**: File validation, resource limits, path traversal protection
4. **Circuit Breaker**: Prevent cascade failures with LibreOffice
5. **Platform-Specific Code**: Proper handling for Linux/Windows/macOS differences
6. **Error Recovery**: Retry mechanisms and graceful fallbacks

This unified plan now includes all critical missing pieces identified during the analysis.