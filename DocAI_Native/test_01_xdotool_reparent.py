#!/usr/bin/env python3
"""
Test 01: xdotool windowreparent approach
Uses xdotool to reparent LibreOffice window into a container
"""

import os
import time
import subprocess
import tkinter as tk
from pathlib import Path

class EmbeddingTest:
    def __init__(self, config, test_dir, logger):
        self.config = config
        self.test_dir = test_dir
        self.logger = logger
        self.container_window_id = None
        self.lo_process = None
        self.lo_window_id = None
        
    def create_container_window(self):
        """Create a container window using tkinter"""
        self.logger.info("Creating container window...")
        
        # Create tkinter window
        self.root = tk.Tk()
        self.root.title("LibreOffice Container - Test 01")
        self.root.geometry(f"{self.config['container_size']['width']}x{self.config['container_size']['height']}")
        
        # Add label
        label = tk.Label(self.root, text="LibreOffice should appear here", bg='lightblue')
        label.pack(fill=tk.BOTH, expand=True)
        
        # Update to ensure window is created
        self.root.update()
        
        # Get window ID
        window_id = self.root.winfo_id()
        self.container_window_id = hex(window_id)
        self.logger.info(f"Container window created with ID: {self.container_window_id}")
        
        return True
    
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
        """Find LibreOffice window using xdotool"""
        self.logger.info(f"Waiting {wait_time}s for LibreOffice window...")
        time.sleep(wait_time)
        
        try:
            # Search for LibreOffice windows
            result = subprocess.run(
                ['xdotool', 'search', '--class', 'libreoffice'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_ids = result.stdout.strip().split('\n')
                self.logger.info(f"Found {len(window_ids)} LibreOffice windows")
                
                # Get window names to find the right one
                for wid in window_ids:
                    name_result = subprocess.run(
                        ['xdotool', 'getwindowname', wid],
                        capture_output=True,
                        text=True
                    )
                    
                    if name_result.returncode == 0:
                        window_name = name_result.stdout.strip()
                        self.logger.info(f"Window {wid}: {window_name}")
                        
                        # Skip splash screens
                        if 'test_embed' in window_name or 'LibreOffice' in window_name and 'Start' not in window_name:
                            self.lo_window_id = wid
                            self.logger.info(f"Selected LibreOffice window: {wid}")
                            return True
                
            self.logger.warning("No suitable LibreOffice window found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding LibreOffice window: {e}")
            return False
    
    def reparent_window(self):
        """Reparent LibreOffice window into container using xdotool"""
        if not self.lo_window_id or not self.container_window_id:
            self.logger.error("Missing window IDs for reparenting")
            return False
        
        try:
            self.logger.info(f"Reparenting {self.lo_window_id} into {self.container_window_id}")
            
            # First, remove window decorations
            subprocess.run([
                'xdotool', 'set_window', '--overrideredirect', '1', self.lo_window_id
            ])
            
            # Reparent the window
            result = subprocess.run([
                'xdotool', 'windowreparent', self.lo_window_id, self.container_window_id
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Reparent failed: {result.stderr}")
                return False
            
            # Move to position 0,0 within container
            subprocess.run([
                'xdotool', 'windowmove', '--relative', self.lo_window_id, '0', '0'
            ])
            
            # Resize to fill container
            subprocess.run([
                'xdotool', 'windowsize', self.lo_window_id,
                str(self.config['container_size']['width']),
                str(self.config['container_size']['height'])
            ])
            
            self.logger.info("Window reparented successfully")
            
            # Update tkinter window to show changes
            self.root.update()
            
            # Give it a moment to settle
            time.sleep(2)
            
            # Verify reparenting
            return self.verify_reparenting()
            
        except Exception as e:
            self.logger.error(f"Error during reparenting: {e}")
            return False
    
    def verify_reparenting(self):
        """Verify that reparenting was successful"""
        try:
            # Get window info
            result = subprocess.run(
                ['xwininfo', '-id', self.lo_window_id],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Check if parent is our container
                for line in output.split('\n'):
                    if 'Parent window id:' in line:
                        parent_id = line.split(':')[1].strip()
                        self.logger.info(f"Parent window ID: {parent_id}")
                        
                        # Convert container ID to same format for comparison
                        container_id_int = int(self.container_window_id, 16)
                        if parent_id == hex(container_id_int) or parent_id == str(container_id_int):
                            self.logger.info("✓ Reparenting verified!")
                            return True
                
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
        
        if hasattr(self, 'root'):
            try:
                self.root.destroy()
            except:
                pass
    
    def run(self, vcl_plugin, wait_time):
        """Run the test with specified parameters"""
        self.logger.info(f"Running xdotool reparent test (VCL: {vcl_plugin}, wait: {wait_time}s)")
        
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
                'method': 'xdotool windowreparent',
                'vcl_plugin': vcl_plugin,
                'container_id': self.container_window_id,
                'libreoffice_id': self.lo_window_id
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