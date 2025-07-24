#!/usr/bin/env python3
"""
Final Working LibreOffice Overlay Test
This version ensures proper API registration
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global state
_window = None
_lo_process = None
_lo_window_id = None
_container_bounds = None

def clear_pywebview_cache():
    """Clear PyWebView cache to prevent API registration issues"""
    cache_paths = [
        Path.home() / '.pywebview',
        Path(tempfile.gettempdir()) / 'pywebview',
        Path.home() / '.cache' / 'pywebview',
    ]
    
    for cache_path in cache_paths:
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                logger.info(f"Cleared cache at: {cache_path}")
            except Exception as e:
                logger.warning(f"Could not clear cache at {cache_path}: {e}")

class LibreOfficeAPI:
    """API class for PyWebView"""
    
    def __init__(self):
        self.window = None
        logger.info("LibreOfficeAPI initialized")
    
    def set_window(self, window):
        """Set window reference"""
        self.window = window
        global _window
        _window = window
        logger.info("Window reference set")
    
    def test_api(self):
        """Test API connectivity"""
        logger.info("test_api called")
        return {"status": "API Working!", "time": time.time()}
    
    def launch_libreoffice(self):
        """Launch and position LibreOffice"""
        global _lo_process, _container_bounds
        
        logger.info("launch_libreoffice called")
        
        if not self.window:
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
            
            _container_bounds = self.window.evaluate_js(js_code)
            logger.info(f"Container bounds: {_container_bounds}")
            
            if not _container_bounds:
                return {"success": False, "error": "Could not get container bounds"}
            
            # Create test document
            test_file = Path(__file__).parent / "test_document.odt"
            test_file.write_text("LibreOffice Overlay Test Document")
            
            # Launch LibreOffice
            cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
            _lo_process = subprocess.Popen(cmd)
            logger.info(f"LibreOffice launched with PID: {_lo_process.pid}")
            
            # Start positioning thread
            threading.Thread(target=self._position_window, daemon=True).start()
            
            return {"success": True, "message": "LibreOffice launching..."}
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _position_window(self):
        """Position LibreOffice window"""
        global _lo_window_id
        
        # Wait for window to appear
        time.sleep(3)
        
        try:
            # Find window by PID
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(_lo_process.pid)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                _lo_window_id = window_ids[-1]
                logger.info(f"Found window: {_lo_window_id}")
                
                # Position window
                subprocess.run([
                    'xdotool', 'windowmove', _lo_window_id,
                    str(_container_bounds['x']),
                    str(_container_bounds['y'])
                ])
                
                # Resize window
                subprocess.run([
                    'xdotool', 'windowsize', _lo_window_id,
                    str(_container_bounds['width']),
                    str(_container_bounds['height'])
                ])
                
                logger.info("Window positioned successfully")
                
        except Exception as e:
            logger.error(f"Position error: {e}")
    
    def close_document(self):
        """Close LibreOffice"""
        global _lo_process, _lo_window_id
        
        logger.info("close_document called")
        
        if _lo_process:
            _lo_process.terminate()
            _lo_process = None
            _lo_window_id = None
            
        return {"success": True}


def create_app():
    """Create the application"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LibreOffice Overlay Test</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                height: 100vh;
                display: flex;
                flex-direction: column;
                background: #f5f5f5;
            }
            
            #header {
                background: #2196F3;
                color: white;
                padding: 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }
            
            #controls {
                background: white;
                padding: 1rem;
                display: flex;
                gap: 1rem;
                align-items: center;
                border-bottom: 1px solid #e0e0e0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            button {
                padding: 0.75rem 1.5rem;
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s;
            }
            
            button:hover {
                background: #1976D2;
                box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
            }
            
            button:active {
                transform: translateY(1px);
            }
            
            #status {
                margin-left: auto;
                padding: 0.5rem 1rem;
                background: #f5f5f5;
                border-radius: 20px;
                font-size: 14px;
                color: #666;
            }
            
            #status.success {
                background: #e8f5e9;
                color: #2e7d32;
            }
            
            #status.error {
                background: #ffebee;
                color: #c62828;
            }
            
            #doc-container {
                flex: 1;
                margin: 1rem;
                background: white;
                border: 3px solid #2196F3;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            #placeholder {
                text-align: center;
                color: #666;
                padding: 2rem;
            }
            
            #placeholder h2 {
                color: #333;
                margin-bottom: 1rem;
            }
            
            #placeholder p {
                color: #999;
                line-height: 1.6;
            }
            
            .info {
                position: fixed;
                bottom: 1rem;
                right: 1rem;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                font-size: 12px;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>LibreOffice Overlay Test - Final Working Version</h1>
        </div>
        
        <div id="controls">
            <button onclick="testAPI()">Test API</button>
            <button onclick="openDocument()">Open Document</button>
            <button onclick="closeDocument()">Close Document</button>
            <span id="status">Initializing...</span>
        </div>
        
        <div id="doc-container">
            <div id="placeholder">
                <h2>Document Viewer Area</h2>
                <p>1. Click "Test API" to verify connectivity</p>
                <p>2. Click "Open Document" to overlay LibreOffice here</p>
                <p>3. LibreOffice will be positioned over this container</p>
            </div>
        </div>
        
        <div class="info" id="info">Waiting for API...</div>
        
        <script>
            let apiReady = false;
            
            function updateStatus(text, type = '') {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = type;
            }
            
            function updateInfo(text) {
                document.getElementById('info').textContent = text;
            }
            
            // Wait for PyWebView API to be ready
            window.addEventListener('pywebviewready', function() {
                console.log('PyWebView ready event fired');
                apiReady = true;
                updateStatus('Ready', 'success');
                updateInfo('API Ready');
                
                // Double-check API availability
                if (window.pywebview && window.pywebview.api) {
                    console.log('API confirmed available');
                    console.log('API methods:', Object.keys(window.pywebview.api));
                } else {
                    console.error('API not available after ready event');
                }
            });
            
            async function testAPI() {
                if (!apiReady) {
                    updateStatus('API not ready yet', 'error');
                    return;
                }
                
                try {
                    console.log('Testing API...');
                    const result = await pywebview.api.test_api();
                    console.log('API test result:', result);
                    updateStatus('API Working: ' + JSON.stringify(result), 'success');
                } catch (e) {
                    console.error('API test error:', e);
                    updateStatus('API Error: ' + e, 'error');
                }
            }
            
            async function openDocument() {
                if (!apiReady) {
                    updateStatus('API not ready yet', 'error');
                    return;
                }
                
                updateStatus('Opening document...', '');
                document.getElementById('placeholder').style.display = 'none';
                
                try {
                    console.log('Calling launch_libreoffice...');
                    const result = await pywebview.api.launch_libreoffice();
                    console.log('Launch result:', result);
                    
                    if (result.success) {
                        updateStatus('Document opened', 'success');
                        updateInfo('LibreOffice PID: ' + result.message);
                    } else {
                        updateStatus('Error: ' + result.error, 'error');
                        document.getElementById('placeholder').style.display = 'block';
                    }
                } catch (e) {
                    console.error('Launch error:', e);
                    updateStatus('Error: ' + e, 'error');
                    document.getElementById('placeholder').style.display = 'block';
                }
            }
            
            async function closeDocument() {
                if (!apiReady) {
                    updateStatus('API not ready yet', 'error');
                    return;
                }
                
                try {
                    console.log('Closing document...');
                    await pywebview.api.close_document();
                    updateStatus('Document closed', '');
                    updateInfo('API Ready');
                    document.getElementById('placeholder').style.display = 'block';
                } catch (e) {
                    console.error('Close error:', e);
                    updateStatus('Error: ' + e, 'error');
                }
            }
            
            // Initial check after page load
            setTimeout(() => {
                if (!apiReady) {
                    updateStatus('API not available - check console', 'error');
                    updateInfo('API initialization failed');
                }
            }, 2000);
        </script>
    </body>
    </html>
    """
    
    # Clear cache first
    logger.info("Clearing PyWebView cache...")
    clear_pywebview_cache()
    
    # Create API instance
    api = LibreOfficeAPI()
    
    # Create window with API
    logger.info("Creating window...")
    window = webview.create_window(
        'LibreOffice Overlay Test',
        html=html,
        js_api=api,
        width=1200,
        height=800,
        min_size=(800, 600)
    )
    
    # Set window reference after creation
    api.set_window(window)
    
    # Start WebView
    logger.info("Starting WebView...")
    webview.start(debug=True)


if __name__ == '__main__':
    print("=" * 60)
    print("LibreOffice Overlay Test - Final Working Version")
    print("=" * 60)
    print()
    print("Features:")
    print("- Cache clearing before start")
    print("- Proper API class structure")
    print("- API ready detection")
    print("- Detailed logging")
    print()
    print("Instructions:")
    print("1. Wait for 'Ready' status")
    print("2. Click 'Test API' to verify")
    print("3. Click 'Open Document' to test overlay")
    print("-" * 60)
    
    create_app()