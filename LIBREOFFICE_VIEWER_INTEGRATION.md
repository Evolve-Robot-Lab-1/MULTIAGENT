# LibreOffice Native Viewer Integration - Feature Specification

## Executive Summary

This document specifies the integration of LibreOffice's native document viewing capabilities into Durga AI's existing document viewer. The goal is to provide pixel-perfect document rendering while maintaining all current functionality.

## Current System Architecture

### Existing Document Viewer
```
┌─────────────────────────────────────────────────────────────┐
│                        Durga AI UI                          │
├──────────────┬─────────────────────┬──────────────────────┤
│  Left Panel  │   Middle Panel      │    Right Panel       │
│  File List   │   Document View     │    AI Chatbot        │
│              │   (HTML Rendered)   │                      │
└──────────────┴─────────────────────┴──────────────────────┘
                          ↑
                          │
                    LibreOffice UNO
                    HTML Conversion
```

### Current Document Flow
1. User uploads document (DOC/DOCX/PDF/TXT)
2. Document stored in `/uploads` directory
3. User clicks file in left panel
4. Backend converts document to HTML using LibreOffice UNO
5. HTML rendered in middle panel with embedded images
6. User can select text for AI interaction

## Proposed Enhancement

### Integration Approach: Embedded LibreOffice Viewer

We will integrate LibreOffice Online (LOOL/Collabora Online) or LibreOffice's native rendering as an iframe-based viewer option.

### Architecture with Native Viewer
```
┌─────────────────────────────────────────────────────────────┐
│                        Durga AI UI                          │
├──────────────┬─────────────────────┬──────────────────────┤
│  Left Panel  │   Middle Panel      │    Right Panel       │
│  File List   │  ┌──────────────┐   │    AI Chatbot        │
│              │  │ View Toggle  │   │                      │
│              │  ├──────────────┤   │                      │
│              │  │   HTML View  │   │                      │
│              │  │      OR      │   │                      │
│              │  │ Native View  │   │                      │
│              │  └──────────────┘   │                      │
└──────────────┴─────────────────────┴──────────────────────┘
```

## Feature Specifications

### 1. Viewer Mode Toggle

**Location**: Document toolbar (top of middle panel)

**UI Design**:
```html
<div class="viewer-mode-container">
    <button class="viewer-toggle-btn" id="viewerModeToggle">
        <span class="toggle-icon">🔄</span>
        <span class="toggle-text">HTML View</span>
    </button>
</div>
```

**Behavior**:
- Default: HTML view (current implementation)
- Click toggles between "HTML View" and "Native View"
- Mode persists across sessions (localStorage)
- Smooth transition animation between modes

### 2. Native Viewer Implementation

**Option A: LibreOffice Online Server**
```javascript
function loadNativeViewer(filename) {
    const viewerFrame = document.createElement('iframe');
    viewerFrame.src = `/loleaflet/${filename}`;
    viewerFrame.className = 'native-viewer-frame';
    viewerFrame.style.width = '100%';
    viewerFrame.style.height = '100%';
    viewerFrame.setAttribute('allowfullscreen', 'true');
    
    document.querySelector('.chat-container').appendChild(viewerFrame);
}
```

**Option B: Direct LibreOffice Rendering**
```python
@app.route('/render_native/<filename>')
def render_native(filename):
    """Render document using LibreOffice in headless mode"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Convert to PDF for native rendering
    pdf_path = convert_to_pdf_headless(filepath)
    
    # Serve PDF with PDF.js or native browser viewer
    return send_file(pdf_path, mimetype='application/pdf')
```

### 3. Feature Preservation Matrix

| Feature | HTML View | Native View | Notes |
|---------|-----------|-------------|-------|
| Document Display | ✅ | ✅ | Full fidelity in native |
| Text Selection | ✅ | ⚠️ | Limited in native |
| Copy/Paste | ✅ | ✅ | Both support |
| AI Integration | ✅ | ⚠️ | Fallback to HTML |
| Edit Mode | ✅ | ❌ | HTML only |
| Zoom | ✅ | ✅ | Native zoom better |
| Search | ✅ | ✅ | Ctrl+F works |
| Mobile | ✅ | ✅ | Responsive |
| Performance | ⚠️ | ✅ | Native faster |
| Offline | ✅ | ⚠️ | Depends on setup |

