#!/usr/bin/env python3
"""
LibreOffice Container Fit - Final Solution
Complete window decoration removal and precise positioning
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
window_ref = None
lo_process = None
lo_window_id = None
container_bounds = None

class ContainerFitAPI:
    def ping(self):
        """Test method"""
        logger.info("ping called!")
        return "pong"
    
    def check_tools(self):
        """Check if required tools are installed"""
        tools = ['wmctrl', 'xdotool', 'xprop', 'xwininfo']
        results = {}
        for tool in tools:
            result = subprocess.run(['which', tool], capture_output=True)
            results[tool] = result.returncode == 0
        return results
    
    def launch_libreoffice(self):
        """Launch and fit LibreOffice in container"""
        global lo_process, container_bounds, window_ref, lo_window_id
        logger.info("launch_libreoffice called")
        
        if not window_ref:
            return {"success": False, "error": "Window not ready"}
        
        try:
            # Get precise container bounds
            js_code = """
            (function() {
                var container = document.getElementById('doc-container');
                if (!container) return null;
                
                var rect = container.getBoundingClientRect();
                var style = window.getComputedStyle(container);
                
                // Account for container border
                var borderTop = parseInt(style.borderTopWidth) || 0;
                var borderLeft = parseInt(style.borderLeftWidth) || 0;
                var borderRight = parseInt(style.borderRightWidth) || 0;
                var borderBottom = parseInt(style.borderBottomWidth) || 0;
                
                // Calculate inner dimensions
                var innerWidth = rect.width - borderLeft - borderRight;
                var innerHeight = rect.height - borderTop - borderBottom;
                
                // Estimate window chrome (title bar, etc)
                var chromeHeight = window.outerHeight - window.innerHeight;
                var chromeWidth = window.outerWidth - window.innerWidth;
                
                return {
                    // Outer position (including borders)
                    outerX: Math.round(window.screenX + rect.left),
                    outerY: Math.round(window.screenY + rect.top + chromeHeight),
                    
                    // Inner position (content area)
                    x: Math.round(window.screenX + rect.left + borderLeft),
                    y: Math.round(window.screenY + rect.top + borderTop + chromeHeight),
                    width: Math.round(innerWidth),
                    height: Math.round(innerHeight),
                    
                    // Debug info
                    debug: {
                        containerWidth: rect.width,
                        containerHeight: rect.height,
                        borderTop: borderTop,
                        borderLeft: borderLeft,
                        chromeHeight: chromeHeight
                    }
                };
            })()
            """
            
            container_bounds = window_ref.evaluate_js(js_code)
            logger.info(f"Container bounds: {container_bounds}")
            
            if not container_bounds:
                return {"success": False, "error": "Could not get container bounds"}
            
            # Highlight container for visual feedback
            window_ref.evaluate_js("""
                document.getElementById('doc-container').style.boxShadow = '0 0 20px rgba(103, 58, 183, 0.8)';
                setTimeout(() => {
                    document.getElementById('doc-container').style.boxShadow = '';
                }, 3000);
            """)
            
            # Create test document
            test_file = Path(__file__).parent / "container_test.odt"
            test_file.write_text("LibreOffice Container Fit Test")
            
            # Launch LibreOffice with specific options
            cmd = [
                'soffice',
                '--nologo',
                '--norestore', 
                '--nodefault',
                '--nolockcheck',
                '--view',
                str(test_file)
            ]
            
            lo_process = subprocess.Popen(cmd)
            logger.info(f"LibreOffice launched with PID: {lo_process.pid}")
            
            # Start fitting process
            threading.Thread(target=fit_window_to_container, daemon=True).start()
            
            return {"success": True, "pid": lo_process.pid, "bounds": container_bounds}
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def refit_window(self):
        """Manually refit the window"""
        if lo_window_id:
            fit_specific_window(lo_window_id)
            return {"success": True}
        return {"success": False, "error": "No window to refit"}
    
    def adjust_position(self, dx=0, dy=0, dw=0, dh=0):
        """Fine-tune window position"""
        global container_bounds, lo_window_id
        
        if not lo_window_id or not container_bounds:
            return {"success": False, "error": "No window or bounds"}
        
        try:
            # Update bounds
            container_bounds['x'] += dx
            container_bounds['y'] += dy
            container_bounds['width'] += dw
            container_bounds['height'] += dh
            
            # Apply new position
            fit_specific_window(lo_window_id)
            
            return {
                "success": True,
                "new_bounds": {
                    "x": container_bounds['x'],
                    "y": container_bounds['y'],
                    "width": container_bounds['width'],
                    "height": container_bounds['height']
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close_document(self):
        """Close LibreOffice"""
        global lo_process, lo_window_id
        logger.info("close_document called")
        
        if lo_process:
            lo_process.terminate()
            lo_process = None
            lo_window_id = None
            return {"success": True}
        return {"success": False, "error": "No document open"}

def fit_window_to_container():
    """Fit LibreOffice window to container with retries"""
    global lo_window_id, lo_process
    
    # Wait for window to appear
    for i in range(10):
        time.sleep(1)
        
        # Find LibreOffice windows
        result = subprocess.run(
            ['xdotool', 'search', '--pid', str(lo_process.pid), '--class', 'libreoffice'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            window_ids = result.stdout.strip().split('\n')
            
            # Try each window
            for wid in window_ids:
                # Get window name
                name_result = subprocess.run(
                    ['xdotool', 'getwindowname', wid],
                    capture_output=True,
                    text=True
                )
                
                if name_result.returncode == 0:
                    window_name = name_result.stdout.strip()
                    logger.info(f"Found window {wid}: {window_name}")
                    
                    # Skip splash/startup windows
                    if 'libreoffice' in window_name.lower() and 'start' not in window_name.lower():
                        lo_window_id = wid
                        fit_specific_window(wid)
                        return
        
        logger.info(f"Waiting for window... attempt {i+1}")
    
    logger.error("Could not find LibreOffice window after 10 attempts")

def fit_specific_window(window_id):
    """Fit a specific window to container with complete decoration removal"""
    global container_bounds
    
    if not container_bounds:
        logger.error("No container bounds")
        return
    
    try:
        logger.info(f"Fitting window {window_id} to container")
        
        # Step 1: Remove ALL window decorations using xprop
        # Remove window decorations using _MOTIF_WM_HINTS
        motif_hints = "0x2, 0x0, 0x0, 0x0, 0x0"  # No decorations
        subprocess.run([
            'xprop', '-id', window_id,
            '-format', '_MOTIF_WM_HINTS', '32c',
            '-set', '_MOTIF_WM_HINTS', motif_hints
        ])
        
        # Step 2: Set window type to make it behave like embedded window
        subprocess.run([
            'xprop', '-id', window_id,
            '-remove', '_NET_WM_WINDOW_TYPE'
        ])
        
        subprocess.run([
            'xprop', '-id', window_id,
            '-format', '_NET_WM_WINDOW_TYPE', '32a',
            '-set', '_NET_WM_WINDOW_TYPE', '_NET_WM_WINDOW_TYPE_NORMAL'
        ])
        
        # Step 3: Remove window from taskbar
        subprocess.run([
            'xprop', '-id', window_id,
            '-format', '_NET_WM_STATE', '32a',
            '-set', '_NET_WM_STATE', '_NET_WM_STATE_SKIP_TASKBAR'
        ])
        
        # Step 4: Use wmctrl to ensure decorations are removed
        subprocess.run([
            'wmctrl', '-i', '-r', window_id,
            '-b', 'add,undecorated'
        ])
        
        # Step 5: Position and resize window
        # Use xdotool for precise control
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
        
        # Step 6: Raise window and keep it on top temporarily
        subprocess.run(['xdotool', 'windowraise', window_id])
        subprocess.run(['xdotool', 'windowfocus', window_id])
        
        # Step 7: Final adjustment using wmctrl
        geometry = f"0,{container_bounds['x']},{container_bounds['y']},{container_bounds['width']},{container_bounds['height']}"
        subprocess.run([
            'wmctrl', '-i', '-r', window_id,
            '-e', geometry
        ])
        
        logger.info(f"Window {window_id} fitted to container at {geometry}")
        
        # Log actual window position for debugging
        get_window_info(window_id)
        
    except Exception as e:
        logger.error(f"Error fitting window: {e}")

def get_window_info(window_id):
    """Get detailed window information for debugging"""
    try:
        # Get window geometry
        result = subprocess.run(
            ['xwininfo', '-id', window_id],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            output = result.stdout
            # Extract position and size
            for line in output.split('\n'):
                if 'Absolute upper-left X:' in line or \
                   'Absolute upper-left Y:' in line or \
                   'Width:' in line or \
                   'Height:' in line:
                    logger.info(f"Window info: {line.strip()}")
    except Exception as e:
        logger.error(f"Error getting window info: {e}")

def create_app():
    global window_ref
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LibreOffice Container Fit - Final</title>
        <style>
            body { 
                font-family: -apple-system, Arial, sans-serif;
                margin: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
                background: #f0f0f0;
            }
            
            #header {
                background: linear-gradient(135deg, #673AB7 0%, #512DA8 100%);
                color: white;
                padding: 1rem;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }
            
            #header h1 {
                margin: 0;
                font-size: 1.5rem;
                font-weight: 300;
            }
            
            #controls {
                padding: 1rem;
                background: white;
                display: flex;
                gap: 0.5rem;
                align-items: center;
                flex-wrap: wrap;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            button {
                padding: 0.5rem 1rem;
                font-size: 0.875rem;
                border: none;
                background: #673AB7;
                color: white;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            button:hover {
                background: #512DA8;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(103, 58, 183, 0.3);
            }
            
            button:active {
                transform: translateY(0);
            }
            
            .adjust-btn {
                background: #9E9E9E;
                padding: 0.25rem 0.5rem;
                font-size: 0.75rem;
            }
            
            .adjust-btn:hover {
                background: #757575;
            }
            
            #status {
                margin-left: auto;
                padding: 0.5rem 1rem;
                background: #f5f5f5;
                border-radius: 20px;
                font-size: 0.875rem;
            }
            
            #main-content {
                flex: 1;
                padding: 1rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            #doc-container {
                width: 90%;
                height: 90%;
                max-width: 1200px;
                max-height: 800px;
                border: 4px solid #673AB7;
                border-radius: 8px;
                background: white;
                position: relative;
                overflow: hidden;
                transition: box-shadow 0.3s;
            }
            
            #doc-container.highlighting {
                box-shadow: 0 0 30px rgba(103, 58, 183, 0.6);
            }
            
            #placeholder {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                color: #999;
                pointer-events: none;
                transition: opacity 0.3s;
            }
            
            #placeholder h2 {
                color: #666;
                font-weight: 300;
            }
            
            .success { color: #4CAF50; }
            .error { color: #f44336; }
            
            #debug-info {
                position: fixed;
                bottom: 1rem;
                right: 1rem;
                background: rgba(0,0,0,0.8);
                color: #0f0;
                padding: 0.5rem 1rem;
                font-family: monospace;
                font-size: 0.75rem;
                border-radius: 4px;
                max-width: 300px;
            }
            
            #adjustment-controls {
                display: flex;
                gap: 1rem;
                align-items: center;
                padding: 0.5rem;
                background: #f5f5f5;
                border-radius: 4px;
            }
            
            .adjust-group {
                display: flex;
                gap: 0.25rem;
                align-items: center;
            }
            
            .adjust-label {
                font-size: 0.75rem;
                color: #666;
                margin-right: 0.25rem;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>LibreOffice Container Fit - Complete Integration</h1>
        </div>
        
        <div id="controls">
            <button onclick="checkTools()">Check Tools</button>
            <button onclick="openDoc()">Open Document</button>
            <button onclick="refitWindow()">Refit Window</button>
            <button onclick="closeDoc()">Close Document</button>
            
            <div id="adjustment-controls">
                <div class="adjust-group">
                    <span class="adjust-label">X:</span>
                    <button class="adjust-btn" onclick="adjust(-5, 0, 0, 0)">-5</button>
                    <button class="adjust-btn" onclick="adjust(5, 0, 0, 0)">+5</button>
                </div>
                <div class="adjust-group">
                    <span class="adjust-label">Y:</span>
                    <button class="adjust-btn" onclick="adjust(0, -5, 0, 0)">-5</button>
                    <button class="adjust-btn" onclick="adjust(0, 5, 0, 0)">+5</button>
                </div>
                <div class="adjust-group">
                    <span class="adjust-label">W:</span>
                    <button class="adjust-btn" onclick="adjust(0, 0, -5, 0)">-5</button>
                    <button class="adjust-btn" onclick="adjust(0, 0, 5, 0)">+5</button>
                </div>
                <div class="adjust-group">
                    <span class="adjust-label">H:</span>
                    <button class="adjust-btn" onclick="adjust(0, 0, 0, -5)">-5</button>
                    <button class="adjust-btn" onclick="adjust(0, 0, 0, 5)">+5</button>
                </div>
            </div>
            
            <span id="status">Ready</span>
        </div>
        
        <div id="main-content">
            <div id="doc-container">
                <div id="placeholder">
                    <h2>Document Container</h2>
                    <p>LibreOffice will be fitted inside this container</p>
                    <p>The container border will be preserved</p>
                </div>
            </div>
        </div>
        
        <div id="debug-info"></div>
        
        <script>
            let containerBounds = null;
            
            function setStatus(text, isError = false) {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = isError ? 'error' : (text.includes('SUCCESS') ? 'success' : '');
            }
            
            function updateDebugInfo() {
                const container = document.getElementById('doc-container');
                const rect = container.getBoundingClientRect();
                const debug = document.getElementById('debug-info');
                
                containerBounds = {
                    x: Math.round(window.screenX + rect.left),
                    y: Math.round(window.screenY + rect.top),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                };
                
                debug.innerHTML = `Container:<br>
                    Pos: ${containerBounds.x}, ${containerBounds.y}<br>
                    Size: ${containerBounds.width} × ${containerBounds.height}`;
            }
            
            window.addEventListener('pywebviewready', function() {
                setStatus('API Ready');
                updateDebugInfo();
            });
            
            window.addEventListener('resize', updateDebugInfo);
            window.addEventListener('move', updateDebugInfo);
            
            async function checkTools() {
                try {
                    const result = await pywebview.api.check_tools();
                    const missing = Object.entries(result)
                        .filter(([tool, installed]) => !installed)
                        .map(([tool]) => tool);
                    
                    if (missing.length === 0) {
                        setStatus('SUCCESS: All tools installed');
                    } else {
                        setStatus('Missing tools: ' + missing.join(', '), true);
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
            
            async function openDoc() {
                try {
                    setStatus('Opening document...');
                    document.getElementById('doc-container').classList.add('highlighting');
                    document.getElementById('placeholder').style.opacity = '0.2';
                    
                    const result = await pywebview.api.launch_libreoffice();
                    if (result.success) {
                        setStatus('SUCCESS: Fitting window...');
                        setTimeout(() => {
                            document.getElementById('doc-container').classList.remove('highlighting');
                            document.getElementById('placeholder').style.display = 'none';
                        }, 3000);
                    } else {
                        setStatus('ERROR: ' + result.error, true);
                        document.getElementById('placeholder').style.opacity = '1';
                        document.getElementById('doc-container').classList.remove('highlighting');
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                    document.getElementById('placeholder').style.opacity = '1';
                }
            }
            
            async function refitWindow() {
                try {
                    setStatus('Refitting window...');
                    const result = await pywebview.api.refit_window();
                    if (result.success) {
                        setStatus('Window refitted');
                    } else {
                        setStatus('ERROR: ' + result.error, true);
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
            
            async function adjust(dx, dy, dw, dh) {
                try {
                    const result = await pywebview.api.adjust_position(dx, dy, dw, dh);
                    if (result.success) {
                        const b = result.new_bounds;
                        document.getElementById('debug-info').innerHTML += 
                            `<br>Adjusted to:<br>${b.x}, ${b.y} | ${b.width}×${b.height}`;
                    }
                } catch (e) {
                    console.error('Adjust error:', e);
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
            
            // Update debug info periodically
            setInterval(updateDebugInfo, 1000);
        </script>
    </body>
    </html>
    """
    
    # Create API
    api = ContainerFitAPI()
    
    # Create window
    window_ref = webview.create_window(
        'LibreOffice Container Fit',
        html=html,
        js_api=api,
        width=1400,
        height=900,
        resizable=True
    )
    
    # Start
    webview.start(debug=True)

if __name__ == '__main__':
    print("=" * 60)
    print("LibreOffice Container Fit - Final Solution")
    print("=" * 60)
    print()
    print("Features:")
    print("- Complete window decoration removal")
    print("- Precise positioning with visual feedback")
    print("- Manual adjustment controls")
    print("- Debug information display")
    print()
    print("Required tools: wmctrl, xdotool, xprop, xwininfo")
    print("-" * 60)
    
    create_app()