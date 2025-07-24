#!/usr/bin/env python3
"""
Test 02: Direct XReparentWindow approach using python-xlib
Uses X11 library directly to reparent LibreOffice window
"""

import os
import time
import subprocess
from pathlib import Path

try:
    from Xlib import X, display
    from Xlib.error import BadWindow
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False

class EmbeddingTest:
    def __init__(self, config, test_dir, logger):
        self.config = config
        self.test_dir = test_dir
        self.logger = logger
        self.display = None
        self.container_window = None
        self.lo_process = None
        self.lo_window = None
        
    def create_container_window(self):
        """Create a container window using Xlib"""
        if not XLIB_AVAILABLE:
            self.logger.error("python-xlib not available")
            return False
        
        self.logger.info("Creating X11 container window...")
        
        try:
            # Open X display
            self.display = display.Display()
            screen = self.display.screen()
            root = screen.root
            
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
                event_mask=X.ExposureMask | X.KeyPressMask | X.StructureNotifyMask
            )
            
            # Set window properties
            self.container_window.set_wm_name("LibreOffice Container - Test 02")
            self.container_window.set_wm_class("libreoffice_container", "LibreOfficeContainer")
            
            # Map (show) the window
            self.container_window.map()
            self.display.sync()
            
            self.logger.info(f"Container window created with ID: 0x{self.container_window.id:x}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create container window: {e}")
            return False
    
    def launch_libreoffice(self, vcl_plugin):
        """Launch LibreOffice with specified VCL plugin"""
        self.logger.info(f"Launching LibreOffice with VCL plugin: {vcl_plugin}")
        
        test_file = Path(__file__).parent / self.config['test_document']
        
        env = os.environ.copy()
        env['SAL_USE_VCLPLUGIN'] = vcl_plugin
        
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
        """Find LibreOffice window using Xlib"""
        if not XLIB_AVAILABLE or not self.display:
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
                            self.lo_window = window
                            self.logger.info(f"Selected LibreOffice window: 0x{window.id:x}")
                            return True
                            
                except BadWindow:
                    # Window disappeared, continue
                    continue
                except Exception as e:
                    self.logger.debug(f"Error checking window: {e}")
                    continue
            
            self.logger.warning("No suitable LibreOffice window found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding LibreOffice window: {e}")
            return False
    
    def reparent_window(self):
        """Reparent LibreOffice window using XReparentWindow"""
        if not self.lo_window or not self.container_window:
            self.logger.error("Missing windows for reparenting")
            return False
        
        try:
            self.logger.info(f"Reparenting 0x{self.lo_window.id:x} into 0x{self.container_window.id:x}")
            
            # Unmap window first (hide it)
            self.lo_window.unmap()
            self.display.sync()
            
            # Remove window manager decorations
            # Set override redirect to bypass window manager
            self.lo_window.change_attributes(override_redirect=1)
            
            # Reparent the window
            self.lo_window.reparent(self.container_window, 0, 0)
            
            # Configure window size to fill container
            self.lo_window.configure(
                width=self.config['container_size']['width'],
                height=self.config['container_size']['height']
            )
            
            # Map window again (show it)
            self.lo_window.map()
            
            # Ensure all X11 commands are executed
            self.display.sync()
            
            self.logger.info("Window reparented successfully")
            
            # Give it a moment to settle
            time.sleep(2)
            
            # Verify reparenting
            return self.verify_reparenting()
            
        except Exception as e:
            self.logger.error(f"Error during reparenting: {e}")
            return False
    
    def verify_reparenting(self):
        """Verify that reparenting was successful"""
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
                self.logger.info("✓ Reparenting verified!")
                return True
            else:
                self.logger.warning("Parent window doesn't match container")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying reparenting: {e}")
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
        
        self.logger.info(f"Running XReparentWindow test (VCL: {vcl_plugin}, wait: {wait_time}s)")
        
        try:
            # Create container window
            if not self.create_container_window():
                return {'success': False, 'error': 'Failed to create container window'}
            
            # Launch LibreOffice
            if not self.launch_libreoffice(vcl_plugin):
                return {'success': False, 'error': 'Failed to launch LibreOffice'}
            
            # Find LibreOffice window
            if not self.find_libreoffice_window(wait_time):
                return {'success': False, 'error': 'Failed to find LibreOffice window'}
            
            # Reparent window
            if not self.reparent_window():
                return {'success': False, 'error': 'Failed to reparent window'}
            
            # Keep window open for screenshot
            time.sleep(3)
            
            return {
                'success': True,
                'method': 'XReparentWindow (python-xlib)',
                'vcl_plugin': vcl_plugin,
                'container_id': f"0x{self.container_window.id:x}",
                'libreoffice_id': f"0x{self.lo_window.id:x}"
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