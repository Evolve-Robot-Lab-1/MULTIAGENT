#!/usr/bin/env python3
"""
Test 06: Composite Overlay approach
Uses X11 Composite extension to create transparent overlay
"""

import os
import time
import subprocess
from pathlib import Path

try:
    from Xlib import X, display
    from Xlib.ext import composite, shape
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
        self.overlay_window = None
        self.lo_process = None
        self.lo_window = None
        self.composite_available = False
        
    def check_composite_extension(self):
        """Check if Composite extension is available"""
        try:
            if not self.display:
                return False
            
            # Check if composite extension is available
            if hasattr(self.display, 'has_extension') and self.display.has_extension('Composite'):
                self.logger.info("Composite extension is available")
                return True
            
            # Alternative check
            try:
                composite.query_version(self.display, 0, 4)
                self.logger.info("Composite extension verified")
                return True
            except:
                pass
                
            self.logger.warning("Composite extension not available")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking composite extension: {e}")
            return False
    
    def create_container_window(self):
        """Create a container window with composite support"""
        if not XLIB_AVAILABLE:
            self.logger.error("python-xlib not available")
            return False
        
        self.logger.info("Creating composite container window...")
        
        try:
            # Open X display
            self.display = display.Display()
            screen = self.display.screen()
            root = screen.root
            
            # Check composite extension
            self.composite_available = self.check_composite_extension()
            
            # Create main container window
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
                           X.StructureNotifyMask | X.SubstructureNotifyMask)
            )
            
            # Set window properties
            self.container_window.set_wm_name("LibreOffice Container - Test 06")
            self.container_window.set_wm_class("libreoffice_container", "LibreOfficeContainer")
            
            # Map (show) the window
            self.container_window.map()
            
            # Create transparent overlay window
            self.overlay_window = self.container_window.create_window(
                0, 0,  # x, y relative to container
                self.config['container_size']['width'],
                self.config['container_size']['height'],
                0,  # border width
                screen.root_depth,
                X.InputOutput,
                X.CopyFromParent,
                background_pixel=0,  # transparent
                event_mask=(X.ExposureMask | X.KeyPressMask | 
                           X.ButtonPressMask | X.ButtonReleaseMask |
                           X.PointerMotionMask)
            )
            
            # Make overlay transparent if composite is available
            if self.composite_available:
                try:
                    # Set window opacity
                    opacity_atom = self.display.intern_atom('_NET_WM_WINDOW_OPACITY')
                    # 0.5 opacity = 0x7fffffff
                    self.overlay_window.change_property(
                        opacity_atom,
                        X.Xatom.CARDINAL,
                        32,
                        [0x7fffffff]
                    )
                except:
                    self.logger.warning("Failed to set window opacity")
            
            # Map overlay
            self.overlay_window.map()
            self.display.sync()
            
            self.logger.info(f"Container window created with ID: 0x{self.container_window.id:x}")
            self.logger.info(f"Overlay window created with ID: 0x{self.overlay_window.id:x}")
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
    
    def apply_composite_overlay(self):
        """Apply composite overlay technique"""
        if not self.lo_window or not self.container_window:
            self.logger.error("Missing windows for composite overlay")
            return False
        
        try:
            self.logger.info(f"Applying composite overlay to 0x{self.lo_window.id:x}")
            
            # Get current window position
            geom = self.lo_window.get_geometry()
            self.logger.info(f"Current LibreOffice position: ({geom.x}, {geom.y})")
            
            # Get container position
            container_geom = self.container_window.get_geometry()
            container_pos = self.container_window.translate_coords(
                self.display.screen().root, 0, 0
            )
            self.logger.info(f"Container position: ({container_pos.x}, {container_pos.y})")
            
            # Calculate relative position
            target_x = container_pos.x
            target_y = container_pos.y
            
            # Method 1: Direct positioning
            self.logger.info("Method 1: Direct window positioning")
            self.lo_window.configure(
                x=target_x,
                y=target_y,
                width=self.config['container_size']['width'],
                height=self.config['container_size']['height']
            )
            self.display.sync()
            time.sleep(1)
            
            # Method 2: Use wmctrl for positioning
            self.logger.info("Method 2: Using wmctrl")
            try:
                subprocess.run([
                    'wmctrl', '-i', '-r', f"0x{self.lo_window.id:x}",
                    '-e', f"0,{target_x},{target_y},{self.config['container_size']['width']},{self.config['container_size']['height']}"
                ])
            except:
                self.logger.warning("wmctrl positioning failed")
            
            # Method 3: Reparent to container (composite style)
            if self.composite_available:
                self.logger.info("Method 3: Composite reparenting")
                try:
                    # Redirect window for compositing
                    composite.redirect_window(self.lo_window, composite.RedirectAutomatic)
                    
                    # Reparent
                    self.lo_window.reparent(self.container_window, 0, 0)
                    
                    # Unredirect after reparenting
                    composite.unredirect_window(self.lo_window, composite.RedirectAutomatic)
                    
                    self.display.sync()
                except Exception as e:
                    self.logger.warning(f"Composite reparenting failed: {e}")
            
            # Method 4: Shape extension masking
            try:
                self.logger.info("Method 4: Shape extension masking")
                
                # Create a region that covers the container
                shape.shape_rectangles(
                    self.overlay_window,
                    shape.SO.Set,
                    shape.SK.Bounding,
                    0,  # x_offset
                    0,  # y_offset
                    [(0, 0, self.config['container_size']['width'], 
                      self.config['container_size']['height'])]
                )
                
                # Make overlay click-through
                shape.shape_rectangles(
                    self.overlay_window,
                    shape.SO.Set,
                    shape.SK.Input,
                    0, 0,
                    []  # Empty = no input
                )
                
            except Exception as e:
                self.logger.warning(f"Shape extension failed: {e}")
            
            # Final sync
            self.display.sync()
            time.sleep(2)
            
            # Verify overlay
            return self.verify_overlay()
            
        except Exception as e:
            self.logger.error(f"Error during composite overlay: {e}")
            return False
    
    def verify_overlay(self):
        """Verify that overlay is working"""
        if not self.lo_window:
            return False
        
        try:
            # Get final positions
            lo_geom = self.lo_window.get_geometry()
            container_pos = self.container_window.translate_coords(
                self.display.screen().root, 0, 0
            )
            
            self.logger.info(f"Final LibreOffice position: ({lo_geom.x}, {lo_geom.y})")
            self.logger.info(f"Container position: ({container_pos.x}, {container_pos.y})")
            
            # Calculate overlap
            x_overlap = (lo_geom.x < container_pos.x + self.config['container_size']['width'] and
                        lo_geom.x + lo_geom.width > container_pos.x)
            y_overlap = (lo_geom.y < container_pos.y + self.config['container_size']['height'] and
                        lo_geom.y + lo_geom.height > container_pos.y)
            
            if x_overlap and y_overlap:
                self.logger.info("✓ Windows are overlapping")
                
                # Check if perfectly aligned
                if (abs(lo_geom.x - container_pos.x) < 10 and 
                    abs(lo_geom.y - container_pos.y) < 10):
                    self.logger.info("✓ Windows are well aligned")
                    return True
                else:
                    self.logger.warning("Windows overlap but not perfectly aligned")
                    return True  # Still consider it a success
            else:
                self.logger.warning("✗ Windows are not overlapping")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying overlay: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.lo_process:
            self.lo_process.terminate()
            self.lo_process = None
        
        if self.overlay_window:
            try:
                self.overlay_window.destroy()
            except:
                pass
        
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
        
        self.logger.info(f"Running composite overlay test (VCL: {vcl_plugin}, wait: {wait_time}s)")
        
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
            
            # Apply composite overlay
            if not self.apply_composite_overlay():
                return {'success': False, 'error': 'Failed to apply composite overlay'}
            
            # Keep window open for screenshot
            time.sleep(3)
            
            return {
                'success': True,
                'method': 'Composite Overlay',
                'vcl_plugin': vcl_plugin,
                'container_id': f"0x{self.container_window.id:x}",
                'overlay_id': f"0x{self.overlay_window.id:x}",
                'libreoffice_id': f"0x{self.lo_window.id:x}",
                'composite_available': self.composite_available
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