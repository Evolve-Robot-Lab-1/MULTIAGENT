#!/usr/bin/env python3
"""
LibreOffice Overlay Test - Improved Positioning
"""

import webview
import logging
import subprocess
import threading
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global window reference
window_ref = None
lo_process = None
container_bounds = None

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
    
    def get_window_info(self):
        """Get window position for debugging"""
        global window_ref
        if not window_ref:
            return {"error": "Window not ready"}
        
        try:
            js_code = """
            (function() {
                return {
                    screenX: window.screenX,
                    screenY: window.screenY,
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    outerWidth: window.outerWidth,
                    outerHeight: window.outerHeight
                };
            })()
            """
            info = window_ref.evaluate_js(js_code)
            logger.info(f"Window info: {info}")
            return info
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return {"error": str(e)}
    
    def launch_libreoffice(self):
        """Launch and position LibreOffice"""
        global lo_process, container_bounds, window_ref
        logger.info("launch_libreoffice called")
        
        if not window_ref:
            return {"success": False, "error": "Window not ready"}
        
        try:
            # First get window info for debugging
            window_info = self.get_window_info()
            logger.info(f"Current window info: {window_info}")
            
            # Get container bounds with better calculation
            js_code = """
            (function() {
                var container = document.getElementById('doc-container');
                if (!container) return null;
                
                var rect = container.getBoundingClientRect();
                
                // Calculate absolute screen position
                // Account for window decorations (title bar, etc)
                var titleBarHeight = window.outerHeight - window.innerHeight;
                var borderWidth = (window.outerWidth - window.innerWidth) / 2;
                
                return {
                    x: Math.round(window.screenX + borderWidth + rect.left),
                    y: Math.round(window.screenY + titleBarHeight + rect.top),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    // Debug info
                    debug: {
                        screenX: window.screenX,
                        screenY: window.screenY,
                        rectLeft: rect.left,
                        rectTop: rect.top,
                        titleBarHeight: titleBarHeight,
                        borderWidth: borderWidth
                    }
                };
            })()
            """
            
            container_bounds = window_ref.evaluate_js(js_code)
            logger.info(f"Container bounds: {container_bounds}")
            
            if not container_bounds:
                return {"success": False, "error": "Could not get container bounds"}
            
            # Create test document
            test_file = Path(__file__).parent / "test_doc.odt"
            test_file.write_text("LibreOffice Overlay Test Document")
            
            # Launch LibreOffice
            cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
            lo_process = subprocess.Popen(cmd)
            logger.info(f"LibreOffice launched with PID: {lo_process.pid}")
            
            # Position in background with delay
            threading.Thread(target=position_window_improved, args=(lo_process.pid,), daemon=True).start()
            
            return {"success": True, "pid": lo_process.pid, "bounds": container_bounds}
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
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
    
    def reposition_window(self):
        """Manually trigger repositioning"""
        global lo_process
        if lo_process:
            threading.Thread(target=position_window_improved, args=(lo_process.pid,), daemon=True).start()
            return {"success": True}
        return {"success": False, "error": "No document open"}

def position_window_improved(pid):
    """Improved window positioning with retries"""
    global container_bounds
    
    # Wait for window to fully load
    time.sleep(4)
    
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            # Find all windows for this PID
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(pid)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                logger.info(f"Found {len(window_ids)} windows for PID {pid}")
                
                # Try each window ID
                for window_id in window_ids:
                    # Get window info
                    info_result = subprocess.run(
                        ['xdotool', 'getwindowname', window_id],
                        capture_output=True,
                        text=True
                    )
                    
                    window_name = info_result.stdout.strip() if info_result.returncode == 0 else "Unknown"
                    logger.info(f"Window {window_id}: {window_name}")
                    
                    # Skip splash screens and dialogs
                    if 'splash' in window_name.lower() or window_name == "":
                        continue
                    
                    # This looks like the main window
                    logger.info(f"Positioning window {window_id} to {container_bounds['x']}, {container_bounds['y']}")
                    
                    # Remove window decorations first
                    subprocess.run([
                        'wmctrl', '-i', '-r', window_id,
                        '-b', 'add,undecorated'
                    ])
                    
                    # Move window
                    subprocess.run([
                        'xdotool', 'windowmove', window_id,
                        str(container_bounds['x']),
                        str(container_bounds['y'])
                    ])
                    
                    # Resize window
                    subprocess.run([
                        'xdotool', 'windowsize', window_id,
                        str(container_bounds['width']),
                        str(container_bounds['height'])
                    ])
                    
                    # Bring to front
                    subprocess.run(['xdotool', 'windowactivate', window_id])
                    
                    logger.info(f"Window {window_id} positioned successfully")
                    return
                
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Position error on attempt {attempt + 1}: {e}")
            time.sleep(1)
    
    logger.error("Failed to position window after all attempts")

