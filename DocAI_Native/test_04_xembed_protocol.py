#!/usr/bin/env python3
"""
Test 04: XEmbed Protocol Implementation
Implements proper XEmbed protocol for embedding LibreOffice
"""

import os
import time
import subprocess
import struct
from pathlib import Path

try:
    from Xlib import X, display, Xatom
    from Xlib.protocol import event
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False

# XEmbed constants
XEMBED_EMBEDDED_NOTIFY = 0
XEMBED_WINDOW_ACTIVATE = 1
XEMBED_WINDOW_DEACTIVATE = 2
XEMBED_REQUEST_FOCUS = 3
XEMBED_FOCUS_IN = 4
XEMBED_FOCUS_OUT = 5
XEMBED_FOCUS_NEXT = 6
XEMBED_FOCUS_PREV = 7

XEMBED_MAPPED = (1 << 0)

class EmbeddingTest:
    def __init__(self, config, test_dir, logger):
        self.config = config
        self.test_dir = test_dir
        self.logger = logger
        self.display = None
        self.container_window = None
        self.lo_process = None
        self.lo_window = None
        self.xembed_atom = None
        self.xembed_info_atom = None
        
    def create_container_window(self):
        """Create a container window with XEmbed support"""
        if not XLIB_AVAILABLE:
            self.logger.error("python-xlib not available")
            return False
        
        self.logger.info("Creating XEmbed container window...")
        
        try:
            # Open X display
            self.display = display.Display()
            screen = self.display.screen()
            root = screen.root
            
            # Get atoms
            self.xembed_atom = self.display.intern_atom('_XEMBED')
            self.xembed_info_atom = self.display.intern_atom('_XEMBED_INFO')
            
            # Create window
            self.container_window = root.create_window(
                50, 50,  # x, y
                self.config['container_size']['width'],
                self.config['container_size']['height'],
                2,  # border width
                screen.root_depth,
                X.InputOutput,
                X.CopyFromParent,
                background_pixel=screen.white_pixel,
                event_mask=(X.ExposureMask | X.KeyPressMask | 
                           X.StructureNotifyMask | X.SubstructureNotifyMask |
                           X.SubstructureRedirectMask)
            )
            
            # Set window properties
            self.container_window.set_wm_name("XEmbed Container - Test 04")
            self.container_window.set_wm_class("xembed_container", "XEmbedContainer")
            
            # Set _XEMBED_INFO property to indicate we support XEmbed
            xembed_info = struct.pack('II', 0, XEMBED_MAPPED)  # version 0, mapped
            self.container_window.change_property(
                self.xembed_info_atom,
                self.xembed_info_atom,
                32,
                xembed_info
            )
            
            # Map (show) the window
            self.container_window.map()
            self.display.sync()
            
            self.logger.info(f"XEmbed container created with ID: 0x{self.container_window.id:x}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create XEmbed container: {e}")
            return False
    
    def launch_libreoffice(self, vcl_plugin):
        """Launch LibreOffice with specified VCL plugin"""
        self.logger.info(f"Launching LibreOffice with VCL plugin: {vcl_plugin}")
        
        test_file = Path(__file__).parent / self.config['test_document']
        
        env = os.environ.copy()
        env['SAL_USE_VCLPLUGIN'] = vcl_plugin
        
        # Set container window ID in environment (some apps check this)
        env['XEMBED_CONTAINER_ID'] = str(self.container_window.id)
        
        cmd = [
            'soffice',
            '--nologo',
            '--norestore',
            '--nodefault',
            '--view',
            str(test_file)
        ]
        
        try:
            self.lo_process = subprocess.Popen(cmd, env=env)
            self.logger.info(f"LibreOffice launched with PID: {self.lo_process.pid}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to launch LibreOffice: {e}")
            return False
    
    def find_libreoffice_window(self, wait_time):
        """Find LibreOffice window and check for XEmbed support"""
        if not self.display:
            return False
        
        self.logger.info(f"Waiting {wait_time}s for LibreOffice window...")
        time.sleep(wait_time)
        
        try:
            # Get root window
            root = self.display.screen().root
            
            # Query window tree
            tree = root.query_tree()
            
            for window in tree.children:
                try:
                    # Get window properties
                    wm_class = window.get_wm_class()
                    wm_name = window.get_wm_name()
                    
                    if wm_class and 'libreoffice' in str(wm_class).lower():
                        self.logger.info(f"Found window: {wm_name} (0x{window.id:x})")
                        
                        # Skip splash screens
                        if wm_name and ('test_embed' in wm_name or 
                                      ('LibreOffice' in wm_name and 'Start' not in wm_name)):
                            
                            # Check if window supports XEmbed
                            xembed_info = self.get_xembed_info(window)
                            if xembed_info:
                                self.logger.info(f"Window supports XEmbed: {xembed_info}")
                            else:
                                self.logger.info("Window doesn't have _XEMBED_INFO, adding it")
                                self.set_xembed_info(window)
                            
                            self.lo_window = window
                            self.logger.info(f"Selected LibreOffice window: 0x{window.id:x}")
                            return True
                            
                except Exception as e:
                    self.logger.debug(f"Error checking window: {e}")
                    continue
            
            self.logger.warning("No suitable LibreOffice window found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding LibreOffice window: {e}")
            return False
    
    def get_xembed_info(self, window):
        """Get _XEMBED_INFO property from window"""
        try:
            prop = window.get_full_property(self.xembed_info_atom, 0)
            if prop:
                # Unpack version and flags
                data = prop.value
                if len(data) >= 8:
                    version, flags = struct.unpack('II', data[:8])
                    return {'version': version, 'flags': flags}
        except:
            pass
        return None
    
    def set_xembed_info(self, window):
        """Set _XEMBED_INFO property on window"""
        try:
            xembed_info = struct.pack('II', 0, XEMBED_MAPPED)  # version 0, mapped
            window.change_property(
                self.xembed_info_atom,
                self.xembed_info_atom,
                32,
                xembed_info
            )
            self.display.sync()
        except Exception as e:
            self.logger.error(f"Failed to set _XEMBED_INFO: {e}")
    
    def embed_window(self):
        """Embed LibreOffice window using XEmbed protocol"""
        if not self.lo_window or not self.container_window:
            self.logger.error("Missing windows for embedding")
            return False
        
        try:
            self.logger.info(f"Embedding 0x{self.lo_window.id:x} using XEmbed protocol")
            
            # Step 1: Reparent the window
            self.lo_window.reparent(self.container_window, 0, 0)
            
            # Step 2: Send XEMBED_EMBEDDED_NOTIFY message
            self.send_xembed_message(
                self.lo_window,
                XEMBED_EMBEDDED_NOTIFY,
                0,
                self.container_window.id,
                0
            )
            
            # Step 3: Configure window size
            self.lo_window.configure(
                width=self.config['container_size']['width'],
                height=self.config['container_size']['height']
            )
            
            # Step 4: Map the window if not already mapped
            self.lo_window.map()
            
            # Step 5: Send XEMBED_WINDOW_ACTIVATE
            self.send_xembed_message(
                self.lo_window,
                XEMBED_WINDOW_ACTIVATE,
                0, 0, 0
            )
            
            # Step 6: Send XEMBED_FOCUS_IN
            self.send_xembed_message(
                self.lo_window,
                XEMBED_FOCUS_IN,
                0, 0, 0
            )
            
            self.display.sync()
            
            self.logger.info("XEmbed protocol completed")
            
            # Give it a moment to settle
            time.sleep(2)
            
            # Verify embedding
            return self.verify_embedding()
            
        except Exception as e:
            self.logger.error(f"Error during XEmbed embedding: {e}")
            return False
    
    def send_xembed_message(self, window, message, detail, data1, data2):
        """Send XEmbed message to window"""
        try:
            # Create ClientMessage event
            ev = event.ClientMessage(
                window=window,
                client_type=self.xembed_atom,
                data=(32, [message, detail, data1, data2, 0])
            )
            
            # Send event
            window.send_event(ev, event_mask=X.NoEventMask)
            self.display.sync()
            
            self.logger.debug(f"Sent XEmbed message: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to send XEmbed message: {e}")
    
    def verify_embedding(self):
        """Verify that embedding was successful"""
        if not self.lo_window:
            return False
        
        try:
            # Query window attributes
            geom = self.lo_window.get_geometry()
            parent = self.lo_window.query_tree().parent
            
            self.logger.info(f"Window geometry: {geom.width}x{geom.height} at ({geom.x},{geom.y})")
            self.logger.info(f"Parent window ID: 0x{parent.id:x}")
            self.logger.info(f"Expected parent ID: 0x{self.container_window.id:x}")
            
            if parent.id == self.container_window.id:
                self.logger.info("✓ XEmbed embedding verified!")
                return True
            else:
                self.logger.warning("Parent window doesn't match container")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying embedding: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.lo_process:
            self.lo_process.terminate()
            self.lo_process = None
        
        if self.container_window:
            try:
                self.container_window.destroy()
            except:
                pass
        
        if self.display:
            try:
                self.display.close()
            except:
                pass
    
    def run(self, vcl_plugin, wait_time):
        """Run the test with specified parameters"""
        if not XLIB_AVAILABLE:
            return {'success': False, 'error': 'python-xlib not available'}
        
        self.logger.info(f"Running XEmbed protocol test (VCL: {vcl_plugin}, wait: {wait_time}s)")
        
        try:
            # Create XEmbed container window
            if not self.create_container_window():
                return {'success': False, 'error': 'Failed to create XEmbed container'}
            
            # Launch LibreOffice
            if not self.launch_libreoffice(vcl_plugin):
                return {'success': False, 'error': 'Failed to launch LibreOffice'}
            
            # Find LibreOffice window
            if not self.find_libreoffice_window(wait_time):
                return {'success': False, 'error': 'Failed to find LibreOffice window'}
            
            # Embed window using XEmbed protocol
            if not self.embed_window():
                return {'success': False, 'error': 'Failed to embed window with XEmbed'}
            
            # Keep window open for screenshot
            time.sleep(3)
            
            return {
                'success': True,
                'method': 'XEmbed Protocol',
                'vcl_plugin': vcl_plugin,
                'container_id': f"0x{self.container_window.id:x}",
                'libreoffice_id': f"0x{self.lo_window.id:x}",
                'xembed_supported': True
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
    result = test.run('gtk3', 3)
    print(f"Result: {result}")