"""
DocAI Native - Enterprise Main Application
Enhanced startup/shutdown with dynamic ports, robust logging, and signal handling
"""

import webview
import threading
import socket
import signal
import sys
import os
import time
import logging
import logging.handlers
import argparse
from pathlib import Path
from werkzeug.serving import make_server
from contextlib import contextmanager

from config import CFG
from backend_server import create_app
from native_api_simple import SimpleNativeAPI
from native_api_dict import api_dict, set_window
from native_api_hybrid import hybrid_api, set_window as hybrid_set_window
from native_api_lambda import lambda_api, set_window_ref as lambda_set_window
from native_api_fixed import FixedAPI
from uno_bridge import UNOSocketBridge


class ApplicationContext:
    """Manages application lifecycle and resources"""
    
    def __init__(self):
        self.flask_server = None
        self.uno_bridge = None
        self.native_api = None
        self.window = None
        self.logger = None
        self.shutdown_event = threading.Event()
        self.hot_reload_thread = None
        
    def setup_logging(self):
        """Configure enterprise logging with rotation"""
        # Ensure logs directory exists
        log_dir = CFG.LOG_FILE.parent
        log_dir.mkdir(exist_ok=True)
        
        # Root logger setup
        self.logger = logging.getLogger(__name__)
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, CFG.LOG_LEVEL))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with context
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            CFG.LOG_FILE,
            maxBytes=CFG.LOG_MAX_BYTES,
            backupCount=CFG.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(getattr(logging, CFG.LOG_LEVEL))
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Configure specific loggers
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        
        self.logger.info(f"Logging configured - Level: {CFG.LOG_LEVEL}")
        self.logger.info(f"Log file: {CFG.LOG_FILE}")
        
    def get_free_port(self):
        """Get a free port from the OS"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        self.logger.info(f"Allocated free port: {port}")
        return port
    
    def validate_dependencies(self):
        """Validate LibreOffice and fail fast if missing"""
        self.logger.info("Validating dependencies...")
        
        # Check LibreOffice path
        lo_path = Path(CFG.LIBREOFFICE_PATH)
        if not lo_path.exists():
            self.logger.error(f"LibreOffice not found at: {CFG.LIBREOFFICE_PATH}")
            self.logger.error("Please install LibreOffice or update the path in config")
            return False
            
        self.logger.info(f"LibreOffice found: {CFG.LIBREOFFICE_PATH}")
        
        # Check Python UNO
        try:
            import uno
            self.logger.info("Python UNO module available")
        except ImportError:
            self.logger.warning("Python UNO not available - some features may be limited")
            self.logger.warning("Install with: sudo apt-get install python3-uno")
        
        return True
    
    def start_flask_server(self, port):
        """Start Flask server with proper WSGI server"""
        self.logger.info(f"Starting Flask server on port {port}")
        
        # Pass UNO bridge to Flask app if available
        app = create_app(uno_bridge=self.uno_bridge)
        
        # Create WSGI server
        self.flask_server = make_server('127.0.0.1', port, app, threaded=True)
        
        # Get actual port (important when port=0)
        actual_port = self.flask_server.server_port
        self.logger.info(f"Flask server bound to port {actual_port}")
        
        # Start server in thread
        server_thread = threading.Thread(
            target=self.flask_server.serve_forever,
            daemon=True,
            name="FlaskServer"
        )
        server_thread.start()
        
        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < CFG.BACKEND_STARTUP_TIMEOUT:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(('127.0.0.1', actual_port))
                    self.logger.info("Flask server is ready")
                    return actual_port
            except ConnectionRefusedError:
                time.sleep(0.1)
        
        raise RuntimeError(f"Flask server failed to start within {CFG.BACKEND_STARTUP_TIMEOUT}s")
    
    def start_uno_bridge(self):
        """Start UNO bridge with dynamic port and retry logic"""
        self.logger.info("Starting UNO bridge...")
        
        for attempt in range(CFG.UNO_RETRY_COUNT):
            try:
                uno_port = self.get_free_port()
                self.uno_bridge = UNOSocketBridge(port=uno_port)
                
                if self.uno_bridge.start_libreoffice_server():
                    self.logger.info(f"UNO bridge started on port {uno_port}")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"UNO bridge attempt {attempt + 1} failed: {e}")
                if attempt < CFG.UNO_RETRY_COUNT - 1:
                    time.sleep(CFG.UNO_RETRY_DELAY)
        
        self.logger.error("Failed to start UNO bridge after all retries")
        return False
    
    def setup_hot_reload(self):
        """Setup hot reload for development"""
        if not CFG.HOT_RELOAD:
            return
            
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class ReloadHandler(FileSystemEventHandler):
                def __init__(self, window):
                    self.window = window
                    self.logger = logging.getLogger(self.__class__.__name__)
                    
                def on_modified(self, event):
                    if event.is_directory:
                        return
                    if event.src_path.endswith(('.html', '.css', '.js')):
                        self.logger.info(f"Frontend file changed: {event.src_path}")
                        if self.window:
                            self.window.reload()
            
            observer = Observer()
            observer.schedule(
                ReloadHandler(self.window),
                str(CFG.FRONTEND_DIR),
                recursive=True
            )
            observer.start()
            
            self.hot_reload_thread = observer
            self.logger.info("Hot reload enabled for frontend files")
            
        except ImportError:
            self.logger.warning("Watchdog not available - hot reload disabled")
    
    def create_window(self, port):
        """Create and configure the main window"""
        self.logger.info("Creating application window...")
        
        # Use FixedAPI class instance for PyWebView compatibility
        self.logger.info("Using FixedAPI class instance for PyWebView")
        self.native_api = FixedAPI()
        self.logger.info(f"Native API type: {type(self.native_api)}")
        self.logger.info(f"Native API class: {self.native_api.__class__.__name__}")
        
        # Verify the methods are callable
        for method_name in ['pickFile', 'checkLibreOffice', 'embedDocument']:
            if hasattr(self.native_api, method_name):
                method = getattr(self.native_api, method_name)
                self.logger.info(f"✓ {method_name}: {type(method)}")
            else:
                self.logger.error(f"✗ {method_name}: NOT FOUND")
        
        # Clear PyWebView cache before creating window
        import shutil
        import tempfile
        cache_paths = [
            Path.home() / '.pywebview',
            Path(tempfile.gettempdir()) / 'pywebview',
            Path.home() / 'AppData' / 'Local' / 'pywebview' / 'EBWebView',  # Windows
            Path.home() / '.cache' / 'pywebview',  # Linux
            Path.home() / 'Library' / 'Caches' / 'pywebview',  # macOS
        ]
        
        for cache_path in cache_paths:
            if cache_path.exists():
                try:
                    shutil.rmtree(cache_path)
                    self.logger.info(f"Cleared cache at: {cache_path}")
                except Exception as e:
                    self.logger.warning(f"Could not clear cache at {cache_path}: {e}")
        
        # Create window
        self.window = webview.create_window(
            title=f"{CFG.APP_NAME} v{CFG.VERSION}",
            url=f'http://127.0.0.1:{port}',
            width=CFG.WINDOW_WIDTH,
            height=CFG.WINDOW_HEIGHT,
            min_size=(CFG.WINDOW_MIN_WIDTH, CFG.WINDOW_MIN_HEIGHT),
            resizable=True,
            js_api=self.native_api
        )
        
        # Set window reference in API
        if hasattr(self.native_api, 'set_window'):
            self.native_api.set_window(self.window)
            self.logger.info("Window reference set in SimpleNativeAPI")
        else:
            self.logger.error("set_window method not found in API!")
        
        # Setup hot reload
        self.setup_hot_reload()
        
        return self.window
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        self._shutting_down = False
        
        def signal_handler(signum, frame):
            if self._shutting_down:
                # Already shutting down, force exit
                self.logger.warning("Force exit requested")
                os._exit(1)
            
            self._shutting_down = True
            self.logger.info(f"Received shutdown signal: {signum}")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Window closing handler
        if self.window:
            self.window.events.closing += self.shutdown
    
    def on_window_ready(self):
        """Called when window is ready"""
        self.logger.info("Application window is ready")
    
    def shutdown(self):
        """Graceful shutdown of all components"""
        if self.shutdown_event.is_set():
            return  # Already shutting down
            
        self.logger.info("Initiating graceful shutdown...")
        self.shutdown_event.set()
        
        # Stop hot reload
        if self.hot_reload_thread:
            try:
                self.hot_reload_thread.stop()
                self.logger.info("Hot reload watcher stopped")
            except Exception as e:
                self.logger.error(f"Error stopping hot reload: {e}")
        
        # Shutdown UNO bridge
        if self.uno_bridge:
            try:
                self.uno_bridge.shutdown()
                self.logger.info("UNO bridge shutdown complete")
            except Exception as e:
                self.logger.error(f"Error shutting down UNO bridge: {e}")
        
        # Shutdown Flask server
        if self.flask_server:
            try:
                self.flask_server.shutdown()
                self.logger.info("Flask server shutdown complete")
            except Exception as e:
                self.logger.error(f"Error shutting down Flask server: {e}")
        
        # Destroy window if exists
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
        
        self.logger.info("Graceful shutdown complete")
        
        # Force exit immediately
        os._exit(0)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=f"{CFG.APP_NAME} - Native Document AI Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Start normally
  python main.py --debug                  # Enable debug mode
  python main.py --open document.docx     # Open file on startup
  python main.py --port 8080              # Use specific port
        """
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode with verbose logging'
    )
    
    parser.add_argument(
        '--port', 
        type=int,
        help='Specify Flask server port (default: random)'
    )
    
    parser.add_argument(
        '--open', 
        type=str,
        metavar='FILE',
        help='Open specified file on startup'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f"{CFG.APP_NAME} {CFG.VERSION}"
    )
    
    return parser.parse_args()


