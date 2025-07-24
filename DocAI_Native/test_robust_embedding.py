#!/usr/bin/env python3
"""
Robust X11 Window Embedding Test with proper window locking
"""

import os
import sys
import time
import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
from pathlib import Path

try:
    from Xlib import X, display
    from Xlib.ext import shape
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False
    print("WARNING: python-xlib required!")

class RobustEmbeddingTest:
    def __init__(self):
        self.window = None
        self.embed_container = None
        self.lo_process = None
        self.lo_window_id = None
        self.container_xid = None
        self.is_embedded = False
        
    def create_window(self):
        """Create GTK window with proper embedding container"""
        self.window = Gtk.Window(title="Robust LibreOffice Embedding Test")
        self.window.set_default_size(1200, 800)
        self.window.connect("destroy", self.cleanup_and_quit)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        self.window.add(vbox)
        
        # Header
        header = Gtk.Label()
        header.set_markup("<b>Robust X11 LibreOffice Embedding (Window Locking)</b>")
        vbox.pack_start(header, False, False, 0)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox.pack_start(button_box, False, False, 0)
        
        btn_embed = Gtk.Button(label="Embed LibreOffice (Auto)")
        btn_embed.connect("clicked", self.auto_embed_libreoffice)
        button_box.pack_start(btn_embed, False, False, 0)
        
        btn_release = Gtk.Button(label="Release Window")
        btn_release.connect("clicked", self.release_window)
        button_box.pack_start(btn_release, False, False, 0)
        
        btn_test = Gtk.Button(label="Test Focus Lock")
        btn_test.connect("clicked", self.test_focus_lock)
        button_box.pack_start(btn_test, False, False, 0)
        
        # Status
        self.status_label = Gtk.Label("Ready to embed LibreOffice...")
        vbox.pack_start(self.status_label, False, False, 0)
        
        # Create embedding container using DrawingArea (more control than Socket)
        embed_frame = Gtk.Frame(label="LibreOffice Container (Locked)")
        self.embed_container = Gtk.DrawingArea()
        self.embed_container.set_size_request(1150, 600)
        self.embed_container.set_can_focus(True)
        
        # Set visual properties for embedding
        self.embed_container.connect("realize", self.on_container_realized)
        self.embed_container.connect("size-allocate", self.on_container_resized)
        self.embed_container.connect("draw", self.on_container_draw)
        
        # Add container to frame
        embed_frame.add(self.embed_container)
        vbox.pack_start(embed_frame, True, True, 0)
        
        self.window.show_all()
        
    def on_container_realized(self, widget):
        """Container is realized and has a window"""
        self.container_xid = widget.get_window().get_xid()
        self.log(f"Container realized with XID: {self.container_xid}")
        
    def on_container_resized(self, widget, allocation):
        """Handle container resize"""
        if self.is_embedded and self.lo_window_id:
            self.resize_embedded_window(allocation.width, allocation.height)
            
    def on_container_draw(self, widget, cr):
        """Draw container background"""
        if not self.is_embedded:
            # Draw placeholder
            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.paint()
            
            # Draw text
            cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.select_font_face("Arial", 0, 0)
            cr.set_font_size(20)
            cr.move_to(400, 300)
            cr.show_text("LibreOffice will be embedded here")
            
    def log(self, message):
        """Log message to console and status"""
        print(f"[LOG] {message}")
        self.status_label.set_text(message)
        
    def auto_embed_libreoffice(self, button):
        """Automatically launch and embed LibreOffice"""
        if not XLIB_AVAILABLE:
            self.log("ERROR: python-xlib not installed!")
            return
            
        if not self.container_xid:
            self.log("ERROR: Container not realized yet!")
            return
            
        self.log("Starting automatic embedding process...")
        
        # Step 1: Launch LibreOffice
        if not self.launch_libreoffice():
            return
            
        # Step 2: Wait and find window (with timeout)
        GLib.timeout_add(100, self.find_and_embed_loop, 0)
        
    def launch_libreoffice(self):
        """Launch LibreOffice process"""
        if self.lo_process:
            self.log("LibreOffice already running!")
            return False
            
        # Create test document
        test_file = Path(__file__).parent / "test_robust.odt"
        test_file.write_text("Robust Embedding Test")
        
        # Launch with specific window title
        cmd = [
            'soffice',
            '--nologo',
            '--norestore',
            '--nodefault',  # Don't show start center
            '--view',
            str(test_file)
        ]
        
        try:
            self.lo_process = subprocess.Popen(cmd)
            self.log(f"Launched LibreOffice (PID: {self.lo_process.pid})")
            return True
        except Exception as e:
            self.log(f"ERROR: Failed to launch: {e}")
            return False
            
    def find_and_embed_loop(self, attempt):
        """Loop to find and embed window"""
        if attempt > 50:  # 5 seconds timeout
            self.log("ERROR: Timeout finding LibreOffice window")
            return False
            
        # Try to find window
        window_id = self.find_libreoffice_window()
        
        if window_id:
            self.lo_window_id = window_id
            self.embed_window()
            return False  # Stop loop
        else:
            # Continue searching
            return True
            
    def find_libreoffice_window(self):
        """Find LibreOffice window by PID and class"""
        try:
            # Search by PID
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(self.lo_process.pid), '--class', 'libreoffice'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                # Return the last one (usually the document window)
                return int(window_ids[-1])
                
        except Exception as e:
            pass
            
        return None
        
    def embed_window(self):
        """Embed LibreOffice window with proper locking"""
        if not self.lo_window_id or not self.container_xid:
            self.log("ERROR: Missing window IDs")
            return
            
        self.log(f"Embedding window {self.lo_window_id} into container {self.container_xid}")
        
        try:
            # Open X display
            d = display.Display()
            
            # Get windows
            container = d.create_resource_object('window', self.container_xid)
            lo_window = d.create_resource_object('window', self.lo_window_id)
            
            # Save original state
            self.original_parent = lo_window.query_tree().parent
            
            # Step 1: Unmap the LibreOffice window
            lo_window.unmap()
            d.sync()
            
            # Step 2: Remove window manager hints
            # This prevents the window manager from managing it
            lo_window.change_attributes(
                override_redirect=True,
                event_mask=X.ExposureMask | X.StructureNotifyMask
            )
            
            # Step 3: Reparent to our container
            lo_window.reparent(container, 0, 0)
            
            # Step 4: Set size to match container
            width = self.embed_container.get_allocated_width()
            height = self.embed_container.get_allocated_height()
            lo_window.configure(
                x=0,
                y=0,
                width=width,
                height=height,
                border_width=0
            )
            
            # Step 5: Set input focus handling
            lo_window.set_input_focus(X.RevertToParent, X.CurrentTime)
            
            # Step 6: Map the window in its new location
            lo_window.map()
            
            # Step 7: Raise to top
            lo_window.raise_window()
            
            # Step 8: Force container to repaint
            d.sync()
            
            # Step 9: Keep the embedded window on top of container
            self.setup_window_lock(d, lo_window, container)
            
            d.close()
            
            self.is_embedded = True
            self.log("LibreOffice embedded and locked successfully!")
            
            # Force container redraw
            self.embed_container.queue_draw()
            
            # Set up continuous position monitoring
            GLib.timeout_add(100, self.monitor_embedded_window)
            
        except Exception as e:
            self.log(f"ERROR during embedding: {e}")
            import traceback
            traceback.print_exc()
            
    def setup_window_lock(self, display, embedded_window, container):
        """Set up additional constraints to lock the window"""
        try:
            # Set window type hints
            embedded_window.change_property(
                display.intern_atom('_NET_WM_WINDOW_TYPE'),
                display.intern_atom('ATOM'),
                32,
                [display.intern_atom('_NET_WM_WINDOW_TYPE_NORMAL')]
            )
            
            # Set state to skip taskbar and pager
            embedded_window.change_property(
                display.intern_atom('_NET_WM_STATE'),
                display.intern_atom('ATOM'),
                32,
                [
                    display.intern_atom('_NET_WM_STATE_SKIP_TASKBAR'),
                    display.intern_atom('_NET_WM_STATE_SKIP_PAGER')
                ]
            )
            
            display.sync()
            
        except Exception as e:
            self.log(f"Warning: Could not set window properties: {e}")
            
    def monitor_embedded_window(self):
        """Monitor and maintain embedded window position"""
        if not self.is_embedded:
            return False  # Stop monitoring
            
        try:
            # Ensure window stays at 0,0 within container
            subprocess.run(
                ['xdotool', 'windowmove', '--sync', str(self.lo_window_id), '0', '0'],
                capture_output=True
            )
        except:
            pass
            
        return self.is_embedded  # Continue if still embedded
        
    def resize_embedded_window(self, width, height):
        """Resize embedded window"""
        if not self.lo_window_id:
            return
            
        try:
            d = display.Display()
            lo_window = d.create_resource_object('window', self.lo_window_id)
            lo_window.configure(width=width, height=height)
            d.sync()
            d.close()
        except Exception as e:
            self.log(f"Resize error: {e}")
            
    def test_focus_lock(self, button):
        """Test that focus stays within embedded window"""
        if self.is_embedded:
            self.embed_container.grab_focus()
            self.log("Focus grabbed by container")
        else:
            self.log("No embedded window to test")
            
    def release_window(self, button):
        """Release embedded window"""
        if not self.is_embedded or not self.lo_window_id:
            self.log("No embedded window to release")
            return
            
        try:
            d = display.Display()
            lo_window = d.create_resource_object('window', self.lo_window_id)
            
            # Unmap
            lo_window.unmap()
            d.sync()
            
            # Restore attributes
            lo_window.change_attributes(override_redirect=False)
            
            # Reparent to root
            root = d.screen().root
            lo_window.reparent(root, 100, 100)
            
            # Map again
            lo_window.map()
            d.sync()
            d.close()
            
            self.is_embedded = False
            self.log("Window released")
            
            # Redraw container
            self.embed_container.queue_draw()
            
        except Exception as e:
            self.log(f"Release error: {e}")
            
    def cleanup_and_quit(self, widget):
        """Clean up and quit"""
        self.is_embedded = False
        
        if self.lo_process:
            self.log("Terminating LibreOffice...")
            self.lo_process.terminate()
            
        Gtk.main_quit()
        
    def run(self):
        """Run the application"""
        Gtk.main()


if __name__ == '__main__':
    print("Robust X11 LibreOffice Embedding Test")
    print("This version locks the window to the container")
    print("-" * 50)
    
    if not XLIB_AVAILABLE:
        print("ERROR: python-xlib is required!")
        print("Install with: pip install python-xlib")
        sys.exit(1)
        
    app = RobustEmbeddingTest()
    app.create_window()
    app.run()