#!/usr/bin/env python3
"""
Final Overlay Test - Using SimpleNativeAPI pattern from DocAI
This matches the actual implementation pattern in the app
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

class OverlayAPI:
    """API class matching DocAI Native pattern"""
    def __init__(self):
        self.window = None
        self.lo_process = None
        self.lo_window_id = None
        self.container_bounds = None
        
    def set_window(self, window):
        """Set window reference"""
        self.window = window
        logger.info("Window reference set")
        
    def launch_libreoffice(self):
        """Launch and position LibreOffice"""
        try:
            logger.info("launch_libreoffice called")
            
            if not self.window:
                return {"success": False, "error": "Window not set"}
                
            # Get container position using JavaScript
            js_code = """
            (function() {
                var container = document.getElementById('doc-container');
                if (!container) return null;
                
                var rect = container.getBoundingClientRect();
                var x = window.screenX + rect.left;
                var y = window.screenY + rect.top + 80; // Adjust for window chrome
                
                return {
                    x: Math.round(x),
                    y: Math.round(y),
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
            test_file = Path(__file__).parent / "overlay_test.odt"
            test_file.write_text("Overlay Test Document")
            
            # Launch LibreOffice
            cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
            self.lo_process = subprocess.Popen(cmd)
            logger.info(f"LibreOffice launched with PID: {self.lo_process.pid}")
            
            # Position window in background thread
            threading.Thread(target=self._position_window, daemon=True).start()
            
            return {"success": True, "message": "LibreOffice launching..."}
            
        except Exception as e:
            logger.error(f"Error in launch_libreoffice: {e}")
            return {"success": False, "error": str(e)}
            
    def _position_window(self):
        """Position LibreOffice window after it opens"""
        time.sleep(3)  # Wait for window
        
        try:
            # Find window by PID
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(self.lo_process.pid)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                
                # Use the last window (usually the document window)
                self.lo_window_id = window_ids[-1]
                logger.info(f"Found LibreOffice window: {self.lo_window_id}")
                
                # Position and resize
                subprocess.run([
                    'xdotool', 'windowmove', self.lo_window_id,
                    str(self.container_bounds['x']),
                    str(self.container_bounds['y'])
                ])
                
                subprocess.run([
                    'xdotool', 'windowsize', self.lo_window_id,
                    str(self.container_bounds['width']),
                    str(self.container_bounds['height'])
                ])
                
                logger.info("Window positioned successfully")
                
        except Exception as e:
            logger.error(f"Error positioning window: {e}")
            
    def close_document(self):
        """Close LibreOffice"""
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
            
    def get_status(self):
        """Get current status"""
        return {
            "running": self.lo_process is not None,
            "window_id": self.lo_window_id
        }


def create_app():
    """Create the application"""
    # HTML interface
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Final Overlay Test</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: Arial, sans-serif;
                height: 100vh;
                display: flex;
                flex-direction: column;
                background: #f0f0f0;
            }
            
            #header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            #header h1 {
                margin: 0;
                font-size: 24px;
            }
            
            #main {
                flex: 1;
                display: flex;
                padding: 20px;
                gap: 20px;
            }
            
            #sidebar {
                width: 200px;
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            #content {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            #controls {
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex;
                gap: 10px;
                align-items: center;
            }
            
            button {
                padding: 10px 20px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                transition: background 0.3s;
            }
            
            button:hover {
                background: #764ba2;
            }
            
            #status {
                margin-left: auto;
                padding: 5px 15px;
                background: #e0e0e0;
                border-radius: 20px;
                font-size: 14px;
            }
            
            #doc-container {
                flex: 1;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }
            
            #placeholder {
                text-align: center;
                color: #999;
            }
            
            #placeholder h2 {
                margin-bottom: 10px;
                color: #666;
            }
            
            .debug-info {
                position: absolute;
                bottom: 10px;
                right: 10px;
                font-size: 12px;
                color: #999;
                background: rgba(255,255,255,0.9);
                padding: 5px 10px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>DocAI Native - LibreOffice Overlay Test</h1>
        </div>
        
        <div id="main">
            <div id="sidebar">
                <h3>Files</h3>
                <p style="color: #999; margin-top: 10px;">File list simulation</p>
            </div>
            
            <div id="content">
                <div id="controls">
                    <button onclick="openDoc()">Open Document</button>
                    <button onclick="closeDoc()">Close Document</button>
                    <span id="status">Ready</span>
                </div>
                
                <div id="doc-container">
                    <div id="placeholder">
                        <h2>Document Viewer</h2>
                        <p>Click "Open Document" to overlay LibreOffice here</p>
                    </div>
                    <div class="debug-info" id="debug"></div>
                </div>
            </div>
        </div>
        
        <script>
            // Update debug info
            function updateDebug() {
                const container = document.getElementById('doc-container');
                const rect = container.getBoundingClientRect();
                document.getElementById('debug').textContent = 
                    `Container: ${Math.round(rect.width)}x${Math.round(rect.height)}`;
            }
            
            updateDebug();
            window.addEventListener('resize', updateDebug);
            
            async function openDoc() {
                document.getElementById('status').textContent = 'Opening...';
                document.getElementById('placeholder').style.display = 'none';
                
                try {
                    const result = await pywebview.api.launch_libreoffice();
                    if (result && result.success) {
                        document.getElementById('status').textContent = 'Document Open';
                    } else {
                        document.getElementById('status').textContent = 'Error: ' + (result ? result.error : 'Unknown');
                        document.getElementById('placeholder').style.display = 'block';
                    }
                } catch (e) {
                    console.error('Error:', e);
                    document.getElementById('status').textContent = 'Error: ' + e;
                    document.getElementById('placeholder').style.display = 'block';
                }
            }
            
            async function closeDoc() {
                try {
                    await pywebview.api.close_document();
                    document.getElementById('status').textContent = 'Ready';
                    document.getElementById('placeholder').style.display = 'block';
                } catch (e) {
                    console.error('Error:', e);
                }
            }
            
            // Log when ready
            console.log('UI ready, pywebview available:', typeof pywebview !== 'undefined');
        </script>
    </body>
    </html>
    """
    
    # Create API instance
    api = OverlayAPI()
    
    # Create window
    window = webview.create_window(
        'LibreOffice Overlay Test',
        html=html,
        js_api=api,
        width=1200,
        height=800
    )
    
    # Set window reference in API
    api.set_window(window)
    
    # Start
    webview.start(debug=True)


if __name__ == '__main__':
    print("=" * 60)
    print("LibreOffice Overlay Test - Final Implementation")
    print("=" * 60)
    print("This test demonstrates the overlay approach for Phase 2")
    print("Click 'Open Document' to position LibreOffice over the container")
    print("-" * 60)
    
    create_app()