#!/usr/bin/env python3
"""
Fixed LibreOffice Overlay - Proven PyWebView Pattern
This implementation follows the exact pattern from DocAI Native main.py
"""

import os
import sys
import time
import subprocess
import threading
import webview
import logging
import shutil
import tempfile
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state - module level
_window = None
_lo_process = None
_lo_window_id = None
_container_bounds = None

# Module-level API functions (no closures!)
def set_window(window):
    """Set the window reference"""
    global _window
    _window = window
    logger.info("Window reference set")

def ping():
    """Test API connectivity"""
    logger.info("ping called")
    return {"pong": True, "time": time.time()}

def launch_libreoffice():
    """Launch and position LibreOffice"""
    global _lo_process, _container_bounds
    
    logger.info("launch_libreoffice called")
    
    if not _window:
        return {"success": False, "error": "Window not set"}
    
    try:
        # Get container bounds
        js_code = """
        (function() {
            var container = document.getElementById('doc-container');
            if (!container) return null;
            
            var rect = container.getBoundingClientRect();
            return {
                x: Math.round(window.screenX + rect.left),
                y: Math.round(window.screenY + rect.top + 80),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            };
        })()
        """
        
        _container_bounds = _window.evaluate_js(js_code)
        logger.info(f"Container bounds: {_container_bounds}")
        
        if not _container_bounds:
            return {"success": False, "error": "Could not get container bounds"}
        
        # Create test document
        test_file = Path(__file__).parent / "fixed_overlay.odt"
        test_file.write_text("Fixed Overlay Test")
        
        # Launch LibreOffice
        cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
        _lo_process = subprocess.Popen(cmd)
        logger.info(f"LibreOffice launched with PID: {_lo_process.pid}")
        
        # Position in background
        threading.Thread(target=_position_window, daemon=True).start()
        
        return {"success": True, "message": "LibreOffice launching..."}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"success": False, "error": str(e)}

