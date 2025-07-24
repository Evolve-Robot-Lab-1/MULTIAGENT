#!/usr/bin/env python3
"""
Test X11 Window Embedding for LibreOffice
This script tests if we can embed LibreOffice into a PyWebView window on Linux
"""

import os
import sys
import time
import subprocess
import threading
import webview
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

class X11EmbeddingTest:
    def __init__(self):
        self.window = None
        self.lo_process = None
        self.test_file = None
        
    def create_test_document(self):
        """Create a test document if none exists"""
        test_file = Path(__file__).parent / "test_embedding.odt"
        if not test_file.exists():
            # Create a simple ODT file
            test_file.write_text("Test document for embedding")
        return str(test_file)
        
    def get_window_id(self, window_name, timeout=10):
        """Get X11 window ID by window name"""
        print(f"[X11] Searching for window: {window_name}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ['xdotool', 'search', '--name', window_name],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    window_ids = result.stdout.strip().split('\n')
                    window_id = window_ids[0]  # Take first match
                    print(f"[X11] Found window ID: {window_id}")
                    return window_id
                    
            except Exception as e:
                print(f"[X11] Error searching for window: {e}")
                
            time.sleep(0.5)
            
        print(f"[X11] Window '{window_name}' not found after {timeout}s")
        return None
        
    def get_pywebview_window_id(self):
        """Get PyWebView window ID"""
        if not self.window:
            print("[ERROR] PyWebView window not created yet")
            return None
            
        # Try multiple methods to get window ID
        methods = [
            lambda: self.get_window_id("X11 Embedding Test"),
            lambda: self.get_window_id("pywebview"),
            lambda: self._get_window_id_from_pid()
        ]
        
        for method in methods:
            window_id = method()
            if window_id:
                return window_id
                
        return None
        
    def _get_window_id_from_pid(self):
        """Get window ID from process PID"""
        try:
            pid = os.getpid()
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(pid)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                print(f"[X11] Found {len(window_ids)} windows for PID {pid}")
                # Filter for visible windows
                for wid in window_ids:
                    check = subprocess.run(
                        ['xdotool', 'getwindowgeometry', wid],
                        capture_output=True
                    )
                    if check.returncode == 0:
                        print(f"[X11] Using window ID from PID: {wid}")
                        return wid
                        
        except Exception as e:
            print(f"[X11] Error getting window from PID: {e}")
            
        return None
        
    def test_basic_embedding(self):
        """Test basic LibreOffice embedding"""
        print("\n=== Testing Basic LibreOffice Embedding ===\n")
        
        # Get PyWebView window ID
        parent_window_id = self.get_pywebview_window_id()
        if not parent_window_id:
            print("[ERROR] Could not get PyWebView window ID")
            return False
            
        print(f"[SUCCESS] PyWebView window ID: {parent_window_id}")
        
        # Create test document
        self.test_file = self.create_test_document()
        print(f"[INFO] Test document: {self.test_file}")
        
        # Try to launch LibreOffice with parent window
        print("\n[TEST 1] Testing --parent-window-id parameter...")
        cmd = [
            'soffice',
            '--nologo',
            '--norestore',
            '--view',
            f'--parent-window-id={parent_window_id}',
            self.test_file
        ]
        
        try:
            self.lo_process = subprocess.Popen(cmd)
            print(f"[INFO] LibreOffice launched with PID: {self.lo_process.pid}")
            
            # Wait for LibreOffice window
            time.sleep(3)
            
            # Check if it worked
            lo_window_id = self.get_window_id("LibreOffice", timeout=5)
            if lo_window_id:
                print(f"[INFO] LibreOffice window ID: {lo_window_id}")
                
                # Check if it's actually embedded
                result = subprocess.run(
                    ['xwininfo', '-id', lo_window_id],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("[INFO] Window info:")
                    for line in result.stdout.split('\n')[:10]:
                        if line.strip():
                            print(f"  {line.strip()}")
                            
        except Exception as e:
            print(f"[ERROR] Failed to launch LibreOffice: {e}")
            return False
            
        return True
        
    def test_manual_reparenting(self):
        """Test manual window reparenting"""
        print("\n[TEST 2] Testing manual window reparenting...")
        
        # Kill previous LibreOffice if running
        if self.lo_process:
            self.lo_process.terminate()
            time.sleep(1)
            
        # Launch LibreOffice normally
        cmd = ['soffice', '--nologo', '--norestore', '--view', self.test_file]
        self.lo_process = subprocess.Popen(cmd)
        
        # Wait for window
        time.sleep(3)
        lo_window_id = self.get_window_id("LibreOffice", timeout=5)
        
        if not lo_window_id:
            print("[ERROR] Could not find LibreOffice window")
            return False
            
        parent_window_id = self.get_pywebview_window_id()
        if not parent_window_id:
            print("[ERROR] Could not get PyWebView window ID")
            return False
            
        # Try to reparent
        print(f"[INFO] Attempting to reparent {lo_window_id} to {parent_window_id}")
        
        try:
            # Remove decorations
            subprocess.run([
                'xdotool', 'windowmove', lo_window_id, '100', '100'
            ])
            
            subprocess.run([
                'xdotool', 'windowsize', lo_window_id, '800', '600'
            ])
            
            # This would require more complex X11 calls
            print("[INFO] Manual reparenting requires python-xlib or similar")
            print("[INFO] For now, windows are positioned but not embedded")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Reparenting failed: {e}")
            return False
            
    def test_xembed_protocol(self):
        """Test XEmbed protocol support"""
        print("\n[TEST 3] Checking XEmbed protocol support...")
        
        # Check if LibreOffice supports XEmbed
        try:
            result = subprocess.run(
                ['soffice', '--help'],
                capture_output=True,
                text=True
            )
            
            if 'xembed' in result.stdout.lower() or 'parent' in result.stdout.lower():
                print("[INFO] LibreOffice may support embedding")
            else:
                print("[WARNING] No obvious embedding support in help text")
                
            # Check for gtk-socket/plug support
            print("\n[INFO] Checking GTK socket/plug support...")
            check_cmd = ['python3', '-c', 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk; print("GTK3 available")']
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[SUCCESS] GTK3 is available for socket/plug embedding")
            else:
                print("[WARNING] GTK3 not available")
                
        except Exception as e:
            print(f"[ERROR] Could not check embedding support: {e}")
            
        return True
        
    def api_test(self):
        """API endpoint for PyWebView"""
        return {
            'get_window_info': self._get_window_info,
            'test_embedding': self._api_test_embedding,
            'get_container_info': self._get_container_info
        }
        
    def _get_window_info(self):
        """Get current window information"""
        window_id = self.get_pywebview_window_id()
        return {
            'window_id': window_id,
            'pid': os.getpid(),
            'platform': sys.platform
        }
        
    def _api_test_embedding(self):
        """Test embedding via API call"""
        success = self.test_basic_embedding()
        return {'success': success}
        
    def _get_container_info(self, container_id):
        """Get container position and size via JavaScript"""
        if not self.window:
            return {'error': 'Window not ready'}
            
        js_code = f"""
        const container = document.getElementById('{container_id}');
        if (container) {{
            const rect = container.getBoundingClientRect();
            ({{
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height,
                found: true
            }})
        }} else {{
            ({{ found: false }})
        }}
        """
        
        result = self.window.evaluate_js(js_code)
        return result
        
    def run_tests(self):
        """Run embedding tests after window loads"""
        def _run():
            time.sleep(2)  # Wait for window to be ready
            
            print("\n" + "="*50)
            print("X11 LIBREOFFICE EMBEDDING TEST")
            print("="*50)
            
            # Run tests
            self.test_basic_embedding()
            self.test_manual_reparenting()
            self.test_xembed_protocol()
            
            print("\n" + "="*50)
            print("TESTS COMPLETE")
            print("="*50)
            
            # Cleanup
            if self.lo_process:
                print("\n[CLEANUP] Terminating LibreOffice...")
                self.lo_process.terminate()
                
        # Run tests in background thread
        test_thread = threading.Thread(target=_run)
        test_thread.daemon = True
        test_thread.start()
        
    def create_window(self):
        """Create PyWebView window for testing"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>X11 Embedding Test</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f0f0f0;
                }
                #container {
                    width: 900px;
                    height: 600px;
                    background: white;
                    border: 2px solid #333;
                    margin: 20px auto;
                    position: relative;
                    overflow: hidden;
                }
                #controls {
                    text-align: center;
                    margin: 20px;
                }
                button {
                    padding: 10px 20px;
                    margin: 5px;
                    font-size: 16px;
                    cursor: pointer;
                }
                #info {
                    background: #333;
                    color: white;
                    padding: 10px;
                    margin: 20px 0;
                    border-radius: 5px;
                }
                pre {
                    background: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
            </style>
        </head>
        <body>
            <h1>X11 LibreOffice Embedding Test</h1>
            
            <div id="info">
                <strong>Test Status:</strong> Check terminal for test results
            </div>
            
            <div id="controls">
                <button onclick="getWindowInfo()">Get Window Info</button>
                <button onclick="testEmbedding()">Test Embedding</button>
                <button onclick="getContainerInfo()">Get Container Info</button>
            </div>
            
            <div id="container">
                <p style="text-align: center; margin-top: 250px; color: #666;">
                    LibreOffice will be embedded here
                </p>
            </div>
            
            <div id="output">
                <h3>Output:</h3>
                <pre id="output-text">Ready for testing...</pre>
            </div>
            
            <script>
                function updateOutput(text) {
                    document.getElementById('output-text').innerText = 
                        typeof text === 'string' ? text : JSON.stringify(text, null, 2);
                }
                
                async function getWindowInfo() {
                    try {
                        const result = await pywebview.api.get_window_info();
                        updateOutput(result);
                    } catch (e) {
                        updateOutput('Error: ' + e.message);
                    }
                }
                
                async function testEmbedding() {
                    updateOutput('Testing embedding... Check terminal for details.');
                    try {
                        const result = await pywebview.api.test_embedding();
                        updateOutput(result);
                    } catch (e) {
                        updateOutput('Error: ' + e.message);
                    }
                }
                
                async function getContainerInfo() {
                    try {
                        const result = await pywebview.api.get_container_info('container');
                        updateOutput(result);
                    } catch (e) {
                        updateOutput('Error: ' + e.message);
                    }
                }
                
                // Auto-run window info on load
                window.addEventListener('load', () => {
                    setTimeout(getWindowInfo, 1000);
                });
            </script>
        </body>
        </html>
        """
        
        # Create API instance
        api = self.api_test()
        
        # Create window
        self.window = webview.create_window(
            'X11 Embedding Test',
            html=html,
            js_api=api,
            width=1200,
            height=800
        )
        
        # Start tests after window loads
        webview.start(self.run_tests, debug=True)


if __name__ == '__main__':
    print("Starting X11 LibreOffice Embedding Test...")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    
    # Check prerequisites
    prerequisites = ['xdotool', 'xwininfo', 'wmctrl']
    missing = []
    
    for tool in prerequisites:
        result = subprocess.run(['which', tool], capture_output=True)
        if result.returncode != 0:
            missing.append(tool)
            
    if missing:
        print(f"\n[ERROR] Missing required tools: {', '.join(missing)}")
        print("Install with: sudo apt-get install xdotool x11-utils wmctrl")
        sys.exit(1)
        
    # Run test
    test = X11EmbeddingTest()
    test.create_window()