#!/usr/bin/env python3
"""
Simple Overlay Approach - Clean implementation
Focus on getting the concept working first
"""

import os
import sys
import time
import subprocess
import threading
import webview
from pathlib import Path

# Global reference for API
app_instance = None

def launch_libreoffice():
    """Launch LibreOffice and position it"""
    return app_instance.launch_and_position_libreoffice() if app_instance else None

def stop_tracking():
    """Stop tracking and close LibreOffice"""
    return app_instance.stop_tracking() if app_instance else None

def get_status():
    """Get current status"""
    if app_instance:
        return {
            'running': app_instance.lo_process is not None,
            'window_id': app_instance.lo_window_id,
            'tracking': app_instance.tracking_active
        }
    return {'running': False, 'window_id': None, 'tracking': False}

class SimpleOverlayApp:
    def __init__(self):
        self.window = None
        self.lo_process = None
        self.lo_window_id = None
        self.tracking_active = False
        self.container_bounds = None
        
    def create_test_document(self):
        """Create a test document"""
        test_file = Path(__file__).parent / "test_simple_overlay.odt"
        test_file.write_text("Simple Overlay Test Document")
        return str(test_file)
        
    def launch_and_position_libreoffice(self):
        """Launch LibreOffice and position it over container"""
        print("[INFO] Launching LibreOffice...")
        
        # Get container position
        self.container_bounds = self.window.evaluate_js("""
            (() => {
                const container = document.getElementById('doc-container');
                const rect = container.getBoundingClientRect();
                
                // Get window position - try multiple methods
                let screenX = 0, screenY = 0;
                if (window.screenX !== undefined) {
                    screenX = window.screenX;
                    screenY = window.screenY;
                } else if (window.screenLeft !== undefined) {
                    screenX = window.screenLeft;
                    screenY = window.screenTop;
                }
                
                // Adjust for window decorations (approximate)
                const titleBarHeight = 30;
                const menuBarHeight = 50;
                
                return {
                    x: Math.round(screenX + rect.left),
                    y: Math.round(screenY + rect.top + titleBarHeight + menuBarHeight),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                };
            })()
        """)
        
        print(f"[INFO] Container bounds: {self.container_bounds}")
        
        # Create and launch document
        test_file = self.create_test_document()
        cmd = ['soffice', '--nologo', '--norestore', '--view', test_file]
        
        try:
            self.lo_process = subprocess.Popen(cmd)
            print(f"[INFO] LibreOffice launched (PID: {self.lo_process.pid})")
            
            # Start positioning thread
            threading.Thread(target=self.position_window_delayed, daemon=True).start()
            
            return {'success': True, 'message': 'LibreOffice launching...'}
            
        except Exception as e:
            print(f"[ERROR] Failed to launch: {e}")
            return {'success': False, 'error': str(e)}
            
    def position_window_delayed(self):
        """Position window after delay"""
        time.sleep(3)  # Give LibreOffice time to start
        
        # Find window
        for attempt in range(10):
            try:
                # Search by PID
                result = subprocess.run(
                    ['xdotool', 'search', '--pid', str(self.lo_process.pid)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    window_ids = result.stdout.strip().split('\n')
                    
                    # Check each window
                    for wid in window_ids:
                        # Get window name
                        name_result = subprocess.run(
                            ['xdotool', 'getwindowname', wid],
                            capture_output=True,
                            text=True
                        )
                        
                        if name_result.returncode == 0:
                            window_name = name_result.stdout.strip()
                            print(f"[INFO] Found window {wid}: {window_name}")
                            
                            if 'libreoffice' in window_name.lower() or '.odt' in window_name:
                                self.lo_window_id = wid
                                print(f"[INFO] Selected LibreOffice window: {wid}")
                                self.position_window()
                                return
                                
            except Exception as e:
                print(f"[ERROR] Search attempt {attempt + 1} failed: {e}")
                
            time.sleep(0.5)
            
        print("[ERROR] Could not find LibreOffice window")
        
    def position_window(self):
        """Position and modify LibreOffice window"""
        if not self.lo_window_id or not self.container_bounds:
            return
            
        print(f"[INFO] Positioning window {self.lo_window_id}")
        
        try:
            # Simple positioning first
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
            
            print("[INFO] Window positioned")
            
            # Try to remove decorations (may not work on all WMs)
            subprocess.run([
                'wmctrl', '-i', '-r', self.lo_window_id,
                '-b', 'toggle,maximized_vert,maximized_horz'
            ], capture_output=True)
            
            # Then resize again
            time.sleep(0.1)
            
            subprocess.run([
                'xdotool', 'windowsize', self.lo_window_id,
                str(self.container_bounds['width']),
                str(self.container_bounds['height'])
            ])
            
            self.tracking_active = True
            print("[INFO] Positioning complete")
            
        except Exception as e:
            print(f"[ERROR] Positioning failed: {e}")
            
    def stop_tracking(self):
        """Stop tracking and close LibreOffice"""
        print("[INFO] Stopping...")
        self.tracking_active = False
        
        if self.lo_process:
            self.lo_process.terminate()
            self.lo_process = None
            
        self.lo_window_id = None
        return {'success': True, 'message': 'Stopped'}
        
    def create_window(self):
        """Create PyWebView window"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Simple Overlay Test</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                
                body {
                    font-family: Arial, sans-serif;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                
                #header {
                    background: #2c3e50;
                    color: white;
                    padding: 15px;
                    text-align: center;
                }
                
                #controls {
                    background: #ecf0f1;
                    padding: 10px;
                    text-align: center;
                }
                
                button {
                    padding: 10px 20px;
                    margin: 0 5px;
                    background: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }
                
                button:hover {
                    background: #2980b9;
                }
                
                #status {
                    display: inline-block;
                    margin-left: 20px;
                    padding: 10px;
                    background: #fff;
                    border-radius: 4px;
                }
                
                #doc-container {
                    flex: 1;
                    background: #f8f8f8;
                    border: 3px solid #3498db;
                    margin: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    color: #7f8c8d;
                    position: relative;
                }
                
                #placeholder {
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div id="header">
                <h1>Simple LibreOffice Overlay Test</h1>
            </div>
            
            <div id="controls">
                <button onclick="openDocument()">Open Document</button>
                <button onclick="closeDocument()">Close Document</button>
                <span id="status">Ready</span>
            </div>
            
            <div id="doc-container">
                <div id="placeholder">
                    Click "Open Document" to overlay LibreOffice here
                </div>
            </div>
            
            <script>
                function setStatus(text, color = '#000') {
                    const status = document.getElementById('status');
                    status.textContent = text;
                    status.style.color = color;
                }
                
                async function openDocument() {
                    setStatus('Launching LibreOffice...', '#f39c12');
                    document.getElementById('placeholder').style.display = 'none';
                    
                    try {
                        const result = await pywebview.api.launch_libreoffice();
                        if (result.success) {
                            setStatus('Document opened', '#27ae60');
                        } else {
                            setStatus('Error: ' + result.error, '#e74c3c');
                            document.getElementById('placeholder').style.display = 'block';
                        }
                    } catch (e) {
                        setStatus('Error: ' + e, '#e74c3c');
                        document.getElementById('placeholder').style.display = 'block';
                    }
                }
                
                async function closeDocument() {
                    try {
                        await pywebview.api.stop_tracking();
                        setStatus('Document closed', '#000');
                        document.getElementById('placeholder').style.display = 'block';
                    } catch (e) {
                        setStatus('Error: ' + e, '#e74c3c');
                    }
                }
                
                // Log window position for debugging
                setInterval(() => {
                    console.log(`Window at: ${window.screenX}, ${window.screenY}`);
                }, 2000);
            </script>
        </body>
        </html>
        """
        
        # Simple API object
        api = {
            'launch_libreoffice': launch_libreoffice,
            'stop_tracking': stop_tracking,
            'get_status': get_status
        }
        
        self.window = webview.create_window(
            'Simple Overlay Test',
            html=html,
            js_api=api,
            width=1000,
            height=700,
            x=100,
            y=100
        )
        
        webview.start(debug=True)


if __name__ == '__main__':
    print("Simple Overlay Test - LibreOffice Positioning")
    print("=" * 50)
    
    # Check for required tools
    tools = ['xdotool', 'wmctrl']
    missing = []
    
    for tool in tools:
        result = subprocess.run(['which', tool], capture_output=True)
        if result.returncode != 0:
            missing.append(tool)
            
    if missing:
        print(f"Missing tools: {', '.join(missing)}")
        print("Install with: sudo apt-get install xdotool wmctrl")
        sys.exit(1)
        
    # Create global app instance
    app_instance = SimpleOverlayApp()
    app_instance.create_window()