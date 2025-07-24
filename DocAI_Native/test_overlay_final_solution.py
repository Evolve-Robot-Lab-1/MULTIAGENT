#!/usr/bin/env python3
"""
LibreOffice Overlay Test - Final Solution
Using wmctrl for more reliable window management
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
    
    def launch_libreoffice(self):
        """Launch and position LibreOffice"""
        global lo_process, container_bounds, window_ref
        logger.info("launch_libreoffice called")
        
        if not window_ref:
            return {"success": False, "error": "Window not ready"}
        
        try:
            # Get container bounds - simplified calculation
            js_code = """
            (function() {
                var container = document.getElementById('doc-container');
                if (!container) return null;
                
                var rect = container.getBoundingClientRect();
                
                // Get absolute position
                return {
                    x: Math.round(window.screenX + rect.left),
                    y: Math.round(window.screenY + rect.top + 50), // Approximate title bar
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
            test_file.write_text("LibreOffice Overlay Test Document")
            
            # Get list of windows before launching
            before_windows = get_all_windows()
            
            # Launch LibreOffice
            cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
            lo_process = subprocess.Popen(cmd)
            logger.info(f"LibreOffice launched with PID: {lo_process.pid}")
            
            # Position window after delay
            threading.Thread(
                target=position_window_wmctrl, 
                args=(lo_process.pid, before_windows), 
                daemon=True
            ).start()
            
            return {"success": True, "pid": lo_process.pid}
            
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
    
    def manual_position(self):
        """Manually position LibreOffice window"""
        global lo_process
        if lo_process:
            # Try to find and position window
            position_libreoffice_by_title()
            return {"success": True}
        return {"success": False, "error": "No document open"}

def get_all_windows():
    """Get list of all windows using wmctrl"""
    try:
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        return []
    except:
        return []

def position_window_wmctrl(pid, before_windows):
    """Position window using wmctrl"""
    global container_bounds
    
    # Wait for window to appear
    time.sleep(5)
    
    try:
        # Get current windows
        after_windows = get_all_windows()
        
        # Find new windows (likely LibreOffice)
        new_windows = [w for w in after_windows if w not in before_windows]
        logger.info(f"New windows: {len(new_windows)}")
        
        for window_line in new_windows:
            if 'LibreOffice' in window_line or '.odt' in window_line:
                # Extract window ID (first field)
                window_id = window_line.split()[0]
                logger.info(f"Found LibreOffice window: {window_id}")
                
                # Position window
                position_window_by_id(window_id)
                return
        
        # If not found by new windows, try by title
        position_libreoffice_by_title()
        
    except Exception as e:
        logger.error(f"Error positioning window: {e}")

def position_libreoffice_by_title():
    """Find and position LibreOffice window by title"""
    global container_bounds
    
    try:
        # Get all windows
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            windows = result.stdout.strip().split('\n')
            
            for window_line in windows:
                if 'LibreOffice' in window_line or '.odt' in window_line:
                    window_id = window_line.split()[0]
                    logger.info(f"Found LibreOffice by title: {window_id}")
                    position_window_by_id(window_id)
                    return
                    
    except Exception as e:
        logger.error(f"Error finding window by title: {e}")

def position_window_by_id(window_id):
    """Position a specific window by ID"""
    global container_bounds
    
    if not container_bounds:
        logger.error("No container bounds available")
        return
    
    try:
        # Remove decorations
        subprocess.run([
            'wmctrl', '-i', '-r', window_id,
            '-b', 'remove,maximized_vert,maximized_horz'
        ])
        
        # Move and resize
        # Format: gravity,x,y,width,height
        geometry = f"0,{container_bounds['x']},{container_bounds['y']},{container_bounds['width']},{container_bounds['height']}"
        
        subprocess.run([
            'wmctrl', '-i', '-r', window_id,
            '-e', geometry
        ])
        
        # Raise window
        subprocess.run([
            'wmctrl', '-i', '-r', window_id,
            '-b', 'add,above'
        ])
        
        logger.info(f"Window {window_id} positioned to {geometry}")
        
    except Exception as e:
        logger.error(f"Error positioning window {window_id}: {e}")

def create_app():
    global window_ref
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LibreOffice Overlay - Final Solution</title>
        <style>
            body { 
                font-family: Arial, sans-serif;
                margin: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            #header {
                background: #673AB7;
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
            }
            button {
                padding: 10px 20px;
                font-size: 14px;
                border: none;
                background: #673AB7;
                color: white;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background: #512DA8;
            }
            #status {
                margin-left: auto;
                padding: 10px;
                background: white;
                border-radius: 4px;
                font-size: 14px;
            }
            #doc-container {
                flex: 1;
                margin: 15px;
                border: 4px solid #673AB7;
                border-radius: 8px;
                background: #f5f5f5;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }
            #placeholder {
                text-align: center;
                color: #666;
                padding: 40px;
            }
            .success { color: #4CAF50; }
            .error { color: #f44336; }
            .info {
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px 10px;
                font-family: monospace;
                font-size: 12px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>LibreOffice Overlay Test - Final Solution</h1>
            <p>Using wmctrl for reliable window management</p>
        </div>
        
        <div id="controls">
            <button onclick="testAPI()">Test API</button>
            <button onclick="checkLO()">Check LibreOffice</button>
            <button onclick="openDoc()">Open Document</button>
            <button onclick="manualPos()">Manual Position</button>
            <button onclick="closeDoc()">Close Document</button>
            <span id="status">Ready</span>
        </div>
        
        <div id="doc-container">
            <div id="placeholder">
                <h2>Document Viewer Area</h2>
                <p>LibreOffice will be overlaid here</p>
                <p>If positioning fails, click "Manual Position"</p>
            </div>
            <div class="info" id="info"></div>
        </div>
        
        <script>
            function setStatus(text, isError = false) {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = isError ? 'error' : (text.includes('SUCCESS') ? 'success' : '');
            }
            
            function updateInfo() {
                const container = document.getElementById('doc-container');
                const rect = container.getBoundingClientRect();
                document.getElementById('info').textContent = 
                    `${Math.round(rect.width)}x${Math.round(rect.height)}`;
            }
            
            window.addEventListener('pywebviewready', function() {
                console.log('PyWebView ready!');
                setStatus('API Ready');
                updateInfo();
            });
            
            window.addEventListener('resize', updateInfo);
            
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
                        setStatus('SUCCESS: LibreOffice found');
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
                    document.getElementById('placeholder').style.opacity = '0.3';
                    
                    const result = await pywebview.api.launch_libreoffice();
                    if (result.success) {
                        setStatus('SUCCESS: Document opened');
                        // Hide placeholder text but keep container visible
                        setTimeout(() => {
                            document.getElementById('placeholder').style.display = 'none';
                        }, 6000);
                    } else {
                        setStatus('ERROR: ' + result.error, true);
                        document.getElementById('placeholder').style.opacity = '1';
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                    document.getElementById('placeholder').style.opacity = '1';
                }
            }
            
            async function manualPos() {
                try {
                    setStatus('Positioning...');
                    const result = await pywebview.api.manual_position();
                    if (result.success) {
                        setStatus('Positioned');
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
                        document.getElementById('placeholder').style.opacity = '1';
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
    print("=" * 60)
    print("LibreOffice Overlay Test - Final Solution")
    print("=" * 60)
    print("Using wmctrl for window management")
    print()
    print("Instructions:")
    print("1. Click 'Open Document' to launch LibreOffice")
    print("2. Wait 5-6 seconds for automatic positioning")
    print("3. If positioning fails, click 'Manual Position'")
    print("-" * 60)
    
    # Check for wmctrl
    result = subprocess.run(['which', 'wmctrl'], capture_output=True)
    if result.returncode != 0:
        print("WARNING: wmctrl not found!")
        print("Install with: sudo apt-get install wmctrl")
    
    create_app()