#!/usr/bin/env python3
"""
Test 05: Window Manager Hints Lock approach
Uses window manager hints to lock LibreOffice window in container
"""

import os
import time
import subprocess
from pathlib import Path

try:
    from Xlib import X, display, Xatom
    from Xlib.protocol import rq
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False

# Window manager hint constants
_NET_WM_STATE_REMOVE = 0
_NET_WM_STATE_ADD = 1
_NET_WM_STATE_TOGGLE = 2

class EmbeddingTest:
    def __init__(self, config, test_dir, logger):
        self.config = config
        self.test_dir = test_dir
        self.logger = logger
        self.display = None
        self.container_window = None
        self.lo_process = None
        self.lo_window = None
        self.wm_atoms = {}
        
    def create_container_window(self):
        """Create a container window with proper WM hints"""
        if not XLIB_AVAILABLE:
            self.logger.error("python-xlib not available")
            return False
        
        self.logger.info("Creating container window with WM hints...")
        
        try:
            # Open X display
            self.display = display.Display()
            screen = self.display.screen()
            root = screen.root
            
            # Get important atoms
            self.wm_atoms = {
                '_NET_WM_STATE': self.display.intern_atom('_NET_WM_STATE'),
                '_NET_WM_STATE_ABOVE': self.display.intern_atom('_NET_WM_STATE_ABOVE'),
                '_NET_WM_STATE_STICKY': self.display.intern_atom('_NET_WM_STATE_STICKY'),
                '_NET_WM_STATE_SKIP_TASKBAR': self.display.intern_atom('_NET_WM_STATE_SKIP_TASKBAR'),
                '_NET_WM_STATE_SKIP_PAGER': self.display.intern_atom('_NET_WM_STATE_SKIP_PAGER'),
                '_NET_WM_WINDOW_TYPE': self.display.intern_atom('_NET_WM_WINDOW_TYPE'),
                '_NET_WM_WINDOW_TYPE_DOCK': self.display.intern_atom('_NET_WM_WINDOW_TYPE_DOCK'),
                '_NET_WM_WINDOW_TYPE_NORMAL': self.display.intern_atom('_NET_WM_WINDOW_TYPE_NORMAL'),
                '_MOTIF_WM_HINTS': self.display.intern_atom('_MOTIF_WM_HINTS'),
                'WM_TRANSIENT_FOR': self.display.intern_atom('WM_TRANSIENT_FOR')
            }
            
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
                           X.SubstructureRedirectMask | X.FocusChangeMask)
            )
            
            # Set window properties
            self.container_window.set_wm_name("LibreOffice Container - Test 05")
            self.container_window.set_wm_class("libreoffice_container", "LibreOfficeContainer")
            
            # Set window type hint
            self.container_window.change_property(
                self.wm_atoms['_NET_WM_WINDOW_TYPE'],
                Xatom.ATOM,
                32,
                [self.wm_atoms['_NET_WM_WINDOW_TYPE_NORMAL']]
            )
            
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
        """Find LibreOffice window"""
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
    
    def lock_window_with_hints(self):
        """Use window manager hints to lock LibreOffice window in container"""
        if not self.lo_window or not self.container_window:
            self.logger.error("Missing windows for locking")
            return False
        
        try:
            self.logger.info(f"Locking 0x{self.lo_window.id:x} using WM hints")
            
            # Step 1: Remove window decorations using Motif hints
            # _MOTIF_WM_HINTS structure: flags, functions, decorations, input_mode, status
            motif_hints = [
                2,      # flags: MWM_HINTS_DECORATIONS
                0,      # functions
                0,      # decorations: 0 = no decorations
                0,      # input_mode
                0       # status
            ]
            
            self.lo_window.change_property(
                self.wm_atoms['_MOTIF_WM_HINTS'],
                self.wm_atoms['_MOTIF_WM_HINTS'],
                32,
                motif_hints,
                format=32
            )
            
            # Step 2: Set transient for hint to make it a child of container
            self.lo_window.change_property(
                self.wm_atoms['WM_TRANSIENT_FOR'],
                Xatom.WINDOW,
                32,
                [self.container_window.id]
            )
            
            # Step 3: Reparent the window
            self.lo_window.reparent(self.container_window, 0, 0)
            
            # Step 4: Configure window size
            self.lo_window.configure(
                width=self.config['container_size']['width'],
                height=self.config['container_size']['height']
            )
            
            # Step 5: Set window state hints to prevent movement
            # Remove ability to move/resize
            self.send_client_message(
                self.lo_window,
                self.wm_atoms['_NET_WM_STATE'],
                [_NET_WM_STATE_ADD, 
                 self.wm_atoms['_NET_WM_STATE_STICKY'],
                 0, 1, 0]
            )
            
            # Step 6: Set override redirect to bypass WM completely
            self.lo_window.change_attributes(override_redirect=1)
            
            # Step 7: Grab pointer to prevent dragging
            self.container_window.grab_button(
                X.AnyButton,
                X.NoModifier,
                True,
                X.ButtonPressMask | X.ButtonReleaseMask,
                X.GrabModeSync,
                X.GrabModeAsync,
                X.NONE,
                X.NONE
            )
            
            # Sync all changes
            self.display.sync()
            
            self.logger.info("Window locked with WM hints")
            
            # Give it a moment to settle
            time.sleep(2)
            
            # Verify locking
            return self.verify_locking()
            
        except Exception as e:
            self.logger.error(f"Error during window locking: {e}")
            return False
    
    def send_client_message(self, window, message_type, data):
        """Send a client message to the window manager"""
        event = rq.ClientMessage(
            window=window,
            client_type=message_type,
            data=(32, data)
        )
        
        root = self.display.screen().root
        root.send_event(event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        self.display.sync()
    
    def verify_locking(self):
        """Verify that window is locked in container"""
        if not self.lo_window:
            return False
        
        try:
            # Query window attributes
            geom = self.lo_window.get_geometry()
            parent = self.lo_window.query_tree().parent
            attrs = self.lo_window.get_attributes()
            
            self.logger.info(f"Window geometry: {geom.width}x{geom.height} at ({geom.x},{geom.y})")
            self.logger.info(f"Parent window ID: 0x{parent.id:x}")
            self.logger.info(f"Expected parent ID: 0x{self.container_window.id:x}")
            self.logger.info(f"Override redirect: {attrs.override_redirect}")
            
            # Check if properly locked
            checks = []
            
            # Check 1: Parent is container
            if parent.id == self.container_window.id:
                self.logger.info("✓ Window is child of container")
                checks.append(True)
            else:
                self.logger.warning("✗ Window is not child of container")
                checks.append(False)
            
            # Check 2: Position is (0, 0)
            if geom.x == 0 and geom.y == 0:
                self.logger.info("✓ Window is at correct position")
                checks.append(True)
            else:
                self.logger.warning(f"✗ Window is at ({geom.x}, {geom.y})")
                checks.append(False)
            
            # Check 3: Override redirect is set
            if attrs.override_redirect:
                self.logger.info("✓ Override redirect is set")
                checks.append(True)
            else:
                self.logger.warning("✗ Override redirect not set")
                checks.append(False)
            
            # All checks must pass
            return all(checks)
                
        except Exception as e:
            self.logger.error(f"Error verifying locking: {e}")
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
        
        self.logger.info(f"Running WM hints lock test (VCL: {vcl_plugin}, wait: {wait_time}s)")
        
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
            
            # Lock window with hints
            if not self.lock_window_with_hints():
                return {'success': False, 'error': 'Failed to lock window with WM hints'}
            
            # Keep window open for screenshot
            time.sleep(3)
            
            return {
                'success': True,
                'method': 'Window Manager Hints Lock',
                'vcl_plugin': vcl_plugin,
                'container_id': f"0x{self.container_window.id:x}",
                'libreoffice_id': f"0x{self.lo_window.id:x}",
                'locked': True
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