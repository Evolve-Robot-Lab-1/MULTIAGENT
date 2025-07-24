#!/usr/bin/env python3
"""
Precise X11 Window Embedding Test
This version carefully identifies and embeds the correct window
"""

import os
import sys
import time
import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from pathlib import Path

try:
    from Xlib import X, display
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False

class PreciseEmbeddingTest:
    def __init__(self):
        self.window = None
        self.socket = None
        self.lo_process = None
        self.lo_window_id = None
        self.embedded_windows = []
        
    def create_window(self):
        """Create GTK window with embedding area"""
        self.window = Gtk.Window(title="Precise LibreOffice Embedding Test")
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
        header.set_markup("<b>Precise X11 LibreOffice Embedding Test</b>")
        vbox.pack_start(header, False, False, 0)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox.pack_start(button_box, False, False, 0)
        
        btn_launch = Gtk.Button(label="1. Launch LibreOffice")
        btn_launch.connect("clicked", self.launch_libreoffice)
        button_box.pack_start(btn_launch, False, False, 0)
        
        btn_find = Gtk.Button(label="2. Find LibreOffice Window")
        btn_find.connect("clicked", self.find_libreoffice_window)
        button_box.pack_start(btn_find, False, False, 0)
        
        btn_embed = Gtk.Button(label="3. Embed Window")
        btn_embed.connect("clicked", self.embed_libreoffice)
        button_box.pack_start(btn_embed, False, False, 0)
        
        btn_restore = Gtk.Button(label="Restore Windows")
        btn_restore.connect("clicked", self.restore_windows)
        button_box.pack_start(btn_restore, False, False, 0)
        
        # Status
        self.status_label = Gtk.Label("Ready to start...")
        vbox.pack_start(self.status_label, False, False, 0)
        
        # Window info text
        self.info_text = Gtk.TextView()
        self.info_text.set_editable(False)
        info_scroll = Gtk.ScrolledWindow()
        info_scroll.set_size_request(1150, 150)
        info_scroll.add(self.info_text)
        vbox.pack_start(info_scroll, False, False, 0)
        
        # Embedding area
        embed_frame = Gtk.Frame(label="LibreOffice Embedding Target")
        self.socket = Gtk.Socket()
        self.socket.set_size_request(1150, 500)
        self.socket.connect("plug-added", self.on_plug_added)
        self.socket.connect("plug-removed", self.on_plug_removed)
        embed_frame.add(self.socket)
        vbox.pack_start(embed_frame, True, True, 0)
        
        self.window.show_all()
        
        # Get socket ID after realization
        GLib.idle_add(self.get_socket_info)
        
    def get_socket_info(self):
        """Get socket information"""
        if self.socket.get_window():
            socket_id = self.socket.get_id()
            self.log_info(f"Socket created with ID: {socket_id}")
            self.log_info(f"Socket window XID: {self.socket.get_window().get_xid()}")
        return False
        
    def log_info(self, text):
        """Log information to the text view"""
        buffer = self.info_text.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, f"{text}\n")
        
        # Auto-scroll
        mark = buffer.get_insert()
        self.info_text.scroll_mark_onscreen(mark)
        
        # Also print to console
        print(f"[LOG] {text}")
        
    def launch_libreoffice(self, button):
        """Launch LibreOffice and track its PID"""
        if self.lo_process:
            self.status_label.set_text("LibreOffice already running!")
            return
            
        # Create test document
        test_file = Path(__file__).parent / "test_precise.odt"
        test_file.write_text("Precise Embedding Test Document")
        
        # Launch LibreOffice
        cmd = ['soffice', '--nologo', '--norestore', '--view', str(test_file)]
        
        try:
            self.lo_process = subprocess.Popen(cmd)
            self.log_info(f"Launched LibreOffice with PID: {self.lo_process.pid}")
            self.status_label.set_text(f"LibreOffice launched (PID: {self.lo_process.pid})")
            
            # Wait a bit for window creation
            GLib.timeout_add(3000, self.auto_find_window)
            
        except Exception as e:
            self.log_info(f"ERROR: Failed to launch LibreOffice: {e}")
            self.status_label.set_text(f"Error: {e}")
            
    def auto_find_window(self):
        """Automatically find window after launch"""
        self.find_libreoffice_window(None)
        return False  # Don't repeat
        
    def find_libreoffice_window(self, button):
        """Find LibreOffice window by PID"""
        if not self.lo_process:
            self.status_label.set_text("Launch LibreOffice first!")
            return
            
        self.log_info("\nSearching for LibreOffice window...")
        
        try:
            # Method 1: Search by PID
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(self.lo_process.pid)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                self.log_info(f"Found {len(window_ids)} windows for PID {self.lo_process.pid}")
                
                # Find the main window (usually the largest)
                for wid in window_ids:
                    # Get window info
                    info_result = subprocess.run(
                        ['xwininfo', '-id', wid],
                        capture_output=True,
                        text=True
                    )
                    
                    if 'LibreOffice' in info_result.stdout:
                        self.lo_window_id = int(wid)
                        self.log_info(f"Found LibreOffice main window: {wid}")
                        
                        # Get window details
                        for line in info_result.stdout.split('\n')[:10]:
                            if line.strip():
                                self.log_info(f"  {line.strip()}")
                                
                        self.status_label.set_text(f"Found LibreOffice window: {wid}")
                        return
                        
            # Method 2: Search by class
            result = subprocess.run(
                ['xdotool', 'search', '--class', 'libreoffice'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                self.lo_window_id = int(window_ids[0])
                self.log_info(f"Found LibreOffice by class: {self.lo_window_id}")
                self.status_label.set_text(f"Found window: {self.lo_window_id}")
            else:
                self.log_info("No LibreOffice window found!")
                self.status_label.set_text("Window not found!")
                
        except Exception as e:
            self.log_info(f"ERROR: {e}")
            self.status_label.set_text(f"Error: {e}")
            
    def embed_libreoffice(self, button):
        """Embed the found LibreOffice window"""
        if not self.lo_window_id:
            self.status_label.set_text("Find LibreOffice window first!")
            return
            
        if not XLIB_AVAILABLE:
            self.status_label.set_text("python-xlib not available!")
            return
            
        self.log_info(f"\nAttempting to embed window {self.lo_window_id}...")
        
        try:
            # Get socket ID
            socket_id = self.socket.get_id()
            
            # Open X display
            d = display.Display()
            
            # Get windows
            socket_win = d.create_resource_object('window', socket_id)
            lo_win = d.create_resource_object('window', self.lo_window_id)
            
            # Store original parent
            original_parent = lo_win.query_tree().parent
            self.embedded_windows.append((self.lo_window_id, original_parent.id))
            
            self.log_info(f"Original parent window: {original_parent.id}")
            
            # Get current window geometry
            geom = lo_win.get_geometry()
            self.log_info(f"Original geometry: {geom.width}x{geom.height}")
            
            # Unmap window first
            lo_win.unmap()
            d.sync()
            
            # Remove window manager decorations
            lo_win.change_attributes(override_redirect=True)
            
            # Reparent to our socket
            lo_win.reparent(socket_win, 0, 0)
            
            # Resize to fit socket
            width = self.socket.get_allocated_width()
            height = self.socket.get_allocated_height()
            lo_win.configure(width=width-2, height=height-2)
            
            # Map the window again
            lo_win.map()
            
            # Ensure it's visible
            lo_win.raise_window()
            
            # Sync all changes
            d.sync()
            d.close()
            
            self.log_info(f"Successfully embedded window {self.lo_window_id}")
            self.status_label.set_text("LibreOffice embedded successfully!")
            
            # Set up resize handler
            self.socket.connect("size-allocate", self.on_socket_resize)
            
        except Exception as e:
            self.log_info(f"ERROR during embedding: {e}")
            self.status_label.set_text(f"Embedding failed: {e}")
            import traceback
            traceback.print_exc()
            
    def on_socket_resize(self, widget, allocation):
        """Handle socket resize"""
        if self.lo_window_id and XLIB_AVAILABLE:
            try:
                d = display.Display()
                lo_win = d.create_resource_object('window', self.lo_window_id)
                lo_win.configure(width=allocation.width-2, height=allocation.height-2)
                d.sync()
                d.close()
            except:
                pass
                
    def restore_windows(self, button):
        """Restore embedded windows to original state"""
        if not self.embedded_windows:
            self.status_label.set_text("No embedded windows to restore")
            return
            
        self.log_info("\nRestoring windows...")
        
        try:
            d = display.Display()
            
            for window_id, original_parent_id in self.embedded_windows:
                try:
                    win = d.create_resource_object('window', window_id)
                    parent = d.create_resource_object('window', original_parent_id)
                    
                    # Unmap first
                    win.unmap()
                    d.sync()
                    
                    # Restore normal attributes
                    win.change_attributes(override_redirect=False)
                    
                    # Reparent back
                    win.reparent(parent, 0, 0)
                    
                    # Map again
                    win.map()
                    d.sync()
                    
                    self.log_info(f"Restored window {window_id}")
                    
                except Exception as e:
                    self.log_info(f"Failed to restore {window_id}: {e}")
                    
            d.close()
            self.embedded_windows.clear()
            self.status_label.set_text("Windows restored")
            
        except Exception as e:
            self.log_info(f"ERROR during restore: {e}")
            
    def on_plug_added(self, socket):
        """Called when plug is added"""
        self.log_info("GTK: Plug added to socket!")
        
    def on_plug_removed(self, socket):
        """Called when plug is removed"""
        self.log_info("GTK: Plug removed from socket!")
        
    def cleanup_and_quit(self, widget):
        """Clean up and quit"""
        if self.lo_process:
            self.log_info("Terminating LibreOffice...")
            self.lo_process.terminate()
            
        Gtk.main_quit()
        
    def run(self):
        """Run the application"""
        Gtk.main()


if __name__ == '__main__':
    print("Precise X11 LibreOffice Embedding Test")
    print(f"python-xlib: {'Available' if XLIB_AVAILABLE else 'Not installed'}")
    print("-" * 50)
    
    app = PreciseEmbeddingTest()
    app.create_window()
    app.run()