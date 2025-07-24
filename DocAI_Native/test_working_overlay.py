#!/usr/bin/env python3
"""
Working Overlay Test - Using exact FixedAPI pattern from DocAI
This follows the proven working pattern
"""

import os
import sys
import time
import subprocess
import threading
import webview
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global references
_window = None
_lo_process = None
_lo_window_id = None
_container_bounds = None

def set_window(window):
    """Set the window reference"""
    global _window
    _window = window
    logger.info("Window reference set")

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
        test_file = Path(__file__).parent / "working_overlay.odt"
        test_file.write_text("Working Overlay Test")
        
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

def ping():
    """Test API connectivity"""
    logger.info("ping called")
    return {"pong": True, "time": time.time()}

# Fixed API class following DocAI pattern
class WorkingAPI:
    """API class that works with PyWebView"""
    
    def __init__(self):
        # Assign module functions as methods
        self.set_window = set_window
        self.launch_libreoffice = launch_libreoffice
        self.close_document = close_document
        self.ping = ping
        logger.info("WorkingAPI initialized")


def create_app():
    """Create the application"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Working Overlay Test</title>
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            #header h1 {
                margin: 0;
                font-size: 1.75rem;
                font-weight: 600;
            }
            
            #header p {
                margin-top: 0.5rem;
                opacity: 0.9;
            }
            
            #content {
                flex: 1;
                padding: 2rem;
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            
            #controls {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                display: flex;
                gap: 1rem;
                align-items: center;
            }
            
            button {
                padding: 0.75rem 1.5rem;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            button:hover {
                background: #5a67d8;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }
            
            button:active {
                transform: translateY(0);
            }
            
            #status {
                margin-left: auto;
                padding: 0.5rem 1rem;
                background: #f0f0f0;
                border-radius: 20px;
                font-size: 0.875rem;
                font-weight: 500;
            }
            
            #status.success { background: #d4edda; color: #155724; }
            #status.error { background: #f8d7da; color: #721c24; }
            #status.loading { background: #fff3cd; color: #856404; }
            
            #doc-container {
                flex: 1;
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }
            
            #placeholder {
                text-align: center;
                color: #718096;
            }
            
            #placeholder svg {
                width: 64px;
                height: 64px;
                margin-bottom: 1rem;
                opacity: 0.3;
            }
            
            #placeholder h2 {
                font-size: 1.5rem;
                font-weight: 600;
                color: #4a5568;
                margin-bottom: 0.5rem;
            }
            
            .debug {
                position: fixed;
                bottom: 1rem;
                right: 1rem;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-family: monospace;
                font-size: 0.75rem;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>Working LibreOffice Overlay Test</h1>
            <p>Using proven FixedAPI pattern from DocAI Native</p>
        </div>
        
        <div id="content">
            <div id="controls">
                <button onclick="testPing()">Test API</button>
                <button onclick="openDoc()">Open Document</button>
                <button onclick="closeDoc()">Close Document</button>
                <span id="status">Ready</span>
            </div>
            
            <div id="doc-container">
                <div id="placeholder">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    <h2>Document Viewer</h2>
                    <p>Click "Open Document" to overlay LibreOffice here</p>
                </div>
            </div>
        </div>
        
        <div class="debug" id="debug">API Status: Checking...</div>
        
        <script>
            function setStatus(text, type = 'default') {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = type;
            }
            
            function setDebug(text) {
                document.getElementById('debug').textContent = text;
            }
            
            // Check API availability
            window.addEventListener('pywebviewready', function() {
                setDebug('API Status: Ready');
                console.log('PyWebView API ready');
            });
            
            async function testPing() {
                try {
                    const result = await pywebview.api.ping();
                    setStatus('API working! Pong: ' + JSON.stringify(result), 'success');
                    console.log('Ping result:', result);
                } catch (e) {
                    setStatus('API Error: ' + e, 'error');
                    console.error('Ping error:', e);
                }
            }
            
            async function openDoc() {
                setStatus('Opening document...', 'loading');
                document.getElementById('placeholder').style.display = 'none';
                
                try {
                    const result = await pywebview.api.launch_libreoffice();
                    if (result && result.success) {
                        setStatus('Document opened', 'success');
                    } else {
                        setStatus('Error: ' + (result ? result.error : 'Unknown'), 'error');
                        document.getElementById('placeholder').style.display = 'block';
                    }
                } catch (e) {
                    setStatus('Error: ' + e, 'error');
                    document.getElementById('placeholder').style.display = 'block';
                    console.error('Open error:', e);
                }
            }
            
            async function closeDoc() {
                try {
                    await pywebview.api.close_document();
                    setStatus('Document closed', 'default');
                    document.getElementById('placeholder').style.display = 'block';
                } catch (e) {
                    setStatus('Error: ' + e, 'error');
                    console.error('Close error:', e);
                }
            }
            
            // Initial check
            setTimeout(() => {
                if (typeof pywebview === 'undefined') {
                    setDebug('API Status: Not available');
                }
            }, 1000);
        </script>
    </body>
    </html>
    """
    
    # Create API instance
    api = WorkingAPI()
    
    # Create window
    window = webview.create_window(
        'Working Overlay Test',
        html=html,
        js_api=api,
        width=1200,
        height=800
    )
    
    # Set window reference
    api.set_window(window)
    
    # Start
    webview.start(debug=True)


if __name__ == '__main__':
    print("=" * 60)
    print("Working LibreOffice Overlay Test")
    print("Using proven FixedAPI pattern from DocAI Native")
    print("=" * 60)
    print()
    print("This should work without PyWebView API errors!")
    print("Click 'Test API' first to verify connectivity")
    print("-" * 60)
    
    create_app()