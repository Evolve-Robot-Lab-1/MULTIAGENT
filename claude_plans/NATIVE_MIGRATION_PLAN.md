# DocAI Native Migration Plan - From Web to Desktop

## Executive Summary

This document outlines the complete migration plan for transforming Durga AI from a web-based application to a native desktop application while preserving all existing functionality and enabling true LibreOffice integration.

### Key Decisions Made:
- **Architecture**: PyWebView wrapper with embedded Flask backend
- **LibreOffice Integration**: UNO socket embedding (prototype) → LibreOfficeKit (future)
- **Philosophy**: Velocity > Perfection, Ship Fast, Iterate Later
- **Modularity**: Keep components swappable for future full-native migration

## Journey Overview

### Starting Point
- **Current State**: Web-based document viewer using Flask + HTML/CSS/JS
- **Problem**: Cannot embed native LibreOffice, only HTML/PDF conversion
- **User Request**: Native LibreOffice viewer with full formatting preservation

### Evolution of Understanding
1. **Initial Misunderstanding**: Implemented PDF conversion (wrong approach)
2. **Clarification**: User wants actual LibreOffice embedding like Cursor/VS Code
3. **Realization**: Need native desktop app, not web app
4. **Decision**: Hybrid approach - keep web tech but wrap in native container

## Architecture Transformation

### From Web Architecture:
```
Browser → HTTP (localhost:8090) → Flask → File Upload → HTML Conversion
```

### To Native Architecture:
```
PyWebView Window → Embedded Flask (random port) → Direct File Access → LibreOffice Embedding
```

## Detailed Execution Steps

### Phase 1: Project Structure Creation

#### Step 1.1: Create Directory Structure
```bash
DocAI_Native/
├── main.py                 # PyWebView entry point
├── backend_server.py       # Modified Flask app
├── uno_bridge.py          # LibreOffice UNO socket integration
├── config.py              # Centralized configuration
├── native_api.py          # Native API bridge
├── requirements.txt       # Dependencies
├── frontend/              # Frontend files (copied from DocAI)
│   ├── index.html        # Modified from indexf.html
│   ├── static/
│   │   ├── css/         # Existing CSS files
│   │   ├── js/          # Modified JS files
│   │   └── assets/      # Images, fonts, etc.
└── build/                # Build configurations
    ├── build.py         # Build script
    └── installer/       # Platform-specific installers
```

### Phase 2: Core Implementation

#### Step 2.1: config.py - Centralized Configuration
```python
import os
from pathlib import Path

class Config:
    # App Info
    APP_NAME = "Durga AI"
    VERSION = "0.1.0"
    
    # Paths
    BASE_DIR = Path(__file__).parent
    FRONTEND_DIR = BASE_DIR / "frontend"
    DOCUMENTS_DIR = Path.home() / "Documents" / "DurgaAI"
    
    # Ports (0 = random)
    FLASK_PORT = 0
    UNO_PORT = 0
    
    # LibreOffice
    LIBREOFFICE_PATH = "/usr/bin/libreoffice"  # Linux
    # LIBREOFFICE_PATH = "C:\\Program Files\\LibreOffice\\program\\soffice.exe"  # Windows
    
    # Auto-update
    UPDATE_URL = "https://api.github.com/repos/yourusername/docai-native/releases/latest"
    AUTO_UPDATE = True
    
    # Development
    DEBUG = True
    HOT_RELOAD = True
    LOG_FILE = BASE_DIR / "docai.log"

CFG = Config()
```

#### Step 2.2: main.py - PyWebView Entry Point
```python
import webview
import threading
import socket
import signal
import sys
import time
from pathlib import Path

from config import CFG
from backend_server import create_app
from native_api import NativeAPI
from uno_bridge import UNOSocketBridge

def get_free_port():
    """Get a free port from the OS"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def start_backend(port, ready_event):
    """Start Flask backend in thread"""
    app = create_app()
    
    # Signal when ready
    def on_ready():
        ready_event.set()
    
    # Run Flask
    app.run(
        host='127.0.0.1',
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )

def main():
    # Get random port
    port = CFG.FLASK_PORT or get_free_port()
    
    # Start backend
    ready_event = threading.Event()
    backend_thread = threading.Thread(
        target=start_backend,
        args=(port, ready_event),
        daemon=True
    )
    backend_thread.start()
    
    # Wait for backend to be ready
    ready_event.wait(timeout=10)
    
    # Initialize native API
    uno_bridge = UNOSocketBridge()
    native_api = NativeAPI(uno_bridge)
    
    # Create window
    window = webview.create_window(
        title=CFG.APP_NAME,
        url=f'http://127.0.0.1:{port}',
        width=1400,
        height=900,
        resizable=True,
        js_api=native_api
    )
    
    # Graceful shutdown
    def on_closing():
        print("Shutting down...")
        uno_bridge.shutdown()
        sys.exit(0)
    
    window.events.closing += on_closing
    
    # Start GUI
    webview.start(debug=CFG.DEBUG)

if __name__ == '__main__':
    main()
```

