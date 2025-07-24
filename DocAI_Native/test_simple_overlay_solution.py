#!/usr/bin/env python3
"""
Simple LibreOffice Overlay Solution
Focus on reliable positioning without complex window manipulation
"""

import webview
import logging
import subprocess
import time
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
window_ref = None
lo_process = None
saved_position = None

class SimpleOverlayAPI:
    def ping(self):
        """Test method"""
        return "pong"
    
    def launch_libreoffice(self):
        """Launch LibreOffice and let user position it"""
        global lo_process, window_ref
        
        if not window_ref:
            return {"success": False, "error": "Window not ready"}
        
        try:
            # Get container position for reference
            js_code = """
            (function() {
                var container = document.getElementById('doc-container');
                var rect = container.getBoundingClientRect();
                return {
                    screenX: window.screenX,
                    screenY: window.screenY,
                    containerX: rect.left,
                    containerY: rect.top,
                    containerWidth: rect.width,
                    containerHeight: rect.height
                };
            })()
            """
            
            info = window_ref.evaluate_js(js_code)
            logger.info(f"Container info: {info}")
            
            # Create test document
            test_file = Path(__file__).parent / "overlay_test.odt"
            test_file.write_text("LibreOffice Overlay Document")
            
            # Launch LibreOffice normally
            cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
            lo_process = subprocess.Popen(cmd)
            
            return {
                "success": True,
                "pid": lo_process.pid,
                "instructions": "LibreOffice opened. Please manually resize and position it over the blue container.",
                "container_info": info
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"success": False, "error": str(e)}
    
    def save_position(self):
        """Save current LibreOffice window position"""
        global saved_position
        
        try:
            # Find LibreOffice window
            result = subprocess.run(
                ['wmctrl', '-l', '-G'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'LibreOffice' in line or '.odt' in line:
                        # Parse: ID DESKTOP X Y W H WM_CLASS MACHINE TITLE
                        parts = line.split(None, 7)
                        if len(parts) >= 6:
                            saved_position = {
                                "window_id": parts[0],
                                "x": int(parts[2]),
                                "y": int(parts[3]),
                                "width": int(parts[4]),
                                "height": int(parts[5]),
                                "title": parts[7] if len(parts) > 7 else "LibreOffice"
                            }
                            
                            # Save to file
                            pos_file = Path(__file__).parent / "libreoffice_position.json"
                            pos_file.write_text(json.dumps(saved_position, indent=2))
                            
                            logger.info(f"Saved position: {saved_position}")
                            return {"success": True, "position": saved_position}
                
                return {"success": False, "error": "LibreOffice window not found"}
                
        except Exception as e:
            logger.error(f"Error saving position: {e}")
            return {"success": False, "error": str(e)}
    
    def load_position(self):
        """Load and apply saved position"""
        global saved_position
        
        try:
            # Load saved position
            pos_file = Path(__file__).parent / "libreoffice_position.json"
            if pos_file.exists():
                saved_position = json.loads(pos_file.read_text())
                
                # Find current LibreOffice window
                result = subprocess.run(
                    ['wmctrl', '-l'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'LibreOffice' in line or '.odt' in line:
                            window_id = line.split()[0]
                            
                            # Apply saved position
                            geometry = f"0,{saved_position['x']},{saved_position['y']},{saved_position['width']},{saved_position['height']}"
                            subprocess.run([
                                'wmctrl', '-i', '-r', window_id,
                                '-e', geometry
                            ])
                            
                            return {"success": True, "position": saved_position}
                
                return {"success": False, "error": "LibreOffice window not found"}
            else:
                return {"success": False, "error": "No saved position found"}
                
        except Exception as e:
            logger.error(f"Error loading position: {e}")
            return {"success": False, "error": str(e)}
    
    def close_document(self):
        """Close LibreOffice"""
        global lo_process
        
        if lo_process:
            lo_process.terminate()
            lo_process = None
            return {"success": True}
        return {"success": False, "error": "No document open"}

def create_app():
    global window_ref
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple LibreOffice Overlay</title>
        <style>
            body { 
                font-family: Arial, sans-serif;
                margin: 0;
                height: 100vh;
                display: flex;
                flex-direction: column;
                background: #f5f5f5;
            }
            
            #header {
                background: #2196F3;
                color: white;
                padding: 1rem;
                text-align: center;
            }
            
            #controls {
                padding: 1rem;
                background: white;
                display: flex;
                gap: 1rem;
                align-items: center;
                flex-wrap: wrap;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            button {
                padding: 0.75rem 1.5rem;
                border: none;
                background: #2196F3;
                color: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            
            button:hover {
                background: #1976D2;
            }
            
            #status {
                flex: 1;
                padding: 0.75rem;
                background: #f5f5f5;
                border-radius: 4px;
                font-size: 14px;
                margin-left: 1rem;
            }
            
            #main {
                flex: 1;
                padding: 2rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            #doc-container {
                width: 80%;
                height: 80%;
                max-width: 1000px;
                border: 4px solid #2196F3;
                background: white;
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            #instructions {
                text-align: center;
                padding: 2rem;
                color: #666;
            }
            
            #instructions h2 {
                color: #333;
                margin-bottom: 1rem;
            }
            
            #instructions ol {
                text-align: left;
                display: inline-block;
                line-height: 1.8;
            }
            
            .success { color: #4CAF50; }
            .error { color: #f44336; }
            
            #position-info {
                position: fixed;
                bottom: 1rem;
                right: 1rem;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 0.5rem 1rem;
                font-family: monospace;
                font-size: 12px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div id="header">
            <h1>Simple LibreOffice Overlay Solution</h1>
            <p>Manual positioning with save/load functionality</p>
        </div>
        
        <div id="controls">
            <button onclick="testAPI()">Test API</button>
            <button onclick="openDoc()">Open Document</button>
            <button onclick="savePos()">Save Position</button>
            <button onclick="loadPos()">Load Position</button>
            <button onclick="closeDoc()">Close Document</button>
            <div id="status">Ready</div>
        </div>
        
        <div id="main">
            <div id="doc-container">
                <div id="instructions">
                    <h2>LibreOffice Overlay Instructions</h2>
                    <ol>
                        <li>Click "Open Document" to launch LibreOffice</li>
                        <li>Manually resize and position LibreOffice window to cover this blue container</li>
                        <li>Click "Save Position" to remember the position</li>
                        <li>Next time, use "Load Position" to automatically restore the position</li>
                    </ol>
                    <p><strong>This container represents where LibreOffice should be positioned</strong></p>
                </div>
            </div>
        </div>
        
        <div id="position-info"></div>
        
        <script>
            function setStatus(text, isError = false) {
                const status = document.getElementById('status');
                status.textContent = text;
                status.className = isError ? 'error' : (text.includes('SUCCESS') ? 'success' : '');
            }
            
            function updatePositionInfo() {
                const container = document.getElementById('doc-container');
                const rect = container.getBoundingClientRect();
                const info = document.getElementById('position-info');
                
                info.textContent = `Container: ${Math.round(rect.width)}×${Math.round(rect.height)} at (${Math.round(rect.left)}, ${Math.round(rect.top)})`;
            }
            
            window.addEventListener('pywebviewready', function() {
                setStatus('API Ready');
                updatePositionInfo();
            });
            
            window.addEventListener('resize', updatePositionInfo);
            
            async function testAPI() {
                try {
                    const result = await pywebview.api.ping();
                    setStatus('SUCCESS: API working - ' + result);
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
            
            async function openDoc() {
                try {
                    setStatus('Opening LibreOffice...');
                    const result = await pywebview.api.launch_libreoffice();
                    
                    if (result.success) {
                        setStatus(result.instructions);
                        document.getElementById('instructions').innerHTML += 
                            '<p style="color: #2196F3; margin-top: 1rem;">LibreOffice is now open. Position it over this container.</p>';
                    } else {
                        setStatus('ERROR: ' + result.error, true);
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
            
            async function savePos() {
                try {
                    const result = await pywebview.api.save_position();
                    
                    if (result.success) {
                        const pos = result.position;
                        setStatus(`SUCCESS: Position saved (${pos.width}×${pos.height} at ${pos.x},${pos.y})`);
                    } else {
                        setStatus('ERROR: ' + result.error, true);
                    }
                } catch (e) {
                    setStatus('ERROR: ' + e, true);
                }
            }
            
            async function loadPos() {
                try {
                    setStatus('Loading saved position...');
                    const result = await pywebview.api.load_position();
                    
                    if (result.success) {
                        const pos = result.position;
                        setStatus(`SUCCESS: Position restored (${pos.width}×${pos.height} at ${pos.x},${pos.y})`);
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
                        document.getElementById('instructions').innerHTML = 
                            document.getElementById('instructions').innerHTML.replace(
                                /<p style="color: #2196F3;.*?<\/p>/, ''
                            );
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
    api = SimpleOverlayAPI()
    
    # Create window
    window_ref = webview.create_window(
        'Simple LibreOffice Overlay',
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
    print("Simple LibreOffice Overlay Solution")
    print("=" * 60)
    print()
    print("This solution uses manual positioning with save/load:")
    print("1. Open LibreOffice")
    print("2. Manually position it over the container")
    print("3. Save the position")
    print("4. Load position next time for quick setup")
    print()
    print("This is the most reliable approach for Phase 2")
    print("-" * 60)
    
    create_app()