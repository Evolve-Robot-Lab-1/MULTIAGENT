#!/usr/bin/env python3
"""
Test 03: GTK Socket with VCL plugins
Uses GTK Socket/Plug mechanism with different SAL_USE_VCLPLUGIN values
"""

import os
import time
import subprocess
from pathlib import Path

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, Gdk, GLib
    GTK_AVAILABLE = True
except ImportError:
    GTK_AVAILABLE = False

class EmbeddingTest:
    def __init__(self, config, test_dir, logger):
        self.config = config
        self.test_dir = test_dir
        self.logger = logger
        self.window = None
        self.socket = None
        self.socket_id = None
        self.lo_process = None
        self.plug_added = False
        
    def create_container_window(self):
        """Create a GTK window with socket"""
        if not GTK_AVAILABLE:
            self.logger.error("GTK not available")
            return False
        
        self.logger.info("Creating GTK Socket window...")
        
        try:
            # Create main window
            self.window = Gtk.Window(title="LibreOffice Container - Test 03")
            self.window.set_default_size(
                self.config['container_size']['width'],
                self.config['container_size']['height']
            )
            
            # Create a box to hold the socket
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.window.add(box)
            
            # Add a label
            label = Gtk.Label(label="LibreOffice should embed here via GTK Socket")
            box.pack_start(label, False, False, 5)
            
            # Create socket
            self.socket = Gtk.Socket()
            self.socket.set_size_request(
                self.config['container_size']['width'] - 10,
                self.config['container_size']['height'] - 40
            )
            box.pack_start(self.socket, True, True, 0)
            
            # Connect signals
            self.socket.connect("plug-added", self.on_plug_added)
            self.socket.connect("plug-removed", self.on_plug_removed)
            self.window.connect("destroy", self.on_window_destroy)
            
            # Show all widgets
            self.window.show_all()
            
            # Get socket ID
            self.socket_id = self.socket.get_id()
            self.logger.info(f"GTK Socket created with ID: 0x{self.socket_id:x}")
            
            # Process events to ensure window is displayed
            while Gtk.events_pending():
                Gtk.main_iteration()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create GTK socket window: {e}")
            return False
    
    def on_plug_added(self, socket):
        """Called when a plug is added to the socket"""
        self.logger.info("✓ Plug added to socket!")
        self.plug_added = True
    
    def on_plug_removed(self, socket):
        """Called when a plug is removed from the socket"""
        self.logger.info("Plug removed from socket")
        self.plug_added = False
    
    def on_window_destroy(self, widget):
        """Called when window is destroyed"""
        if self.lo_process:
            self.lo_process.terminate()
    
    def launch_libreoffice(self, vcl_plugin):
        """Launch LibreOffice with specified VCL plugin"""
        self.logger.info(f"Launching LibreOffice with VCL plugin: {vcl_plugin}")
        
        test_file = Path(__file__).parent / self.config['test_document']
        
        env = os.environ.copy()
        env['SAL_USE_VCLPLUGIN'] = vcl_plugin
        
        # Force GTK backend for X11
        if vcl_plugin.startswith('gtk'):
            env['GDK_BACKEND'] = 'x11'
        
        # Try different approaches
        approaches = [
            # Approach 1: Direct socket ID as parent
            [
                'soffice',
                f'--parent={self.socket_id}',
                '--nologo',
                '--norestore',
                '--view',
                str(test_file)
            ],
            # Approach 2: Socket ID as display
            [
                'soffice',
                f'--display=:{self.socket_id}',
                '--nologo',
                '--norestore',
                '--view',
                str(test_file)
            ],
            # Approach 3: Standard launch (for reparenting)
            [
                'soffice',
                '--nologo',
                '--norestore',
                '--nodefault',
                '--view',
                str(test_file)
            ]
        ]
        
        for i, cmd in enumerate(approaches):
            self.logger.info(f"Trying approach {i+1}: {' '.join(cmd[:2])}")
            
            try:
                self.lo_process = subprocess.Popen(cmd, env=env)
                self.logger.info(f"LibreOffice launched with PID: {self.lo_process.pid}")
                
                # Give it time to start
                time.sleep(3)
                
                # Check if plug was added
                if self.plug_added:
                    self.logger.info(f"✓ Success with approach {i+1}")
                    return True
                
                # If not embedded, try reparenting
                if i == len(approaches) - 1:  # Last approach
                    self.attempt_reparenting()
                
                # Check again
                if self.plug_added:
                    return True
                
                # Kill process for next attempt
                if self.lo_process:
                    self.lo_process.terminate()
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Failed with approach {i+1}: {e}")
                continue
        
        return self.plug_added
    
    def attempt_reparenting(self):
        """Attempt to reparent LibreOffice window into socket"""
        self.logger.info("Attempting to reparent LibreOffice window...")
        
        try:
            # Find LibreOffice window
            result = subprocess.run(
                ['xdotool', 'search', '--pid', str(self.lo_process.pid)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                
                for wid in window_ids:
                    # Try to add window to socket
                    try:
                        self.socket.add_id(int(wid))
                        self.logger.info(f"Added window {wid} to socket")
                        time.sleep(1)
                        
                        if self.plug_added:
                            return True
                    except Exception as e:
                        self.logger.debug(f"Failed to add window {wid}: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error during reparenting: {e}")
    
    def wait_and_verify(self, wait_time):
        """Wait and verify embedding"""
        self.logger.info(f"Waiting {wait_time}s for embedding...")
        
        # Process GTK events while waiting
        start_time = time.time()
        while time.time() - start_time < wait_time:
            while Gtk.events_pending():
                Gtk.main_iteration()
            time.sleep(0.1)
            
            if self.plug_added:
                self.logger.info("✓ Embedding successful!")
                return True
        
        return self.plug_added
    
    def cleanup(self):
        """Clean up resources"""
        if self.lo_process:
            self.lo_process.terminate()
            self.lo_process = None
        
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            
            # Process remaining events
            while Gtk.events_pending():
                Gtk.main_iteration()
    
    def run(self, vcl_plugin, wait_time):
        """Run the test with specified parameters"""
        if not GTK_AVAILABLE:
            return {'success': False, 'error': 'GTK not available'}
        
        self.logger.info(f"Running GTK Socket test (VCL: {vcl_plugin}, wait: {wait_time}s)")
        
        try:
            # Create container window with socket
            if not self.create_container_window():
                return {'success': False, 'error': 'Failed to create GTK socket window'}
            
            # Launch LibreOffice
            if not self.launch_libreoffice(vcl_plugin):
                return {'success': False, 'error': 'Failed to launch or embed LibreOffice'}
            
            # Wait and verify
            if not self.wait_and_verify(wait_time):
                return {'success': False, 'error': 'LibreOffice not embedded in socket'}
            
            # Keep window open for screenshot
            time.sleep(3)
            
            return {
                'success': True,
                'method': 'GTK Socket/Plug',
                'vcl_plugin': vcl_plugin,
                'socket_id': f"0x{self.socket_id:x}",
                'embedded': True
            }
            
        except Exception as e:
            self.logger.error(f"Test error: {e}")
            return {'success': False, 'error': str(e)}
            
        finally:
            self.cleanup()


if __name__ == '__main__':
    # For standalone testing
    import logging
    import json
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    with open('test_config.json', 'r') as f:
        config = json.load(f)
    
    test = EmbeddingTest(config, Path('.'), logger)
    result = test.run('gtk3', 5)
    print(f"Result: {result}")