def create_app():
    global window_ref
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LibreOffice Overlay - Improved</title>
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
                padding: 15px;
                text-align: center;
            }
            #controls {
                padding: 15px;
                background: #f5f5f5;
                display: flex;
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
            }
            button {
                padding: 8px 16px;
                font-size: 14px;
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
                padding: 8px;
                background: white;
                border-radius: 4px;
                font-size: 14px;
            }
            #doc-container {
                flex: 1;
                margin: 15px;
                border: 3px solid #2196F3;
                border-radius: 8px;
                background: white;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }
            #placeholder {
                text-align: center;
                color: #666;
                padding: 20px;
            }
            .success { color: #4CAF50; }
            .error { color: #f44336; }
            #debug {
                position: absolute;
                bottom: 10px;
                right: 10px;
                background: rgba(0,0,0,0.7);
                color: #0f0;
                padding: 5px 10px;
                font-family: monospace;
                font-size: 12px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>LibreOffice Overlay Test - Improved</h1>
        </div>
        
        <div id="controls">
            <button onclick="testAPI()">Test API</button>
            <button onclick="checkLO()">Check LibreOffice</button>
            <button onclick="getInfo()">Get Window Info</button>
            <button onclick="openDoc()">Open Document</button>
            <button onclick="reposition()">Reposition</button>
            <button onclick="closeDoc()">Close Document</button>
            <span id="status">Ready</span>
        </div>
        
        <div id="doc-container">
            <div id="placeholder">
                <h2>Document Viewer Area</h2>
                <p>LibreOffice will be positioned here</p>
                <p>Container size: <span id="container-size"></span></p>
            </div>
            <div id="debug"></div>
        </div>
        
        <script>
            function setStatus(text, isError = false) {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = isError ? 'error' : (text.includes('SUCCESS') ? 'success' : '');
            }
            
            function updateContainerSize() {
                const container = document.getElementById('doc-container');
                const rect = container.getBoundingClientRect();
                document.getElementById('container-size').textContent = 
                    `${Math.round(rect.width)} x ${Math.round(rect.height)}`;
                document.getElementById('debug').textContent = 
                    `Pos: ${Math.round(rect.left)}, ${Math.round(rect.top)}`;
            }
            
            window.addEventListener('pywebviewready', function() {
                console.log('PyWebView ready!');
                setStatus('API Ready');
                updateContainerSize();
            });
            
            window.addEventListener('resize', updateContainerSize);
            
            async function testAPI() {
                try {
                    const result = await pywebview.api.ping();
                    setStatus('SUCCESS: ' + result);
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
            
            async function checkLO() {
                try {
                    const result = await pywebview.api.check_libreoffice();
                    if (result.available) {
                        setStatus('SUCCESS: LibreOffice at ' + result.path);
                    } else {
                        setStatus('LibreOffice not found', true);
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
            
            async function getInfo() {
                try {
                    const result = await pywebview.api.get_window_info();
                    setStatus('Window: ' + JSON.stringify(result));
                    console.log('Window info:', result);
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
                        setStatus('SUCCESS: PID ' + result.pid);
                        console.log('Launch result:', result);
                    } else {
                        setStatus('ERROR: ' + result.error, true);
                        document.getElementById('placeholder').style.display = 'block';
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                    document.getElementById('placeholder').style.display = 'block';
                }
            }
            
            async function reposition() {
                try {
                    const result = await pywebview.api.reposition_window();
                    if (result.success) {
                        setStatus('Repositioning...');
                    } else {
                        setStatus('ERROR: ' + result.error, true);
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
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
    
    # Create API
    api = OverlayAPI()
    
    # Create window
    window_ref = webview.create_window(
        'LibreOffice Overlay Test',
        html=html,
        js_api=api,
        width=1200,
        height=800,
        resizable=True
    )
    
    # Start
    webview.start(debug=True)

if __name__ == '__main__':
    print("LibreOffice Overlay Test - Improved Positioning")
    print("Features:")
    print("- Better position calculation")
    print("- Window decoration removal")
    print("- Reposition button for manual adjustment")
    print("- Debug information")
    print("-" * 50)
    create_app()