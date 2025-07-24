#!/usr/bin/env python3
"""
LibreOffice Overlay Test - Exact Ultra Simple Pattern
"""

import webview
import logging
import subprocess
import threading
import time
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Global window reference
window_ref = None
lo_process = None
container_bounds = None

# Simple class matching ultra-simple pattern exactly
class OverlayAPI:
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
        global lo_process, container_bounds, window_ref
        logger.info("launch_libreoffice called")
        
        if not window_ref:
            return {"success": False, "error": "Window not ready"}
        
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
            
            container_bounds = window_ref.evaluate_js(js_code)
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
    global container_bounds
    
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
            window_id = window_ids[-1]
            logger.info(f"Found window: {window_id}")
            
            # Position and resize
            subprocess.run([
                'xdotool', 'windowmove', window_id,
                str(container_bounds['x']),
                str(container_bounds['y'])
            ])
            
            subprocess.run([
                'xdotool', 'windowsize', window_id,
                str(container_bounds['width']),
                str(container_bounds['height'])
            ])
            
            logger.info("Window positioned")
            
    except Exception as e:
        logger.error(f"Position error: {e}")

def create_app():
    global window_ref
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LibreOffice Overlay - Working</title>
        <style>
            body { 
                font-family: Arial, sans-serif;
                margin: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            #header {
                background: #4CAF50;
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
                background: #2196F3;
                color: white;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background: #1976D2;
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
            <p>Using exact Ultra Simple pattern</p>
        </div>
        
        <div id="controls">
            <button onclick="testAPI()">Test API</button>
            <button onclick="checkLO()">Check LibreOffice</button>
            <button onclick="openDoc()">Open Document</button>
            <button onclick="closeDoc()">Close Document</button>
            <span id="status">Click Test API first</span>
        </div>
        
        <div id="doc-container">
            <div id="placeholder">
                <h2>Document Viewer Area</h2>
                <p>LibreOffice will be positioned here</p>
            </div>
        </div>
        
        <script>
            console.log('Page loaded');
            
            function setStatus(text, isError = false) {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = isError ? 'error' : (text.includes('SUCCESS') ? 'success' : '');
            }
            
            window.addEventListener('pywebviewready', function() {
                console.log('PyWebView ready!');
                setStatus('API Ready - Click Test API');
            });
            
            async function testAPI() {
                console.log('Testing ping...');
                try {
                    if (!window.pywebview) {
                        throw new Error('pywebview not available');
                    }
                    if (!window.pywebview.api) {
                        throw new Error('pywebview.api not available');
                    }
                    
                    const result = await pywebview.api.ping();
                    console.log('Ping result:', result);
                    setStatus('SUCCESS: ' + result);
                } catch (e) {
                    console.error('Error:', e);
                    setStatus('ERROR: ' + e.message, true);
                }
            }
            
            async function checkLO() {
                try {
                    const result = await pywebview.api.check_libreoffice();
                    if (result.available) {
                        setStatus('SUCCESS: LibreOffice found at ' + result.path);
                    } else {
                        setStatus('LibreOffice not found', true);
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
            
            async function openDoc() {
                try {
                    setStatus('Opening document...');
                    document.getElementById('placeholder').style.display = 'none';
                    
                    const result = await pywebview.api.launch_libreoffice();
                    if (result.success) {
                        setStatus('SUCCESS: Document opened (PID: ' + result.pid + ')');
                    } else {
                        setStatus('ERROR: ' + result.error, true);
                        document.getElementById('placeholder').style.display = 'block';
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
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
                        setStatus('ERROR: ' + result.error, true);
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
        </script>
    </body>
    </html>
    """
    
    # Create API - matching ultra simple exactly
    api = OverlayAPI()
    logger.info(f"API created: {api}")
    logger.info(f"API type: {type(api)}")
    logger.info(f"API ping method: {api.ping}")
    
    # Create window
    window_ref = webview.create_window(
        'LibreOffice Overlay Test',
        html=html,
        js_api=api
    )
    
    # Start
    webview.start(debug=True)

if __name__ == '__main__':
    print("LibreOffice Overlay Test - Working Version")
    print("Using exact Ultra Simple pattern")
    print("-" * 40)
    create_app()