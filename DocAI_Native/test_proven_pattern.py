#!/usr/bin/env python3
"""
LibreOffice Overlay Test - Using Proven Pattern from SimpleNativeAPI
This follows the EXACT working pattern from DocAI Native
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

class SimpleOverlayAPI:
    """Simple API following the proven SimpleNativeAPI pattern"""
    
    def __init__(self):
        self.window = None
        self.lo_process = None
        self.lo_window_id = None
        self.container_bounds = None
        logger.info("SimpleOverlayAPI initialized")
        # Log available methods on init
        methods = [m for m in dir(self) if not m.startswith('_') and callable(getattr(self, m, None))]
        logger.info(f"Available API methods: {methods}")
    
    def set_window(self, window):
        """Set the webview window reference"""
        self.window = window
        logger.info("Window reference set in SimpleOverlayAPI")
    
    def ping(self):
        """Simple ping to test API connectivity"""
        logger.info("ping called")
        return {"pong": True, "timestamp": time.time()}
    
    def checkLibreOffice(self):
        """Check if LibreOffice is available"""
        logger.info("checkLibreOffice called")
        
        try:
            # Check if soffice command exists
            result = subprocess.run(['which', 'soffice'], capture_output=True)
            available = result.returncode == 0
            
            return {
                "available": available,
                "path": result.stdout.decode().strip() if available else None
            }
        except Exception as e:
            logger.error(f"Error checking LibreOffice: {e}")
            return {"available": False, "error": str(e)}
    
    def launchLibreOffice(self):
        """Launch and position LibreOffice"""
        logger.info("launchLibreOffice called")
        
        if not self.window:
            logger.error("Window not set")
            return {"success": False, "error": "Window not set"}
        
        try:
            # Get container bounds using JavaScript
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
            
            self.container_bounds = self.window.evaluate_js(js_code)
            logger.info(f"Container bounds: {self.container_bounds}")
            
            if not self.container_bounds:
                return {"success": False, "error": "Could not get container bounds"}
            
            # Create test document
            test_file = Path(__file__).parent / "test_document.odt"
            test_file.write_text("LibreOffice Overlay Test Document")
            
            # Launch LibreOffice
            cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
            self.lo_process = subprocess.Popen(cmd)
            logger.info(f"LibreOffice launched with PID: {self.lo_process.pid}")
            
            # Start positioning in background
            threading.Thread(target=self._position_window, daemon=True).start()
            
            return {"success": True, "pid": self.lo_process.pid}
            
        except Exception as e:
            logger.error(f"Error launching LibreOffice: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _position_window(self):
        """Position LibreOffice window (internal method)"""
        # Wait for window to appear
        time.sleep(3)
        
        try:
            # Find window by PID
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(self.lo_process.pid)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                self.lo_window_id = window_ids[-1]
                logger.info(f"Found window: {self.lo_window_id}")
                
                # Position window
                subprocess.run([
                    'xdotool', 'windowmove', self.lo_window_id,
                    str(self.container_bounds['x']),
                    str(self.container_bounds['y'])
                ])
                
                # Resize window
                subprocess.run([
                    'xdotool', 'windowsize', self.lo_window_id,
                    str(self.container_bounds['width']),
                    str(self.container_bounds['height'])
                ])
                
                logger.info("Window positioned successfully")
                
        except Exception as e:
            logger.error(f"Error positioning window: {e}")
    
    def closeDocument(self):
        """Close LibreOffice"""
        logger.info("closeDocument called")
        
        try:
            if self.lo_process:
                self.lo_process.terminate()
                self.lo_process = None
                self.lo_window_id = None
                logger.info("LibreOffice closed")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error closing document: {e}")
            return {"success": False, "error": str(e)}
    
    def getAvailableMethods(self):
        """Return list of available API methods for debugging"""
        methods = []
        for method in dir(self):
            if not method.startswith('_') and callable(getattr(self, method)):
                methods.append(method)
        logger.info(f"Available API methods: {methods}")
        return methods


def create_app():
    """Create the application"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LibreOffice Overlay - Proven Pattern</title>
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
                background: #4CAF50;
                color: white;
                padding: 1rem;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            #controls {
                background: white;
                padding: 1rem;
                display: flex;
                gap: 1rem;
                align-items: center;
                border-bottom: 1px solid #e0e0e0;
            }
            
            button {
                padding: 0.75rem 1.5rem;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s;
            }
            
            button:hover {
                background: #45a049;
                box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
            }
            
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            
            #status {
                margin-left: auto;
                padding: 0.5rem 1rem;
                background: #f5f5f5;
                border-radius: 20px;
                font-size: 14px;
            }
            
            .success { color: #4CAF50; }
            .error { color: #f44336; }
            
            #doc-container {
                flex: 1;
                margin: 1rem;
                background: white;
                border: 3px solid #4CAF50;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
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
            
            .log {
                position: fixed;
                bottom: 1rem;
                right: 1rem;
                background: rgba(0,0,0,0.8);
                color: #0f0;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                font-size: 12px;
                font-family: monospace;
                max-width: 400px;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>LibreOffice Overlay Test - Proven Pattern</h1>
            <p>Using SimpleNativeAPI pattern from DocAI Native</p>
        </div>
        
        <div id="controls">
            <button onclick="testAPI()">Test API</button>
            <button onclick="checkLO()">Check LibreOffice</button>
            <button onclick="openDocument()">Open Document</button>
            <button onclick="closeDocument()">Close Document</button>
            <span id="status">Initializing...</span>
        </div>
        
        <div id="doc-container">
            <div id="placeholder">
                <h2>Document Viewer Area</h2>
                <p>1. Click "Test API" to verify connectivity</p>
                <p>2. Click "Check LibreOffice" to verify installation</p>
                <p>3. Click "Open Document" to overlay LibreOffice here</p>
            </div>
        </div>
        
        <div class="log" id="log">Waiting for API...</div>
        
        <script>
            let apiReady = false;
            
            function log(msg) {
                console.log(msg);
                document.getElementById('log').textContent = msg;
            }
            
            function setStatus(text, isError = false) {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = isError ? 'error' : (text.includes('✓') ? 'success' : '');
            }
            
            // Wait for PyWebView API
            window.addEventListener('pywebviewready', async function() {
                log('PyWebView ready event fired');
                apiReady = true;
                
                // Check API methods
                if (window.pywebview && window.pywebview.api) {
                    try {
                        const methods = await pywebview.api.getAvailableMethods();
                        log('API methods: ' + methods.join(', '));
                        setStatus('✓ API Ready');
                    } catch (e) {
                        log('Could not get API methods: ' + e);
                        setStatus('API Ready (limited)', false);
                    }
                } else {
                    log('API object not found');
                    setStatus('API Error', true);
                }
            });
            
            async function testAPI() {
                if (!apiReady) {
                    setStatus('API not ready', true);
                    return;
                }
                
                try {
                    log('Testing API ping...');
                    const result = await pywebview.api.ping();
                    log('Ping result: ' + JSON.stringify(result));
                    setStatus('✓ API Working: pong=' + result.pong);
                } catch (e) {
                    log('API test error: ' + e);
                    setStatus('API Error: ' + e, true);
                }
            }
            
            async function checkLO() {
                if (!apiReady) {
                    setStatus('API not ready', true);
                    return;
                }
                
                try {
                    log('Checking LibreOffice...');
                    const result = await pywebview.api.checkLibreOffice();
                    log('Check result: ' + JSON.stringify(result));
                    if (result.available) {
                        setStatus('✓ LibreOffice found at: ' + result.path);
                    } else {
                        setStatus('LibreOffice not found', true);
                    }
                } catch (e) {
                    log('Check error: ' + e);
                    setStatus('Check Error: ' + e, true);
                }
            }
            
            async function openDocument() {
                if (!apiReady) {
                    setStatus('API not ready', true);
                    return;
                }
                
                setStatus('Opening document...');
                document.getElementById('placeholder').style.display = 'none';
                
                try {
                    log('Launching LibreOffice...');
                    const result = await pywebview.api.launchLibreOffice();
                    log('Launch result: ' + JSON.stringify(result));
                    
                    if (result.success) {
                        setStatus('✓ Document opened (PID: ' + result.pid + ')');
                    } else {
                        setStatus('Error: ' + result.error, true);
                        document.getElementById('placeholder').style.display = 'block';
                    }
                } catch (e) {
                    log('Launch error: ' + e);
                    setStatus('Launch Error: ' + e, true);
                    document.getElementById('placeholder').style.display = 'block';
                }
            }
            
            async function closeDocument() {
                if (!apiReady) {
                    setStatus('API not ready', true);
                    return;
                }
                
                try {
                    log('Closing document...');
                    const result = await pywebview.api.closeDocument();
                    log('Close result: ' + JSON.stringify(result));
                    setStatus('Document closed');
                    document.getElementById('placeholder').style.display = 'block';
                } catch (e) {
                    log('Close error: ' + e);
                    setStatus('Close Error: ' + e, true);
                }
            }
            
            // Initial check
            setTimeout(() => {
                if (!apiReady) {
                    log('API not ready after 2 seconds');
                    setStatus('API timeout', true);
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
    api = SimpleOverlayAPI()
    
    # Create window
    logger.info("Creating window...")
    window = webview.create_window(
        'LibreOffice Overlay Test',
        html=html,
        js_api=api,
        width=1200,
        height=800
    )
    
    # Set window reference
    api.set_window(window)
    
    # Start WebView
    logger.info("Starting WebView...")
    webview.start(debug=True)


if __name__ == '__main__':
    print("=" * 60)
    print("LibreOffice Overlay Test - Proven Pattern")
    print("Using SimpleNativeAPI pattern from DocAI Native")
    print("=" * 60)
    print()
    print("This version uses:")
    print("- Simple instance methods (no complexity)")
    print("- Same structure as working SimpleNativeAPI")
    print("- Method discovery for debugging")
    print("-" * 60)
    
    create_app()