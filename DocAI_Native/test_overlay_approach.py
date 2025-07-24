#!/usr/bin/env python3
"""
Overlay Approach - Position LibreOffice window over container
This is a more reliable fallback if true embedding doesn't work
"""

import os
import sys
import time
import subprocess
import threading
import webview
from pathlib import Path

class OverlayEmbeddingTest:
    def __init__(self):
        self.window = None
        self.lo_process = None
        self.lo_window_id = None
        self.tracking_active = False
        self.container_bounds = None
        
    def create_test_document(self):
        """Create a test document"""
        test_file = Path(__file__).parent / "test_overlay.odt"
        if not test_file.exists():
            test_file.write_text("Overlay Embedding Test Document")
        return str(test_file)
        
    def launch_and_position_libreoffice(self):
        """Launch LibreOffice and position it over container"""
        # Get container position first
        self.container_bounds = self.window.evaluate_js("""
            const container = document.getElementById('doc-container');
            const rect = container.getBoundingClientRect();
            const screenX = window.screenX || window.screenLeft || 0;
            const screenY = window.screenY || window.screenTop || 0;
            ({
                x: Math.round(screenX + rect.left),
                y: Math.round(screenY + rect.top + 75), // Account for window chrome
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            })
        """)
        
        print(f"[INFO] Container bounds: {self.container_bounds}")
        
        # Create test document
        test_file = self.create_test_document()
        
        # Launch LibreOffice
        cmd = ['soffice', '--nologo', '--norestore', '--view', test_file]
        
        try:
            self.lo_process = subprocess.Popen(cmd)
            print(f"[INFO] LibreOffice launched (PID: {self.lo_process.pid})")
            
            # Wait for window and position it
            threading.Thread(target=self.position_libreoffice_window, daemon=True).start()
            
        except Exception as e:
            print(f"[ERROR] Failed to launch LibreOffice: {e}")
            
    def position_libreoffice_window(self):
        """Find and position LibreOffice window"""
        time.sleep(2)  # Wait for window creation
        
        # Find LibreOffice window
        for attempt in range(10):
            try:
                # Try multiple search methods
                # Method 1: By PID and class
                result = subprocess.run(
                    ['xdotool', 'search', '--pid', str(self.lo_process.pid), '--class', 'libreoffice'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0 or not result.stdout.strip():
                    # Method 2: Just by PID
                    result = subprocess.run(
                        ['xdotool', 'search', '--pid', str(self.lo_process.pid)],
                        capture_output=True,
                        text=True
                    )
                
                if result.returncode == 0 and result.stdout.strip():
                    window_ids = result.stdout.strip().split('\n')
                    
                    # Find the main window (usually the last one)
                    for wid in reversed(window_ids):
                        info = subprocess.run(
                            ['xwininfo', '-id', wid],
                            capture_output=True,
                            text=True
                        )
                        
                        if 'LibreOffice' in info.stdout or 'libreoffice' in info.stdout.lower():
                            self.lo_window_id = wid
                            print(f"[INFO] Found LibreOffice window: {wid}")
                            time.sleep(0.5)  # Let window fully initialize
                            self.apply_window_modifications()
                            self.start_position_tracking()
                            return
                            
            except Exception as e:
                print(f"[ERROR] Window search error: {e}")
                
            time.sleep(0.5)
            
        print("[ERROR] Could not find LibreOffice window after 10 attempts")
            
    def apply_window_modifications(self):
        """Modify LibreOffice window for overlay mode"""
        if not self.lo_window_id or not self.container_bounds:
            return
            
        try:
            # First, unmap the window to make changes
            subprocess.run(['xdotool', 'windowunmap', self.lo_window_id], capture_output=True)
            time.sleep(0.1)
            
            # Remove window decorations - try multiple methods
            # Method 1: MOTIF hints (most reliable)
            subprocess.run([
                'xprop', '-id', self.lo_window_id,
                '-f', '_MOTIF_WM_HINTS', '32c',
                '-set', '_MOTIF_WM_HINTS', '2, 0, 0, 0, 0'
            ], capture_output=True)
            
            # Method 2: GTK frame extents
            subprocess.run([
                'xprop', '-id', self.lo_window_id,
                '-remove', '_GTK_FRAME_EXTENTS'
            ], capture_output=True)
            
            # Method 3: Using wmctrl
            subprocess.run([
                'wmctrl', '-i', '-r', self.lo_window_id,
                '-b', 'add,undecorated'
            ], capture_output=True)
            
            # Set window type to utility (helps with some WMs)
            subprocess.run([
                'xprop', '-id', self.lo_window_id,
                '-f', '_NET_WM_WINDOW_TYPE', '32a',
                '-set', '_NET_WM_WINDOW_TYPE', '_NET_WM_WINDOW_TYPE_UTILITY'
            ], capture_output=True)
            
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
            
            # Remap the window
            subprocess.run(['xdotool', 'windowmap', self.lo_window_id], capture_output=True)
            
            # Keep on top but not as a dialog
            subprocess.run([
                'wmctrl', '-i', '-r', self.lo_window_id,
                '-b', 'add,above,sticky'
            ], capture_output=True)
            
            # Focus the PyWebView window to keep it as the main window
            time.sleep(0.1)
            subprocess.run(['xdotool', 'windowfocus', str(self.window.uid)], capture_output=True)
            
            print("[INFO] Window positioned and modified successfully")
            
        except Exception as e:
            print(f"[ERROR] Window modification failed: {e}")
            
    def start_position_tracking(self):
        """Start tracking container position"""
        self.tracking_active = True
        
        def track():
            while self.tracking_active and self.lo_window_id:
                try:
                    # Get current container position
                    bounds = self.window.evaluate_js("""
                        const container = document.getElementById('doc-container');
                        if (container) {
                            const rect = container.getBoundingClientRect();
                            const screenX = window.screenX || window.screenLeft || 0;
                            const screenY = window.screenY || window.screenTop || 0;
                            ({
                                x: Math.round(screenX + rect.left),
                                y: Math.round(screenY + rect.top + 75),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            })
                        }
                    """)
                    
                    if bounds and bounds != self.container_bounds:
                        self.container_bounds = bounds
                        
                        # Update LibreOffice position
                        subprocess.run([
                            'xdotool', 'windowmove', self.lo_window_id,
                            str(bounds['x']), str(bounds['y'])
                        ], capture_output=True)
                        
                        subprocess.run([
                            'xdotool', 'windowsize', self.lo_window_id,
                            str(bounds['width']), str(bounds['height'])
                        ], capture_output=True)
                        
                except Exception as e:
                    pass
                    
                time.sleep(0.1)
                
        threading.Thread(target=track, daemon=True).start()
        
    def stop_tracking(self):
        """Stop position tracking"""
        self.tracking_active = False
        
        if self.lo_process:
            self.lo_process.terminate()
            
    def api_handler(self):
        """API for PyWebView"""
        class API:
            def __init__(self, app):
                self.app = app
                
            def launch_libreoffice(self):
                return self.app.launch_and_position_libreoffice()
                
            def stop_tracking(self):
                return self.app.stop_tracking()
                
            def get_status(self):
                return {
                    'running': self.app.lo_process is not None,
                    'window_id': self.app.lo_window_id,
                    'tracking': self.app.tracking_active
                }
                
        return API(self)
        
    def create_window(self):
        """Create PyWebView window"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Overlay Embedding Test</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    overflow: hidden;
                }
                
                #header {
                    background: #2c3e50;
                    color: white;
                    padding: 10px 20px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    height: 50px;
                }
                
                #main-container {
                    display: flex;
                    height: calc(100vh - 70px);
                }
                
                #sidebar {
                    width: 250px;
                    background: #34495e;
                    color: white;
                    padding: 20px;
                }
                
                #content-area {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }
                
                #controls {
                    background: #ecf0f1;
                    padding: 10px;
                    border-bottom: 1px solid #bdc3c7;
                }
                
                #doc-container {
                    flex: 1;
                    background: #ffffff;
                    position: relative;
                    overflow: hidden;
                    border: 2px solid #3498db;
                    margin: 10px;
                }
                
                #placeholder {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    color: #7f8c8d;
                    font-size: 24px;
                }
                
                button {
                    padding: 8px 16px;
                    margin: 0 5px;
                    background: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                
                button:hover {
                    background: #2980b9;
                }
                
                #status {
                    margin-left: 20px;
                    color: #2c3e50;
                }
            </style>
        </head>
        <body>
            <div id="header">
                <h1>DocAI Native - Overlay Embedding Test</h1>
                <div>Simulating PyWebView App Layout</div>
            </div>
            
            <div id="main-container">
                <div id="sidebar">
                    <h3>Files</h3>
                    <p>File list would go here...</p>
                </div>
                
                <div id="content-area">
                    <div id="controls">
                        <button onclick="launchLibreOffice()">Open Document</button>
                        <button onclick="stopTracking()">Close Document</button>
                        <span id="status">Ready</span>
                    </div>
                    
                    <div id="doc-container">
                        <div id="placeholder">
                            LibreOffice will appear here
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                async function launchLibreOffice() {
                    document.getElementById('status').textContent = 'Launching...';
                    document.getElementById('placeholder').style.display = 'none';
                    
                    try {
                        await pywebview.api.launch_libreoffice();
                        document.getElementById('status').textContent = 'Document open';
                    } catch (e) {
                        document.getElementById('status').textContent = 'Error: ' + e;
                    }
                }
                
                async function stopTracking() {
                    try {
                        await pywebview.api.stop_tracking();
                        document.getElementById('status').textContent = 'Document closed';
                        document.getElementById('placeholder').style.display = 'flex';
                    } catch (e) {
                        document.getElementById('status').textContent = 'Error: ' + e;
                    }
                }
                
                // Monitor window movement
                let lastPosition = { x: window.screenX, y: window.screenY };
                
                setInterval(() => {
                    if (window.screenX !== lastPosition.x || window.screenY !== lastPosition.y) {
                        lastPosition = { x: window.screenX, y: window.screenY };
                        console.log('Window moved to:', lastPosition);
                    }
                }, 100);
            </script>
        </body>
        </html>
        """
        
        api = self.api_handler()
        
        self.window = webview.create_window(
            'Overlay Embedding Test',
            html=html,
            js_api=api,
            width=1200,
            height=800,
            resizable=True
        )
        
        webview.start(debug=True)


if __name__ == '__main__':
    print("Overlay Approach - LibreOffice Positioning Test")
    print("This simulates embedding by positioning LibreOffice over the container")
    print("-" * 60)
    
    app = OverlayEmbeddingTest()
    app.create_window()