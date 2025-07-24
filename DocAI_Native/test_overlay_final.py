#!/usr/bin/env python3
"""
LibreOffice Overlay Test - Building on Ultra Simple Success
"""

import webview
import logging
import subprocess
import threading
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
lo_process = None
lo_window_id = None
container_bounds = None

class OverlayAPI:
    def __init__(self):
        self.window = None
        logger.info("OverlayAPI initialized")
    
    def set_window(self, window):
        self.window = window
        logger.info("Window reference set")
    
    def ping(self):
        """Test method"""
        logger.info("ping called!")
        return "pong"
    
    def check_libreoffice(self):
        """Check if LibreOffice is installed"""
        logger.info("check_libreoffice called")
        try:
            result = subprocess.run(['which', 'soffice'], capture_output=True, text=True)
            available = result.returncode == 0
            return {
                "available": available,
                "path": result.stdout.strip() if available else None
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"available": False, "error": str(e)}
    
    def launch_libreoffice(self):
        """Launch and position LibreOffice"""
        global lo_process, container_bounds
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
            
            container_bounds = self.window.evaluate_js(js_code)
            logger.info(f"Container bounds: {container_bounds}")
            
            if not container_bounds:
                return {"success": False, "error": "Could not get container bounds"}
            
            # Create test document
            test_file = Path(__file__).parent / "test_doc.odt"
            test_file.write_text("LibreOffice Overlay Test")
            
            # Launch LibreOffice
            cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
            lo_process = subprocess.Popen(cmd)
            logger.info(f"LibreOffice launched with PID: {lo_process.pid}")
            
            # Position in background
            threading.Thread(target=position_window, args=(lo_process.pid,), daemon=True).start()
            
            return {"success": True, "pid": lo_process.pid}
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"success": False, "error": str(e)}
    
    def close_document(self):
        """Close LibreOffice"""
        global lo_process
        logger.info("close_document called")
        
        if lo_process:
            lo_process.terminate()
            lo_process = None
            return {"success": True}
        return {"success": False, "error": "No document open"}

def position_window(pid):
    """Position LibreOffice window"""
    global lo_window_id, container_bounds
    
    time.sleep(3)  # Wait for window
    
    try:
        # Find window
        result = subprocess.run(
            ['xdotool', 'search', '--pid', str(pid)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_ids = result.stdout.strip().split('\n')
            lo_window_id = window_ids[-1]
            logger.info(f"Found window: {lo_window_id}")
            
            # Position and resize
            subprocess.run([
                'xdotool', 'windowmove', lo_window_id,
                str(container_bounds['x']),
                str(container_bounds['y'])
            ])
            
            subprocess.run([
                'xdotool', 'windowsize', lo_window_id,
                str(container_bounds['width']),
                str(container_bounds['height'])
            ])
            
            logger.info("Window positioned")
            
    except Exception as e:
        logger.error(f"Position error: {e}")

def create_app():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LibreOffice Overlay - Final</title>
        <style>
            body { 
                font-family: Arial, sans-serif;
                margin: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            #header {
                background: #2196F3;
                color: white;
                padding: 20px;
                text-align: center;
            }
            #controls {
                padding: 20px;
                background: #f5f5f5;
                display: flex;
                gap: 10px;
                align-items: center;
            }
            button {
                padding: 10px 20px;
                font-size: 16px;
                border: none;
                background: #4CAF50;
                color: white;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background: #45a049;
            }
            #status {
                margin-left: auto;
                padding: 10px;
                background: white;
                border-radius: 4px;
            }
            #doc-container {
                flex: 1;
                margin: 20px;
                border: 3px solid #2196F3;
                border-radius: 8px;
                background: white;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            }
            #placeholder {
                text-align: center;
                color: #666;
            }
            .success { color: #4CAF50; }
            .error { color: #f44336; }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>LibreOffice Overlay Test</h1>
            <p>Based on working Ultra Simple pattern</p>
        </div>
        
        <div id="controls">
            <button onclick="testAPI()">Test API</button>
            <button onclick="checkLO()">Check LibreOffice</button>
            <button onclick="openDoc()">Open Document</button>
            <button onclick="closeDoc()">Close Document</button>
            <span id="status">Ready</span>
        </div>
        
        <div id="doc-container">
            <div id="placeholder">
                <h2>Document Viewer Area</h2>
                <p>LibreOffice will be positioned here</p>
            </div>
        </div>
        
        <script>
            function setStatus(text, isError = false) {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = isError ? 'error' : (text.includes('✓') ? 'success' : '');
            }
            
            window.addEventListener('pywebviewready', function() {
                console.log('PyWebView ready!');
                setStatus('✓ API Ready');
            });
            
            async function testAPI() {
                try {
                    const result = await pywebview.api.ping();
                    setStatus('✓ API Working: ' + result);
                } catch (e) {
                    setStatus('Error: ' + e, true);
                }
            }
            
            async function checkLO() {
                try {
                    const result = await pywebview.api.check_libreoffice();
                    if (result.available) {
                        setStatus('✓ LibreOffice found: ' + result.path);
                    } else {
                        setStatus('LibreOffice not found', true);
                    }
                } catch (e) {
                    setStatus('Error: ' + e, true);
                }
            }
            
            async function openDoc() {
                try {
                    setStatus('Opening document...');
                    document.getElementById('placeholder').style.display = 'none';
                    
                    const result = await pywebview.api.launch_libreoffice();
                    if (result.success) {
                        setStatus('✓ Document opened (PID: ' + result.pid + ')');
                    } else {
                        setStatus('Error: ' + result.error, true);
                        document.getElementById('placeholder').style.display = 'block';
                    }
                } catch (e) {
                    setStatus('Error: ' + e, true);
                    document.getElementById('placeholder').style.display = 'block';
                }
            }
            
            async function closeDoc() {
                try {
                    const result = await pywebview.api.close_document();
                    if (result.success) {
                        setStatus('Document closed');
                        document.getElementById('placeholder').style.display = 'block';
                    } else {
                        setStatus('Error: ' + result.error, true);
                    }
                } catch (e) {
                    setStatus('Error: ' + e, true);
                }
            }
        </script>
    </body>
    </html>
    """
    
    # Create API
    api = OverlayAPI()
    
    # Create window
    window = webview.create_window(
        'LibreOffice Overlay Test',
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
    print("LibreOffice Overlay Test - Final Working Version")
    print("Based on proven Ultra Simple pattern")
    print("=" * 60)
    create_app()