### 4. Backend API Endpoints

#### New Endpoints
```python
# Native viewer endpoint
GET /api/document/native/<filename>
Response: {
    "viewer_url": "/native/view/...",
    "format": "native",
    "features_available": ["zoom", "print", "download"]
}

# Viewer capability check
GET /api/viewer/capabilities
Response: {
    "native_available": true,
    "formats_supported": ["docx", "doc", "odt", "pdf"],
    "features": {...}
}

# Mode preference
POST /api/user/preferences/viewer-mode
Body: {"mode": "native"}
```

#### Modified Endpoints
```python
# Enhanced document info
GET /api/document/info/<filename>
Response: {
    "filename": "report.docx",
    "size": 1234567,
    "format": "docx",
    "viewer_modes": ["html", "native"],
    "recommended_mode": "native"
}
```

### 5. Frontend Components

#### ViewerModeSelector Component
```javascript
class ViewerModeSelector {
    constructor() {
        this.currentMode = localStorage.getItem('viewerMode') || 'html';
        this.onModeChange = null;
    }
    
    render() {
        return `
            <div class="viewer-mode-selector">
                <label class="mode-switch">
                    <input type="checkbox" 
                           id="viewerModeSwitch"
                           ${this.currentMode === 'native' ? 'checked' : ''}>
                    <span class="slider">
                        <span class="mode-label html">HTML</span>
                        <span class="mode-label native">Native</span>
                    </span>
                </label>
            </div>
        `;
    }
    
    switchMode(mode) {
        this.currentMode = mode;
        localStorage.setItem('viewerMode', mode);
        if (this.onModeChange) {
            this.onModeChange(mode);
        }
    }
}
```

#### DocumentViewer Enhancement
```javascript
class EnhancedDocumentViewer {
    constructor(container) {
        this.container = container;
        this.currentMode = 'html';
        this.currentDocument = null;
    }
    
    async loadDocument(filename, mode = null) {
        mode = mode || this.currentMode;
        
        if (mode === 'native') {
            await this.loadNativeViewer(filename);
        } else {
            await this.loadHTMLViewer(filename);
        }
        
        this.currentDocument = filename;
        this.currentMode = mode;
    }
    
    async loadNativeViewer(filename) {
        // Implementation for native viewer
        const response = await fetch(`/api/document/native/${filename}`);
        const data = await response.json();
        
        this.container.innerHTML = `
            <iframe src="${data.viewer_url}" 
                    class="native-document-viewer"
                    allowfullscreen>
            </iframe>
        `;
    }
    
    async loadHTMLViewer(filename) {
        // Existing HTML viewer implementation
        const response = await fetch(`/view_document/${filename}`);
        const html = await response.text();
        this.container.innerHTML = html;
        
        // Re-initialize features
        this.initializeTextSelection();
        this.initializeContextMenu();
    }
}
```

### 6. Integration Points

#### With AI Chat
```javascript
// Bridge for native viewer limitations
class AIIntegrationBridge {
    constructor(viewer, chatInterface) {
        this.viewer = viewer;
        this.chat = chatInterface;
    }
    
    handleNativeViewerSelection() {
        // Show notification
        this.showNotification(
            'Text selection limited in native view. ' +
            'Switch to HTML view for AI features.'
        );
        
        // Offer quick switch
        this.showQuickSwitch();
    }
    
    showQuickSwitch() {
        const switchBtn = document.createElement('button');
        switchBtn.textContent = 'Switch to HTML View';
        switchBtn.onclick = () => {
            viewerModeSelector.switchMode('html');
            viewer.loadDocument(currentDocument, 'html');
        };
        
        this.chat.addSystemMessage({
            content: 'For AI text analysis, please switch to HTML view.',
            action: switchBtn
        });
    }
}
```

