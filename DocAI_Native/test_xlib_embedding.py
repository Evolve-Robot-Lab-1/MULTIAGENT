#!/usr/bin/env python3
"""
Simple X11 Window Embedding Test using python-xlib
Tests if we can embed LibreOffice window into another window
"""

import os
import sys
import time
import subprocess
import tkinter as tk
from pathlib import Path

try:
    from Xlib import X, display
    from Xlib.xobject import drawable
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False
    print("WARNING: python-xlib not installed!")
    print("Install with: pip install python-xlib")

class XlibEmbeddingTest:
    def __init__(self):
        self.root = None
        self.container_frame = None
        self.lo_process = None
        self.display = None
        
    def create_window(self):
        """Create a simple Tkinter window as container"""
        self.root = tk.Tk()
        self.root.title("X11 Embedding Test")
        self.root.geometry("1000x700")
        
        # Header
        header = tk.Label(self.root, text="X11 Window Embedding Test", font=("Arial", 16))
        header.pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Launch LibreOffice", command=self.launch_libreoffice).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Embed Window", command=self.embed_window).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Test Overlay", command=self.test_overlay).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(self.root, text="Ready", fg="blue")
        self.status_label.pack(pady=5)
        
        # Container frame for embedding
        self.container_frame = tk.Frame(self.root, width=900, height=500, bg="lightgray", relief=tk.SUNKEN, bd=2)
        self.container_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.container_frame.pack_propagate(False)
        
        # Add label to container
        tk.Label(self.container_frame, text="LibreOffice will be embedded here", bg="lightgray").pack(expand=True)
        
        # Initialize X11 display
        if XLIB_AVAILABLE:
            self.display = display.Display()
            
    def launch_libreoffice(self):
        """Launch LibreOffice in a separate window"""
        if self.lo_process:
            self.status_label.config(text="LibreOffice already running", fg="orange")
            return
            
        # Create test document
        test_file = Path(__file__).parent / "test_xlib.odt"
        test_file.write_text("X11 Embedding Test")
        
        # Launch LibreOffice
        cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
        
        try:
            self.lo_process = subprocess.Popen(cmd)
            self.status_label.config(text=f"LibreOffice launched (PID: {self.lo_process.pid})", fg="green")
            
            # Give it time to create window
            self.root.after(3000, self.find_libreoffice_window)
            
        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg="red")
            
    def find_libreoffice_window(self):
        """Find LibreOffice window ID"""
        try:
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'LibreOffice'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                self.lo_window_id = int(window_ids[0])
                self.status_label.config(text=f"Found LibreOffice window: {self.lo_window_id}", fg="green")
            else:
                self.status_label.config(text="LibreOffice window not found", fg="red")
                
        except Exception as e:
            self.status_label.config(text=f"Error finding window: {e}", fg="red")
            
    def embed_window(self):
        """Attempt to embed LibreOffice window"""
        if not XLIB_AVAILABLE:
            self.status_label.config(text="python-xlib not available!", fg="red")
            return
            
        if not hasattr(self, 'lo_window_id'):
            self.status_label.config(text="LibreOffice window not found. Launch it first!", fg="red")
            return
            
        try:
            # Get container window ID
            container_id = self.container_frame.winfo_id()
            self.status_label.config(text=f"Embedding {self.lo_window_id} into {container_id}...", fg="blue")
            
            # Get windows
            container_win = self.display.create_resource_object('window', container_id)
            lo_win = self.display.create_resource_object('window', self.lo_window_id)
            
            # Store original parent for cleanup
            self.original_parent = lo_win.query_tree().parent
            
            # Remove window decorations
            lo_win.change_attributes(override_redirect=True)
            
            # Reparent LibreOffice window
            lo_win.reparent(container_win, 0, 0)
            
            # Resize to fit container
            width = self.container_frame.winfo_width()
            height = self.container_frame.winfo_height()
            lo_win.configure(width=width, height=height)
            
            # Map the window
            lo_win.map()
            
            # Flush changes
            self.display.sync()
            
            self.status_label.config(text="Window embedded successfully!", fg="green")
            
            # Set up resize handler
            self.container_frame.bind("<Configure>", self.on_container_resize)
            
        except Exception as e:
            self.status_label.config(text=f"Embedding failed: {e}", fg="red")
            import traceback
            traceback.print_exc()
            
    def on_container_resize(self, event):
        """Handle container resize"""
        if hasattr(self, 'lo_window_id') and XLIB_AVAILABLE:
            try:
                lo_win = self.display.create_resource_object('window', self.lo_window_id)
                lo_win.configure(width=event.width, height=event.height)
                self.display.sync()
            except:
                pass
                
    def test_overlay(self):
        """Test overlay positioning (fallback method)"""
        if not hasattr(self, 'lo_window_id'):
            self.status_label.config(text="LibreOffice not running!", fg="red")
            return
            
        try:
            # Get container position on screen
            x = self.container_frame.winfo_rootx()
            y = self.container_frame.winfo_rooty()
            width = self.container_frame.winfo_width()
            height = self.container_frame.winfo_height()
            
            # Position LibreOffice window over container
            subprocess.run(['xdotool', 'windowmove', str(self.lo_window_id), str(x), str(y)])
            subprocess.run(['xdotool', 'windowsize', str(self.lo_window_id), str(width), str(height)])
            
            # Remove decorations
            subprocess.run(['xdotool', 'key', '--window', str(self.lo_window_id), 'F11'])  # Try fullscreen
            
            self.status_label.config(text=f"Positioned at {x},{y} size {width}x{height}", fg="green")
            
        except Exception as e:
            self.status_label.config(text=f"Overlay failed: {e}", fg="red")
            
    def cleanup(self):
        """Cleanup on exit"""
        if self.lo_process:
            print("Terminating LibreOffice...")
            self.lo_process.terminate()
            
        if XLIB_AVAILABLE and self.display:
            self.display.close()
            
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
        
    def on_close(self):
        """Handle window close"""
        self.cleanup()
        self.root.destroy()


if __name__ == '__main__':
    print("X11 Window Embedding Test")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print(f"python-xlib: {'Available' if XLIB_AVAILABLE else 'Not installed'}")
    print("-" * 50)
    
    app = XlibEmbeddingTest()
    app.create_window()
    app.run()