#### Step 2.3: native_api.py - Native API Bridge
```python
import os
from pathlib import Path
import webview

class NativeAPI:
    """API exposed to JavaScript"""
    
    def __init__(self, uno_bridge):
        self.uno_bridge = uno_bridge
        self.window = None
    
    def set_window(self, window):
        self.window = window
    
    def pick_file(self):
        """Native file picker"""
        file_types = (
            'Document files (*.docx;*.doc;*.odt;*.pdf;*.txt)',
            'All files (*.*)'
        )
        
        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types
        )
        
        if result and len(result) > 0:
            return str(Path(result[0]).resolve())
        return None
    
    def pick_folder(self):
        """Native folder picker"""
        result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if result and len(result) > 0:
            return str(Path(result[0]).resolve())
        return None
    
    def save_file(self, suggested_name="document.docx"):
        """Native save dialog"""
        result = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=suggested_name
        )
        if result:
            return str(Path(result).resolve())
        return None
    
    def embed_libreoffice(self, container_id, file_path):
        """Embed LibreOffice in container"""
        try:
            return self.uno_bridge.embed_document(file_path, container_id)
        except Exception as e:
            return {"error": str(e)}
    
    def show_message(self, title, message):
        """Native message box"""
        self.window.create_confirmation_dialog(title, message)
    
    def get_platform(self):
        """Get platform info"""
        import platform
        return {
            "system": platform.system(),
            "version": platform.version(),
            "machine": platform.machine()
        }
```

#### Step 2.4: uno_bridge.py - LibreOffice Integration
```python
import subprocess
import time
import os
import socket
from pathlib import Path
from config import CFG

class UNOSocketBridge:
    """LibreOffice UNO socket integration"""
    
    def __init__(self):
        self.port = None
        self.process = None
        self._find_free_port()
    
    def _find_free_port(self):
        """Find free port for UNO"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            self.port = s.getsockname()[1]
    
    def start_libreoffice_server(self):
        """Start LibreOffice with UNO socket"""
        if self.process:
            return True
            
        cmd = [
            CFG.LIBREOFFICE_PATH,
            '--accept=socket,host=localhost,port={};urp;'.format(self.port),
            '--norestore',
            '--norelogo',
            '--nodefault',
            '--headless'
        ]
        
        # Try to start LibreOffice
        for attempt in range(3):
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                time.sleep(2)  # Wait for startup
                
                # Check if running
                if self.process.poll() is None:
                    print(f"LibreOffice started on port {self.port}")
                    return True
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    self._find_free_port()  # Try different port
                    
        return False
    
    def embed_document(self, file_path, container_id):
        """Embed document in container (prototype)"""
        if not self.start_libreoffice_server():
            return {"error": "Failed to start LibreOffice"}
        
        try:
            # This is the prototype implementation
            # TODO: Replace with proper LOK implementation
            
            # For now, return success with info
            return {
                "success": True,
                "mode": "uno_socket",
                "port": self.port,
                "file": file_path,
                "message": "Document loaded (prototype mode)"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def shutdown(self):
        """Shutdown LibreOffice"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None
```

#### Step 2.5: backend_server.py - Modified Flask App
```python
import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

# Add parent directory to path to import existing modules
sys.path.insert(0, str(Path(__file__).parent.parent / "DocAI"))

from config import CFG

def create_app():
    """Create Flask app with modifications for native"""
    app = Flask(__name__, 
                static_folder=str(CFG.FRONTEND_DIR / 'static'),
                template_folder=str(CFG.FRONTEND_DIR))
    
    # Serve frontend
    @app.route('/')
    def index():
        return send_from_directory(CFG.FRONTEND_DIR, 'index.html')
    
    # Native file operations (no upload!)
    @app.route('/api/open_file', methods=['POST'])
    def open_file():
        """Open file from native file picker"""
        data = request.json
        file_path = data.get('path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'Invalid file path'}), 400
        
        # Reuse existing document processing logic
        try:
            # Import existing processing function
            from app.services.document_service import process_document
            result = process_document(file_path)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Remove all upload routes - we don't need them!
    # @app.route('/upload') - DELETED
    # @app.route('/rag/upload') - DELETED
    
    # Keep existing routes that make sense
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Keep existing chat functionality"""
        # Reuse existing chat logic
        pass
    
    # Health check
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'ok',
            'version': CFG.VERSION,
            'mode': 'native'
        })
    
    return app
```

