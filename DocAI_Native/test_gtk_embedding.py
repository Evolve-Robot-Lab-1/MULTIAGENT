#!/usr/bin/env python3
"""
Test GTK Socket/Plug Embedding for LibreOffice
This tests if we can embed LibreOffice using GTK3 Socket/Plug mechanism
"""

import os
import sys
import time
import subprocess
import threading
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, GLib, WebKit2
from pathlib import Path

class GTKEmbeddingTest:
    def __init__(self):
        self.window = None
        self.socket = None
        self.lo_process = None
        self.socket_id = None
        
    def create_test_document(self):
        """Create a test document"""
        test_file = Path(__file__).parent / "test_gtk_embedding.odt"
        if not test_file.exists():
            test_file.write_text("GTK Embedding Test Document")
        return str(test_file)
        
    def create_window(self):
        """Create GTK window with WebView and Socket"""
        # Main window
        self.window = Gtk.Window(title="GTK LibreOffice Embedding Test")
        self.window.set_default_size(1200, 800)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        self.window.add(vbox)
        
        # Header
        header = Gtk.Label()
        header.set_markup("<b>GTK Socket/Plug LibreOffice Embedding Test</b>")
        vbox.pack_start(header, False, False, 0)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox.pack_start(button_box, False, False, 0)
        
        btn_info = Gtk.Button(label="Get Socket Info")
        btn_info.connect("clicked", self.on_get_info)
        button_box.pack_start(btn_info, False, False, 0)
        
        btn_embed = Gtk.Button(label="Embed LibreOffice")
        btn_embed.connect("clicked", self.on_embed_libreoffice)
        button_box.pack_start(btn_embed, False, False, 0)
        
        btn_test = Gtk.Button(label="Test X11 Embedding")
        btn_test.connect("clicked", self.on_test_x11)
        button_box.pack_start(btn_test, False, False, 0)
        
        # Info label
        self.info_label = Gtk.Label("Ready for testing...")
        vbox.pack_start(self.info_label, False, False, 0)
        
        # Main container with WebView and Socket
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(paned, True, True, 0)
        
        # Left side - WebView
        webview_frame = Gtk.Frame(label="WebView Side")
        self.webview = WebKit2.WebView()
        self.webview.load_html("""
            <html>
            <body style="font-family: Arial; padding: 20px;">
                <h2>WebView Content</h2>
                <p>This represents the DocAI interface.</p>
                <div style="border: 2px dashed #ccc; padding: 20px; margin: 20px 0;">
                    <p>LibreOffice would normally be embedded in a container like this.</p>
                </div>
            </body>
            </html>
        """)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.webview)
        webview_frame.add(scrolled)
        paned.pack1(webview_frame, True, False)
        
        # Right side - Socket for embedding
        socket_frame = Gtk.Frame(label="LibreOffice Embedding Area")
        
        # Create GTK Socket
        self.socket = Gtk.Socket()
        self.socket.set_size_request(600, 500)
        
        # Connect to plug-added signal
        self.socket.connect("plug-added", self.on_plug_added)
        self.socket.connect("plug-removed", self.on_plug_removed)
        
        socket_frame.add(self.socket)
        paned.pack2(socket_frame, True, False)
        
        # Set paned position
        paned.set_position(500)
        
        # Show all
        self.window.show_all()
        
        # Get socket ID after window is realized
        GLib.idle_add(self.get_socket_id)
        
    def get_socket_id(self):
        """Get the socket ID for embedding"""
        if self.socket.get_window():
            self.socket_id = self.socket.get_id()
            self.info_label.set_text(f"Socket ID: {self.socket_id}")
            print(f"[GTK] Socket ID: {self.socket_id}")
        return False
        
    def on_get_info(self, button):
        """Get socket information"""
        info = f"Socket ID: {self.socket_id}\n"
        info += f"Window ID: {self.window.get_window().get_xid() if self.window.get_window() else 'Not available'}\n"
        info += f"Display: {os.environ.get('DISPLAY', 'Not set')}"
        
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Socket Information",
        )
        dialog.format_secondary_text(info)
        dialog.run()
        dialog.destroy()
        
    def on_embed_libreoffice(self, button):
        """Try to embed LibreOffice"""
        if not self.socket_id:
            self.info_label.set_text("Socket not ready!")
            return
            
        self.info_label.set_text("Attempting to embed LibreOffice...")
        
        # Create test document
        test_file = self.create_test_document()
        
        # Try different embedding methods
        self.try_gtk_plug_embedding(test_file)
        
    def try_gtk_plug_embedding(self, document_path):
        """Try GTK plug embedding"""
        print("\n[TEST] Trying GTK Plug embedding...")
        
        # LibreOffice doesn't directly support GTK plug, but we can try some approaches
        
        # Method 1: Try with XEMBED hint
        env = os.environ.copy()
        env['XEMBED'] = str(self.socket_id)
        
        cmd = [
            'soffice',
            '--nologo',
            '--norestore',
            '--view',
            document_path
        ]
        
        try:
            self.lo_process = subprocess.Popen(cmd, env=env)
            print(f"[INFO] LibreOffice launched with XEMBED={self.socket_id}")
            
            # Give it time to start
            time.sleep(3)
            
            # Try to find and reparent the window
            self.try_manual_embedding()
            
        except Exception as e:
            print(f"[ERROR] Failed to launch LibreOffice: {e}")
            self.info_label.set_text(f"Error: {e}")
            
    def try_manual_embedding(self):
        """Try manual X11 embedding after LibreOffice starts"""
        print("\n[TEST] Trying manual X11 embedding...")
        
        try:
            # Find LibreOffice window
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'LibreOffice'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lo_window_id = result.stdout.strip().split('\n')[0]
                print(f"[INFO] Found LibreOffice window: {lo_window_id}")
                
                # Try xembed approach
                self.embed_with_xlib(int(lo_window_id))
                
        except Exception as e:
            print(f"[ERROR] Manual embedding failed: {e}")
            
    def embed_with_xlib(self, lo_window_id):
        """Use python-xlib to embed window"""
        try:
            from Xlib import X, display
            from Xlib.xobject import drawable
            
            d = display.Display()
            
            # Get our socket window
            socket_xid = self.socket_id
            socket_win = d.create_resource_object('window', socket_xid)
            
            # Get LibreOffice window
            lo_win = d.create_resource_object('window', lo_window_id)
            
            # Reparent LibreOffice window to our socket
            lo_win.reparent(socket_win, 0, 0)
            
            # Remove decorations
            lo_win.change_attributes(override_redirect=True)
            
            # Map the window
            lo_win.map()
            
            d.sync()
            
            print("[SUCCESS] Window reparented using python-xlib")
            self.info_label.set_text("LibreOffice embedded successfully!")
            
        except ImportError:
            print("[WARNING] python-xlib not available")
            print("Install with: pip install python-xlib")
            self.try_xdotool_embedding(lo_window_id)
            
        except Exception as e:
            print(f"[ERROR] Xlib embedding failed: {e}")
            
    def try_xdotool_embedding(self, lo_window_id):
        """Fallback to xdotool for embedding"""
        print("\n[TEST] Trying xdotool embedding...")
        
        try:
            # Get socket window geometry
            socket_win = self.socket.get_window()
            if socket_win:
                x, y = socket_win.get_position()
                width = self.socket.get_allocated_width()
                height = self.socket.get_allocated_height()
                
                # Position LibreOffice window over socket
                subprocess.run(['xdotool', 'windowmove', str(lo_window_id), str(x), str(y)])
                subprocess.run(['xdotool', 'windowsize', str(lo_window_id), str(width), str(height)])
                
                print(f"[INFO] Positioned LibreOffice at {x},{y} size {width}x{height}")
                self.info_label.set_text("LibreOffice positioned (not truly embedded)")
                
        except Exception as e:
            print(f"[ERROR] xdotool positioning failed: {e}")
            
    def on_test_x11(self, button):
        """Test X11 embedding approaches"""
        dialog = Gtk.Dialog(
            title="X11 Embedding Test",
            transient_for=self.window,
            flags=0
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content = dialog.get_content_area()
        
        label = Gtk.Label("This will test various X11 embedding methods.\nCheck terminal for results.")
        content.add(label)
        
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            self.run_x11_tests()
            
    def run_x11_tests(self):
        """Run comprehensive X11 tests"""
        print("\n" + "="*50)
        print("X11 EMBEDDING TESTS")
        print("="*50)
        
        # Test 1: Check window manager
        result = subprocess.run(['wmctrl', '-m'], capture_output=True, text=True)
        print(f"\n[Window Manager]\n{result.stdout}")
        
        # Test 2: List all windows
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
        print(f"\n[Current Windows]\n{result.stdout[:500]}...")
        
        # Test 3: Check X11 properties
        if self.socket_id:
            result = subprocess.run(
                ['xprop', '-id', str(self.socket_id)],
                capture_output=True, text=True
            )
            print(f"\n[Socket X11 Properties]\n{result.stdout[:500]}...")
            
    def on_plug_added(self, socket):
        """Called when a plug is successfully added"""
        print("[GTK] Plug added to socket!")
        self.info_label.set_text("Plug successfully added!")
        
    def on_plug_removed(self, socket):
        """Called when a plug is removed"""
        print("[GTK] Plug removed from socket!")
        self.info_label.set_text("Plug removed")
        
        if self.lo_process:
            self.lo_process.terminate()
            self.lo_process = None
            
    def run(self):
        """Run the GTK application"""
        Gtk.main()
        
    def cleanup(self):
        """Cleanup on exit"""
        if self.lo_process:
            print("\n[CLEANUP] Terminating LibreOffice...")
            self.lo_process.terminate()


if __name__ == '__main__':
    print("GTK Socket/Plug LibreOffice Embedding Test")
    print(f"Platform: {sys.platform}")
    print(f"GTK Version: {Gtk.get_major_version()}.{Gtk.get_minor_version()}")
    
    # Check for python-xlib
    try:
        import Xlib
        print("python-xlib: Available")
    except ImportError:
        print("python-xlib: Not installed (install with: pip install python-xlib)")
        
    app = GTKEmbeddingTest()
    app.create_window()
    
    try:
        app.run()
    finally:
        app.cleanup()