def _position_window():
    """Position LibreOffice window"""
    global _lo_window_id
    
    time.sleep(3)
    
    try:
        # Find window
        result = subprocess.run(
            ['xdotool', 'search', '--pid', str(_lo_process.pid)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_ids = result.stdout.strip().split('\n')
            _lo_window_id = window_ids[-1]
            logger.info(f"Found window: {_lo_window_id}")
            
            # Position it
            subprocess.run([
                'xdotool', 'windowmove', _lo_window_id,
                str(_container_bounds['x']),
                str(_container_bounds['y'])
            ])
            
            subprocess.run([
                'xdotool', 'windowsize', _lo_window_id,
                str(_container_bounds['width']),
                str(_container_bounds['height'])
            ])
            
            logger.info("Window positioned")
            
    except Exception as e:
        logger.error(f"Position error: {e}")

def close_document():
    """Close LibreOffice"""
    global _lo_process, _lo_window_id
    
    logger.info("close_document called")
    
    if _lo_process:
        _lo_process.terminate()
        _lo_process = None
        _lo_window_id = None
        
    return {"success": True}

# Fixed API class - exactly like DocAI Native
class FixedOverlayAPI:
    """Fixed API class for PyWebView - proven pattern"""
    
    def __init__(self):
        # Simple assignments - no wrappers!
        self.set_window = set_window
        self.ping = ping
        self.launch_libreoffice = launch_libreoffice
        self.close_document = close_document
        logger.info("FixedOverlayAPI initialized")


def clear_pywebview_cache():
    """Clear PyWebView cache to prevent API registration issues"""
    cache_paths = [
        Path.home() / '.pywebview',
        Path(tempfile.gettempdir()) / 'pywebview',
        Path.home() / 'AppData' / 'Local' / 'pywebview' / 'EBWebView',  # Windows
        Path.home() / '.cache' / 'pywebview',  # Linux
        Path.home() / 'Library' / 'Caches' / 'pywebview',  # macOS
    ]
    
    for cache_path in cache_paths:
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                logger.info(f"Cleared cache at: {cache_path}")
            except Exception as e:
                logger.warning(f"Could not clear cache at {cache_path}: {e}")


def create_app():
    """Create the application following DocAI Native pattern"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fixed LibreOffice Overlay</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, sans-serif;
                height: 100vh;
                display: flex;
                flex-direction: column;
                background: #f5f5f5;
            }
            
            #header {
                background: #4a90e2;
                color: white;
                padding: 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            #controls {
                background: white;
                padding: 1rem;
                display: flex;
                gap: 1rem;
                align-items: center;
                border-bottom: 1px solid #ddd;
            }
            
            button {
                padding: 0.5rem 1rem;
                background: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            
            button:hover {
                background: #357abd;
            }
            
            #status {
                margin-left: auto;
                padding: 0.5rem 1rem;
                background: #f0f0f0;
                border-radius: 4px;
                font-size: 0.875rem;
            }
            
            #doc-container {
                flex: 1;
                margin: 1rem;
                background: white;
                border: 2px solid #4a90e2;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            }
            
            #placeholder {
                text-align: center;
                color: #999;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>Fixed LibreOffice Overlay Test</h1>
        </div>
        
        <div id="controls">
            <button onclick="testAPI()">Test API</button>
            <button onclick="openDoc()">Open Document</button>
            <button onclick="closeDoc()">Close Document</button>
            <span id="status">Ready</span>
        </div>
        
        <div id="doc-container">
            <div id="placeholder">
                <p>Click "Test API" first to verify connectivity</p>
                <p>Then click "Open Document" to overlay LibreOffice here</p>
            </div>
        </div>
        
        <script>
            function setStatus(text) {
                document.getElementById('status').textContent = text;
            }
            
            async function testAPI() {
                try {
                    const result = await pywebview.api.ping();
                    setStatus('API Working! ' + JSON.stringify(result));
                    console.log('Ping success:', result);
                } catch (e) {
                    setStatus('API Error: ' + e);
                    console.error('Ping error:', e);
                }
            }
            
            async function openDoc() {
                setStatus('Opening...');
                document.getElementById('placeholder').style.display = 'none';
                
                try {
                    const result = await pywebview.api.launch_libreoffice();
                    if (result.success) {
                        setStatus('Document opened');
                    } else {
                        setStatus('Error: ' + result.error);
                        document.getElementById('placeholder').style.display = 'block';
                    }
                } catch (e) {
                    setStatus('Error: ' + e);
                    document.getElementById('placeholder').style.display = 'block';
                    console.error('Open error:', e);
                }
            }
            
            async function closeDoc() {
                try {
                    await pywebview.api.close_document();
                    setStatus('Document closed');
                    document.getElementById('placeholder').style.display = 'block';
                } catch (e) {
                    setStatus('Error: ' + e);
                    console.error('Close error:', e);
                }
            }
            
            // Log when ready
            window.addEventListener('pywebviewready', function() {
                console.log('PyWebView ready');
                setStatus('API Ready - Click Test API');
            });
        </script>
    </body>
    </html>
    """
    
    # CRITICAL: Clear cache first!
    logger.info("Clearing PyWebView cache...")
    clear_pywebview_cache()
    
    # Create API instance
    api = FixedOverlayAPI()
    
    # Create window
    window = webview.create_window(
        'Fixed LibreOffice Overlay',
        html=html,
        js_api=api,
        width=1200,
        height=800
    )
    
    # Set window reference AFTER creation
    api.set_window(window)
    
    # Start
    webview.start(debug=True)


if __name__ == '__main__':
    print("=" * 60)
    print("FIXED LibreOffice Overlay Test")
    print("Following exact DocAI Native pattern")
    print("=" * 60)
    print()
    print("This implementation:")
    print("1. Clears PyWebView cache before starting")
    print("2. Uses module-level functions (no closures)")
    print("3. Uses simple class with direct assignments")
    print("4. Sets window reference after creation")
    print("-" * 60)
    
    create_app()