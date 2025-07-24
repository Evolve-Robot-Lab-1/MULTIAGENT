#!/usr/bin/env python3
"""
Automated LibreOffice Embedding Test Suite
Runs all embedding approaches sequentially and logs results
"""

import os
import sys
import time
import json
import logging
import subprocess
import importlib
from datetime import datetime
from pathlib import Path
import traceback

# Setup paths
SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR / "embedding_tests_results"
CONFIG_FILE = SCRIPT_DIR / "test_config.json"

# Test modules to run in order
TEST_MODULES = [
    "test_01_xdotool_reparent",
    "test_02_xreparent_direct", 
    "test_03_gtk_socket_vcl",
    "test_04_xembed_protocol",
    "test_05_wm_hints_lock",
    "test_06_composite_overlay"
]

class TestRunner:
    def __init__(self):
        self.config = self.load_config()
        self.session_dir = self.create_session_directory()
        self.setup_logging()
        self.results = {}
        
    def load_config(self):
        """Load test configuration"""
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    
    def create_session_directory(self):
        """Create timestamped directory for this test session"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = RESULTS_DIR / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def setup_logging(self):
        """Setup logging for the test session"""
        log_file = self.session_dir / "test_runner.log"
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("TestRunner")
        self.logger.info(f"Test session started: {self.session_dir}")
    
    def check_prerequisites(self):
        """Check if all required tools are installed"""
        self.logger.info("Checking prerequisites...")
        
        tools = {
            'xdotool': 'sudo apt-get install xdotool',
            'wmctrl': 'sudo apt-get install wmctrl',
            'xprop': 'x11-utils package',
            'xwininfo': 'x11-utils package',
            'soffice': 'LibreOffice'
        }
        
        missing = []
        for tool, install_info in tools.items():
            result = subprocess.run(['which', tool], capture_output=True)
            if result.returncode != 0:
                missing.append(f"{tool} ({install_info})")
            else:
                self.logger.info(f"✓ {tool} found")
        
        # Check Python modules
        try:
            import Xlib
            self.logger.info("✓ python-xlib found")
        except ImportError:
            missing.append("python-xlib (pip install python-xlib)")
        
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            self.logger.info("✓ python-gi (GTK) found")
        except:
            missing.append("python-gi (sudo apt-get install python3-gi)")
        
        if missing:
            self.logger.error(f"Missing prerequisites: {', '.join(missing)}")
            return False
        
        # Check display system
        display_system = os.environ.get('XDG_SESSION_TYPE', 'unknown')
        self.logger.info(f"Display system: {display_system}")
        if display_system == 'wayland':
            self.logger.warning("Running on Wayland - X11 embedding may not work properly")
        
        return True
    
    def create_test_document(self):
        """Create test document for embedding tests"""
        test_file = SCRIPT_DIR / self.config['test_document']
        test_file.write_text(self.config['test_content'])
        self.logger.info(f"Created test document: {test_file}")
        return test_file
    
    def cleanup_libreoffice(self):
        """Kill any running LibreOffice processes"""
        subprocess.run(['pkill', 'soffice'], capture_output=True)
        time.sleep(1)
    
    def take_screenshot(self, test_name, description):
        """Take a screenshot of the current state"""
        if not self.config['screenshot_enabled']:
            return
        
        screenshot_dir = self.session_dir / test_name / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%H-%M-%S")
        filename = f"{description}_{timestamp}.png"
        filepath = screenshot_dir / filename
        
        # Use import to take screenshot
        try:
            result = subprocess.run(
                ['import', '-window', 'root', str(filepath)],
                capture_output=True
            )
            if result.returncode == 0:
                self.logger.info(f"Screenshot saved: {filename}")
            else:
                self.logger.warning("Failed to take screenshot")
        except:
            pass
    
    def run_test_module(self, module_name):
        """Run a single test module"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Running test: {module_name}")
        self.logger.info(f"{'='*60}")
        
        test_dir = self.session_dir / module_name
        test_dir.mkdir(exist_ok=True)
        
        # Setup test result structure
        test_result = {
            'module': module_name,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'attempts': []
        }
        
        try:
            # Import test module
            module = importlib.import_module(module_name)
            
            # Create test instance
            test_class = getattr(module, 'EmbeddingTest')
            test = test_class(
                config=self.config,
                test_dir=test_dir,
                logger=self.logger
            )
            
            # Run test with different VCL plugins
            for vcl_plugin in self.config['vcl_plugins']:
                self.logger.info(f"\nTesting with VCL plugin: {vcl_plugin}")
                
                for attempt in range(self.config['max_attempts_per_test']):
                    self.logger.info(f"Attempt {attempt + 1}/{self.config['max_attempts_per_test']}")
                    
                    # Clean up before test
                    if self.config['cleanup_on_failure']:
                        self.cleanup_libreoffice()
                    
                    # Run the test
                    result = test.run(vcl_plugin, self.config['wait_times'][min(attempt, len(self.config['wait_times'])-1)])
                    
                    # Record attempt
                    attempt_data = {
                        'vcl_plugin': vcl_plugin,
                        'attempt': attempt + 1,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    test_result['attempts'].append(attempt_data)
                    
                    # Take screenshot
                    self.take_screenshot(module_name, f"{vcl_plugin}_attempt_{attempt+1}")
                    
                    # Check if successful
                    if result.get('success', False):
                        self.logger.info(f"✓ Success with {vcl_plugin}!")
                        test_result['status'] = 'success'
                        test_result['successful_config'] = {
                            'vcl_plugin': vcl_plugin,
                            'wait_time': self.config['wait_times'][min(attempt, len(self.config['wait_times'])-1)],
                            'details': result
                        }
                        break
                    else:
                        self.logger.warning(f"✗ Failed: {result.get('error', 'Unknown error')}")
                
                # If successful, no need to try other VCL plugins
                if test_result['status'] == 'success':
                    break
            
            if test_result['status'] != 'success':
                test_result['status'] = 'failed'
            
        except Exception as e:
            self.logger.error(f"Test module error: {e}")
            self.logger.error(traceback.format_exc())
            test_result['status'] = 'error'
            test_result['error'] = str(e)
        
        finally:
            test_result['end_time'] = datetime.now().isoformat()
            
            # Save test results
            results_file = test_dir / "results.json"
            with open(results_file, 'w') as f:
                json.dump(test_result, f, indent=2)
            
            # Clean up
            if self.config['cleanup_on_failure']:
                self.cleanup_libreoffice()
        
        return test_result
    
    def generate_html_report(self):
        """Generate HTML report of all tests"""
        html_file = self.session_dir / "final_report.html"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>LibreOffice Embedding Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .test-module {{ 
            border: 1px solid #ddd; 
            margin: 20px 0; 
            padding: 15px;
            border-radius: 5px;
        }}
        .success {{ background-color: #d4edda; }}
        .failed {{ background-color: #f8d7da; }}
        .error {{ background-color: #fff3cd; }}
        .attempt {{ 
            margin: 10px 0; 
            padding: 10px;
            background: #f5f5f5;
            border-radius: 3px;
        }}
        pre {{ 
            background: #f0f0f0; 
            padding: 10px; 
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <h1>LibreOffice Embedding Test Results</h1>
    <p>Session: {self.session_dir.name}</p>
    <p>Total tests: {len(self.results)}</p>
    <p>Successful: {sum(1 for r in self.results.values() if r['status'] == 'success')}</p>
"""
        
        for module_name, result in self.results.items():
            status_class = result['status']
            html_content += f"""
    <div class="test-module {status_class}">
        <h2>{module_name}</h2>
        <p>Status: {result['status']}</p>
"""
            
            if result['status'] == 'success' and 'successful_config' in result:
                config = result['successful_config']
                html_content += f"""
        <h3>Successful Configuration:</h3>
        <ul>
            <li>VCL Plugin: {config['vcl_plugin']}</li>
            <li>Wait Time: {config['wait_time']}s</li>
        </ul>
        <pre>{json.dumps(config['details'], indent=2)}</pre>
"""
            
            html_content += """
        <h3>Attempts:</h3>
"""
            for attempt in result['attempts'][-3:]:  # Show last 3 attempts
                html_content += f"""
        <div class="attempt">
            <strong>VCL: {attempt['vcl_plugin']}, Attempt: {attempt['attempt']}</strong><br>
            Result: {attempt['result'].get('success', False)}<br>
            {f"Error: {attempt['result'].get('error', 'None')}" if not attempt['result'].get('success') else ''}
        </div>
"""
            
            html_content += """
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report generated: {html_file}")
    
    def run_all_tests(self):
        """Run all test modules"""
        self.logger.info("Starting automated LibreOffice embedding tests")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.logger.error("Prerequisites check failed. Exiting.")
            return False
        
        # Create test document
        self.create_test_document()
        
        # Run each test module
        for module_name in TEST_MODULES:
            module_file = SCRIPT_DIR / f"{module_name}.py"
            
            if not module_file.exists():
                self.logger.warning(f"Test module not found: {module_file}")
                self.results[module_name] = {
                    'status': 'skipped',
                    'reason': 'Module file not found'
                }
                continue
            
            try:
                result = self.run_test_module(module_name)
                self.results[module_name] = result
                
                # Check if we should continue
                if not self.config['continue_on_failure'] and result['status'] != 'success':
                    self.logger.warning("Stopping tests due to failure (continue_on_failure=false)")
                    break
                    
            except Exception as e:
                self.logger.error(f"Failed to run {module_name}: {e}")
                self.results[module_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Generate final report
        self.generate_html_report()
        
        # Summary
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST SUMMARY")
        self.logger.info("="*60)
        
        for module_name, result in self.results.items():
            status = result.get('status', 'unknown')
            self.logger.info(f"{module_name}: {status}")
            
            if status == 'success' and 'successful_config' in result:
                config = result['successful_config']
                self.logger.info(f"  → VCL: {config['vcl_plugin']}, Wait: {config['wait_time']}s")
        
        self.logger.info(f"\nResults saved to: {self.session_dir}")
        self.logger.info(f"View report: file://{self.session_dir / 'final_report.html'}")
        
        return True


def main():
    """Main entry point"""
    print("LibreOffice Embedding Automated Test Suite")
    print("="*60)
    
    runner = TestRunner()
    success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()