def main():
    """Main application entry point with enterprise startup flow"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Apply CLI overrides
    if args.debug:
        CFG.DEBUG = True
        CFG.LOG_LEVEL = "DEBUG"
        CFG.HOT_RELOAD = True
    
    if args.port:
        CFG.FLASK_PORT = args.port
    
    if args.open:
        startup_path = Path(args.open).resolve()
        if startup_path.exists():
            CFG.STARTUP_FILE = startup_path
        else:
            print(f"Error: Startup file not found: {args.open}")
            sys.exit(1)
    
    # Initialize application context
    app_ctx = ApplicationContext()
    
    try:
        # 1. Configure rotating logs
        app_ctx.setup_logging()
        app_ctx.logger.info(f"Starting {CFG.APP_NAME} v{CFG.VERSION}")
        app_ctx.logger.info(f"Debug mode: {CFG.DEBUG}")
        app_ctx.logger.info(f"Startup file: {CFG.STARTUP_FILE}")
        
        # 2. Check dependencies & fail fast
        if not app_ctx.validate_dependencies():
            app_ctx.logger.error("Dependency validation failed")
            sys.exit(1)
        
        # 3. Get dynamic port
        port = CFG.FLASK_PORT or app_ctx.get_free_port()
        
        # 4. Start UNO bridge with retry logic (before Flask to enable window manager)
        if not app_ctx.start_uno_bridge():
            app_ctx.logger.warning("UNO bridge failed - continuing without LibreOffice integration")
        
        # 5. Start Flask server with WSGI (after UNO bridge so it can initialize window manager)
        actual_port = app_ctx.start_flask_server(port)
        
        # 6. Create window and native API
        window = app_ctx.create_window(actual_port)
        
        # 7. Setup signal handlers and shutdown hooks
        app_ctx.setup_signal_handlers()
        
        # 8. Setup window ready callback
        window.events.loaded += app_ctx.on_window_ready
        
        # 9. Start GUI (blocking call)
        app_ctx.logger.info("Starting GUI main loop...")
        webview.start(debug=CFG.DEBUG)
        
    except KeyboardInterrupt:
        app_ctx.logger.info("Interrupted by user")
    except Exception as e:
        app_ctx.logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        app_ctx.shutdown()


if __name__ == '__main__':
    main()