#### With File Browser
```javascript
// Enhance file click handler
function handleFileClick(filename) {
    const mode = viewerModeSelector.currentMode;
    
    // Check file compatibility
    if (mode === 'native' && !isNativeCompatible(filename)) {
        console.warn('File not compatible with native viewer, falling back to HTML');
        viewer.loadDocument(filename, 'html');
    } else {
        viewer.loadDocument(filename, mode);
    }
    
    // Update UI state
    updateDocumentTitle(filename);
    updateViewerModeUI(mode);
}
```

### 7. Configuration

#### Server Configuration
```yaml
# config/libreoffice.yaml
libreoffice:
  mode: "online"  # "online" or "headless"
  online:
    server_url: "http://localhost:9980"
    wopi_url: "http://localhost:5000/wopi"
  headless:
    binary_path: "/usr/bin/libreoffice"
    temp_dir: "/tmp/libreoffice"
  supported_formats:
    - doc
    - docx
    - odt
    - pdf
    - xls
    - xlsx
    - ppt
    - pptx
```

#### Client Configuration
```javascript
// config/viewer.config.js
const VIEWER_CONFIG = {
    defaultMode: 'html',
    enableModeToggle: true,
    nativeViewer: {
        enabled: true,
        fallbackToHtml: true,
        supportedFormats: ['doc', 'docx', 'odt', 'pdf'],
        iframeAttributes: {
            sandbox: 'allow-scripts allow-same-origin allow-forms',
            allowfullscreen: true
        }
    },
    htmlViewer: {
        enableEditing: true,
        enableTextSelection: true,
        preserveFormatting: true
    },
    transitions: {
        duration: 300,
        easing: 'ease-in-out'
    }
};
```

### 8. Error Handling

```javascript
class ViewerErrorHandler {
    static handle(error, context) {
        console.error('Viewer error:', error, context);
        
        const strategies = {
            'native_load_failed': () => {
                this.fallbackToHtml(context.filename);
                this.notifyUser('Native viewer unavailable, using HTML view');
            },
            'libreoffice_not_running': () => {
                this.fallbackToHtml(context.filename);
                this.notifyAdmin('LibreOffice service not running');
            },
            'unsupported_format': () => {
                this.showFormatError(context.format);
            },
            'network_error': () => {
                this.retryWithBackoff(context);
            }
        };
        
        const strategy = strategies[error.type] || strategies.default;
        strategy();
    }
    
    static fallbackToHtml(filename) {
        viewerModeSelector.switchMode('html');
        viewer.loadDocument(filename, 'html');
    }
}
```

### 9. Performance Considerations

#### Lazy Loading
```javascript
// Only load native viewer components when needed
async function loadNativeViewerComponents() {
    if (!window.NativeViewer) {
        const module = await import('./native-viewer.js');
        window.NativeViewer = module.NativeViewer;
    }
    return window.NativeViewer;
}
```

#### Caching Strategy
```python
# Cache converted documents
from functools import lru_cache

@lru_cache(maxsize=100)
def get_document_preview(filename, mode):
    if mode == 'native':
        return generate_native_preview(filename)
    return generate_html_preview(filename)
```

### 10. Migration Strategy

#### Phase 1: Feature Flag (Week 1)
```javascript
const FEATURES = {
    nativeViewer: false  // Start disabled
};
```

#### Phase 2: Beta Testing (Week 2-3)
- Enable for specific users
- Collect performance metrics
- Gather user feedback

#### Phase 3: Gradual Rollout (Week 4-5)
- 10% → 25% → 50% → 100%
- Monitor error rates
- A/B test user engagement

#### Phase 4: Full Launch (Week 6)
- Enable by default for new users
- Existing users keep preference
- Documentation update

## Success Metrics

### Technical Metrics
- Page load time < 2s
- Viewer switch time < 500ms
- Error rate < 0.1%
- Memory usage < 200MB

### User Metrics
- Feature adoption > 60%
- User satisfaction > 4.5/5
- Support tickets < 5/week
- Mode switch rate < 2/session

## Appendix: Technical Dependencies

### Required Packages
```bash
# Backend
pip install python-uno
pip install pycairo
pip install PyPDF2

# Frontend (if using LibreOffice Online)
npm install @collabora/online-sdk
```

### System Requirements
- LibreOffice 7.0+
- Python 3.8+
- 2GB RAM minimum
- 10GB disk space

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+