### Phase 3: Frontend Modifications

#### Step 3.1: Modify index.html
```html
<!-- Changes to frontend/index.html -->
<!-- Replace file upload with native picker -->
<script>
// Check if running in native mode
const isNative = window.pywebview !== undefined;

// Override file operations
async function handleUploadFile() {
    if (isNative) {
        const path = await pywebview.api.pick_file();
        if (path) {
            openDocument(path);
        }
    } else {
        // Fallback for development
        console.warn('Not in native mode');
    }
}

async function openDocument(path) {
    const response = await fetch('/api/open_file', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path: path})
    });
    
    const data = await response.json();
    displayDocument(data);
}

// Native LibreOffice embedding
async function embedLibreOffice(path) {
    if (isNative) {
        const result = await pywebview.api.embed_libreoffice('doc-container', path);
        console.log('Embed result:', result);
    }
}
</script>
```

### Phase 4: Build and Distribution

#### Step 4.1: requirements.txt
```
pywebview>=4.0.0
flask>=2.0.0
python-uno
watchdog>=2.0.0
packaging>=21.0
pyinstaller>=5.0
```

#### Step 4.2: Build Script (build.py)
```python
import PyInstaller.__main__
import shutil
from pathlib import Path

def build():
    """Build executable"""
    
    # Clean previous builds
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('build', ignore_errors=True)
    
    # Run PyInstaller
    PyInstaller.__main__.run([
        'main.py',
        '--name=DurgaAI',
        '--onefile',
        '--windowed',
        '--icon=frontend/static/assets/icon.ico',
        '--add-data=frontend:frontend',
        '--add-data=config.py:.',
        '--hidden-import=uno',
        '--hidden-import=flask',
    ])
    
    print("Build complete! Check dist/ folder")

if __name__ == '__main__':
    build()
```

## Testing Strategy

### 1. Development Testing
```bash
# Run in development mode
cd DocAI_Native
python main.py

# Test features:
- [ ] Window opens correctly
- [ ] File picker works
- [ ] Document loads
- [ ] LibreOffice embedding (prototype)
- [ ] Chat functionality
```

### 2. Build Testing
```bash
# Build executable
python build.py

# Test executable
./dist/DurgaAI

# Verify:
- [ ] Runs without Python installed
- [ ] All features work
- [ ] No missing dependencies
```

## Migration Checklist

- [x] Understand requirements (native LibreOffice embedding)
- [x] Design architecture (PyWebView + Flask)
- [x] Plan implementation (modular, fast shipping)
- [ ] Create folder structure
- [ ] Implement core files
- [ ] Migrate frontend
- [ ] Test prototype
- [ ] Build executable
- [ ] Test on target platforms
- [ ] Implement auto-update
- [ ] Ship to users

## Future Roadmap

### Short Term (Next Sprint)
1. Complete UNO socket prototype
2. Basic LibreOffice embedding working
3. Ship first version to users
4. Gather feedback

### Medium Term (1-2 Months)
1. Migrate from UNO to LibreOfficeKit
2. Implement proper embedding
3. Add collaboration features
4. Performance optimization

### Long Term (3-6 Months)
1. Consider full native widgets (PyQt6)
2. Advanced LibreOffice integration
3. Multi-window support
4. Plugin architecture

## Key Decisions Log

1. **PyWebView over Electron**: Lighter, Python-native, no Chromium
2. **Keep Flask**: Reuse existing backend logic
3. **Random Ports**: Security through obscurity
4. **UNO Socket First**: Quick prototype, LOK later
5. **Modular Architecture**: Easy to swap components

## Resources and References

- [PyWebView Documentation](https://pywebview.flowrl.com/)
- [LibreOffice UNO API](https://api.libreoffice.org/)
- [PyInstaller Guide](https://pyinstaller.readthedocs.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## Progress Status

### Completed ✅
- Requirements analysis
- Architecture design
- Implementation plan
- Code templates

### In Progress 🚧
- Folder structure creation
- Core implementation
- Frontend migration

### Pending ⏳
- Testing
- Building
- Distribution
- User feedback

---

*Last Updated: [Current Date]*
*Next Review: After prototype implementation*