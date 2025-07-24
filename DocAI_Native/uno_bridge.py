"""
UNO Bridge for LibreOffice Integration
Handles LibreOffice UNO socket communication and document embedding
"""

import subprocess
import time
import os
import socket
import logging
import platform
import uuid
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from collections import OrderedDict
import functools

# UNO imports - will be imported conditionally
uno = None
unohelper = None

from config import CFG

logger = logging.getLogger(__name__)


def with_uno_error_handling(func):
    """Decorator for handling UNO errors with automatic recovery"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        max_retries = 2
        for attempt in range(max_retries):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_type = type(e).__name__
                logger.error(f"{func.__name__} failed (attempt {attempt + 1}): {error_type}: {e}")
                
                # Check if it's a connection-related error
                if any(err in str(e).lower() for err in ['connection', 'disposed', 'socket', 'bridge']):
                    if attempt < max_retries - 1:
                        logger.info("Attempting connection recovery...")
                        if hasattr(self, 'recover_connection') and self.recover_connection():
                            logger.info("Recovery successful, retrying operation...")
                            continue
                
                # If we're here, either it's not recoverable or recovery failed
                if attempt == max_retries - 1:
                    logger.error(f"{func.__name__} failed after all retries")
                    raise
        
        return None
    return wrapper


def import_uno_modules():
    """Import UNO modules dynamically"""
    global uno, unohelper
    try:
        import uno as uno_module
        import unohelper as unohelper_module
        uno = uno_module
        unohelper = unohelper_module
        logger.info("UNO modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"Failed to import UNO modules: {e}")
        logger.error("Install with: sudo apt-get install python3-uno")
        return False


def create_property(name: str, value: Any) -> 'PropertyValue':
    """Create a UNO PropertyValue"""
    if not uno:
        raise RuntimeError("UNO modules not imported")
    
    from com.sun.star.beans import PropertyValue
    prop = PropertyValue()
    prop.Name = name
    prop.Value = value
    return prop


def create_properties(**kwargs) -> tuple:
    """Create multiple PropertyValues from kwargs"""
    return tuple(create_property(k, v) for k, v in kwargs.items())


class UNOConnection:
    """Manages UNO connection to LibreOffice"""
    
    def __init__(self, host='localhost', port=2002):
        self.host = host
        self.port = port
        self.local_context = None
        self.resolver = None
        self.context = None
        self.desktop = None
        self._connected = False
        
    def connect(self, max_retries=3) -> bool:
        """Establish UNO connection with retry logic"""
        if not import_uno_modules():
            return False
            
        from com.sun.star.connection import NoConnectException
        
        for attempt in range(max_retries):
            try:
                # Get local context
                self.local_context = uno.getComponentContext()
                
                # Create UNO URL resolver
                self.resolver = self.local_context.ServiceManager.createInstanceWithContext(
                    "com.sun.star.bridge.UnoUrlResolver", 
                    self.local_context
                )
                
                # Build connection string
                connection_string = (
                    f"uno:socket,host={self.host},port={self.port};"
                    f"urp;StarOffice.ComponentContext"
                )
                
                logger.info(f"Attempting UNO connection: {connection_string}")
                
                # Resolve the connection
                self.context = self.resolver.resolve(connection_string)
                
                # Get desktop service
                self.desktop = self.context.ServiceManager.createInstanceWithContext(
                    "com.sun.star.frame.Desktop",
                    self.context
                )
                
                self._connected = True
                logger.info("UNO connection established successfully")
                return True
                
            except NoConnectException as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Failed to establish UNO connection after all retries")
                    
            except Exception as e:
                logger.error(f"Unexpected error during connection: {e}")
                return False
        
        return False
    
    def disconnect(self):
        """Disconnect from LibreOffice"""
        self._connected = False
        self.desktop = None
        self.context = None
        self.resolver = None
        self.local_context = None
        logger.info("UNO connection closed")


class LoadedDocument:
    """Wrapper for loaded LibreOffice documents"""
    
    def __init__(self, component, file_path: str):
        self.component = component
        self.file_path = file_path
        self.controller = None
        self.frame = None
        self.window = None
        self.doc_id = str(uuid.uuid4())
        self._extract_window_info()
    
    def _extract_window_info(self):
        """Extract window and frame information"""
        try:
            # Get current controller
            self.controller = self.component.getCurrentController()
            if not self.controller:
                raise RuntimeError("No controller available")
            
            # Get frame
            self.frame = self.controller.getFrame()
            if not self.frame:
                raise RuntimeError("No frame available")
            
            # Get container window
            self.window = self.frame.getContainerWindow()
            if not self.window:
                raise RuntimeError("No window available")
                
            logger.info(f"Window info extracted for document: {self.file_path}")
                
        except Exception as e:
            logger.error(f"Failed to extract window info: {e}")
            raise
    
    def get_window_handle_linux(self) -> Optional[Dict[str, Any]]:
        """Get X11 Window ID on Linux"""
        try:
            # Method 1: Try direct UNO method
            toolkit = self.window.getToolkit()
            
            # Try to get window handle through UNO
            if hasattr(self.window, 'getWindowHandle'):
                handle_bytes = self.window.getWindowHandle()
                if handle_bytes:
                    # Convert bytes to window ID
                    import struct
                    window_id = struct.unpack('L', handle_bytes)[0]
                    logger.info(f"Got X11 window ID via UNO: {window_id}")
                    return {'type': 'x11', 'handle': window_id}
            
            # Method 2: Use window title with xwininfo
            title = self.frame.getTitle() or "LibreOffice"
            logger.info(f"Searching for window with title: {title}")
            
            # Wait a bit for window to be created
            time.sleep(0.5)
            
            # Use xwininfo to find window
            import subprocess
            result = subprocess.run(
                ['xwininfo', '-name', title, '-int'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse window ID from output
                for line in result.stdout.split('\n'):
                    if 'Window id:' in line:
                        # Extract the numeric window ID
                        parts = line.split()
                        if len(parts) >= 4:
                            window_id = int(parts[3])
                            logger.info(f"Got X11 window ID via xwininfo: {window_id}")
                            return {'type': 'x11', 'handle': window_id}
            else:
                logger.warning(f"xwininfo failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"X11 handle extraction failed: {e}")
            
        return None
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get document metadata"""
        try:
            doc_props = self.component.getDocumentProperties()
            
            # Get page count
            page_count = 1
            try:
                if hasattr(self.component, 'getDrawPages'):
                    page_count = self.component.getDrawPages().getCount()
                elif hasattr(self.component, 'getTextTables'):
                    # For text documents, estimate pages
                    cursor = self.controller.getViewCursor()
                    cursor.gotoEnd(False)
                    page_count = cursor.getPage()
            except:
                pass
            
            return {
                'doc_id': self.doc_id,
                'title': doc_props.Title or Path(self.file_path).name,
                'author': doc_props.Author,
                'subject': doc_props.Subject,
                'pages': page_count,
                'modified': str(doc_props.ModificationDate) if doc_props.ModificationDate else None,
                'created': str(doc_props.CreationDate) if doc_props.CreationDate else None
            }
        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            return {
                'doc_id': self.doc_id,
                'title': Path(self.file_path).name,
                'error': str(e)
            }
    
    def zoom_document(self, zoom_level: int) -> Dict[str, Any]:
        """Set document zoom level"""
        try:
            if not self.controller:
                return {'success': False, 'error': 'No controller available'}
            
            # Get view settings
            view_settings = self.controller.getViewSettings()
            if hasattr(view_settings, 'ZoomValue'):
                view_settings.ZoomValue = zoom_level
                logger.info(f"Set zoom to {zoom_level}% for document: {self.file_path}")
                return {'success': True, 'zoom': zoom_level}
            else:
                return {'success': False, 'error': 'Zoom not supported for this document type'}
        except Exception as e:
            logger.error(f"Failed to set zoom: {e}")
            return {'success': False, 'error': str(e)}
    
    def scroll_to_page(self, page_num: int) -> Dict[str, Any]:
        """Scroll to specific page"""
        try:
            if not self.controller:
                return {'success': False, 'error': 'No controller available'}
            
            # Different approaches for different document types
            if hasattr(self.controller, 'getViewCursor'):
                # Text documents
                view_cursor = self.controller.getViewCursor()
                view_cursor.jumpToPage(page_num)
                return {'success': True, 'page': page_num}
            elif hasattr(self.controller, 'setCurrentPage'):
                # Presentation/Drawing documents
                self.controller.setCurrentPage(self.component.getDrawPages().getByIndex(page_num - 1))
                return {'success': True, 'page': page_num}
            else:
                return {'success': False, 'error': 'Page navigation not supported for this document type'}
        except Exception as e:
            logger.error(f"Failed to scroll to page: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_current_page(self) -> int:
        """Get current page number"""
        try:
            if hasattr(self.controller, 'getViewCursor'):
                cursor = self.controller.getViewCursor()
                return cursor.getPage()
            elif hasattr(self.controller, 'getCurrentPage'):
                current_page = self.controller.getCurrentPage()
                # Find page index
                pages = self.component.getDrawPages()
                for i in range(pages.getCount()):
                    if pages.getByIndex(i) == current_page:
                        return i + 1
            return 1
        except:
            return 1
    
    def close(self):
        """Close the document"""
        try:
            if hasattr(self.component, 'close'):
                self.component.close(True)
            else:
                self.component.dispose()
            logger.info(f"Document closed: {self.file_path}")
        except Exception as e:
            logger.error(f"Error closing document: {e}")


class DocumentLoader:
    """Handles document loading via UNO"""
    
    def __init__(self, desktop):
        self.desktop = desktop
        self.loaded_documents = OrderedDict()  # Track loaded documents
        
    def load_document(self, file_path: str, hidden: bool = False) -> LoadedDocument:
        """Load a document and return wrapper object"""
        if not uno:
            raise RuntimeError("UNO modules not available")
            
        from com.sun.star.lang import IllegalArgumentException
        from com.sun.star.io import IOException
        
        # Validate file path
        abs_path = Path(file_path).resolve()
        if not abs_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Convert to file URL
        file_url = uno.systemPathToFileUrl(str(abs_path))
        
        # Create load properties
        load_props = []
        load_props.append(create_property("Hidden", hidden))
        load_props.append(create_property("ReadOnly", False))
        load_props.append(create_property("AsTemplate", False))
        
        # Add format detection
        load_props.append(create_property("FilterName", ""))  # Auto-detect
        
        try:
            logger.info(f"Loading document: {file_url}")
            
            # Load the document
            document = self.desktop.loadComponentFromURL(
                file_url,
                "_blank",  # Target frame
                0,         # Search flags
                load_props
            )
            
            if not document:
                raise RuntimeError("Failed to load document")
            
            # Create wrapper
            loaded_doc = LoadedDocument(document, str(abs_path))
            self.loaded_documents[loaded_doc.doc_id] = loaded_doc
            
            logger.info(f"Document loaded successfully: {loaded_doc.doc_id}")
            return loaded_doc
            
        except IllegalArgumentException as e:
            raise ValueError(f"Invalid document format: {e}")
        except IOException as e:
            raise IOError(f"IO error loading document: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading document: {e}")
            raise


class UNOSocketBridge:
    """LibreOffice UNO socket integration with document loading"""
    
    def __init__(self, port=None):
        self.port = port
        self.process = None
        self.is_running = False
        self.connection = None
        self.document_loader = None
        self.loaded_documents = {}  # doc_id -> LoadedDocument
        
        if not self.port:
            self._find_free_port()
        logger.info(f"UNO Bridge initialized with port {self.port}")
    
    def _find_free_port(self):
        """Find free port for UNO"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            self.port = s.getsockname()[1]
        logger.debug(f"UNO port allocated: {self.port}")
    
    def _is_port_in_use(self, port):
        """Check if port is in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except OSError:
                return True
    
    def _check_libreoffice_path(self):
        """Check if LibreOffice executable exists"""
        libreoffice_path = CFG.LIBREOFFICE_PATH
        if not Path(libreoffice_path).exists():
            # Try common alternative paths
            alternatives = [
                "libreoffice",
                "soffice",
                "/usr/bin/soffice",
                "/opt/libreoffice/program/soffice"
            ]
            
            for alt in alternatives:
                try:
                    result = subprocess.run([alt, "--version"], 
                                          capture_output=True, 
                                          timeout=5)
                    if result.returncode == 0:
                        logger.info(f"Found LibreOffice at: {alt}")
                        return alt
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            logger.error(f"LibreOffice not found at {libreoffice_path}")
            return None
        
        return libreoffice_path
    
    def start_libreoffice_server(self):
        """Start LibreOffice with UNO socket"""
        if self.is_running and self.process and self.process.poll() is None:
            logger.info("LibreOffice server already running")
            return True
        
        # Kill any existing LibreOffice processes
        try:
            subprocess.run(['pkill', '-f', 'soffice'], capture_output=True)
            time.sleep(1)  # Give it time to clean up
        except Exception as e:
            logger.debug(f"Error killing existing LibreOffice processes: {e}")
        
        libreoffice_path = self._check_libreoffice_path()
        if not libreoffice_path:
            logger.error("LibreOffice executable not found")
            return False
        
        # Try multiple times with different ports if needed
        for attempt in range(CFG.UNO_RETRY_COUNT):
            try:
                # Check if port is free
                if self._is_port_in_use(self.port):
                    logger.warning(f"Port {self.port} is in use, trying another")
                    self._find_free_port()
                
                cmd = [
                    libreoffice_path,
                    '--headless',
                    '--invisible',
                    '--nologo',
                    '--nolockcheck',
                    '--accept=socket,host=localhost,port=' + str(self.port) + ';urp;'
                ]
                
                logger.info(f"Starting LibreOffice (attempt {attempt + 1}): {' '.join(cmd)}")
                
                # Set environment to avoid Java dependency issues
                env = os.environ.copy()
                env['SAL_USE_VCLPLUGIN'] = 'gen'  # Use generic VCL plugin
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    env=env
                )
                
                # Wait and check if process started successfully
                time.sleep(CFG.UNO_RETRY_DELAY)
                
                if self.process.poll() is None:
                    # Process is running, test connection
                    if self._test_uno_connection():
                        self.is_running = True
                        logger.info(f"LibreOffice server started successfully on port {self.port}")
                        return True
                    else:
                        logger.warning("LibreOffice started but UNO connection failed")
                        self._cleanup_process()
                else:
                    # Process died
                    stdout, stderr = self.process.communicate()
                    stderr_text = stderr.decode()
                    logger.error(f"LibreOffice process died: {stderr_text}")
                    
                    # Check if it's just a javaldx warning (non-fatal)
                    if "failed to launch javaldx" in stderr_text.lower() and not stdout:
                        logger.warning("javaldx warning detected - this is usually non-fatal, continuing...")
                        # Give it more time and check connection
                        time.sleep(3)
                        if self._test_uno_connection():
                            self.is_running = True
                            logger.info(f"LibreOffice server started successfully (with javaldx warning) on port {self.port}")
                            return True
                    
                    self._cleanup_process()
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                self._cleanup_process()
                
                if attempt < CFG.UNO_RETRY_COUNT - 1:
                    logger.info(f"Retrying in {CFG.UNO_RETRY_DELAY} seconds...")
                    time.sleep(CFG.UNO_RETRY_DELAY)
                    self._find_free_port()  # Try different port
        
        logger.error("Failed to start LibreOffice server after all attempts")
        return False
    
    def _test_uno_connection(self):
        """Test UNO connection"""
        try:
            import uno
            from com.sun.star.connection import NoConnectException
            
            # Create UNO context
            local_context = uno.getComponentContext()
            resolver = local_context.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", local_context
            )
            
            # Try to connect
            connect_string = f"uno:socket,host=localhost,port={self.port};urp;StarOffice.ComponentContext"
            
            context = resolver.resolve(connect_string)
            logger.debug("UNO connection test successful")
            return True
            
        except ImportError:
            logger.warning("Python UNO module not available")
            return False
        except NoConnectException:
            logger.debug("UNO connection failed - service not ready")
            return False
        except Exception as e:
            logger.debug(f"UNO connection test failed: {e}")
            return False
    
    def _cleanup_process(self):
        """Clean up LibreOffice process"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except Exception as e:
                logger.error(f"Error cleaning up process: {e}")
            finally:
                self.process = None
                self.is_running = False
    
    def ensure_connection(self) -> bool:
        """Ensure UNO connection is established"""
        if not self.connection or not self.connection._connected:
            # Start LibreOffice if needed
            if not self.is_running:
                if not self.start_libreoffice_server():
                    return False
                    
            # Establish UNO connection
            self.connection = UNOConnection(port=self.port)
            if not self.connection.connect():
                logger.error("Failed to establish UNO connection")
                return False
                
            # Initialize document loader
            self.document_loader = DocumentLoader(self.connection.desktop)
            logger.info("UNO connection and document loader initialized")
            
        return True
    
    @with_uno_error_handling
    def load_document(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load a document via UNO and return document info with window handle"""
        try:
            # Ensure connection
            if not self.ensure_connection():
                return {
                    'success': False,
                    'error': 'Failed to establish UNO connection'
                }
            
            # Load document
            logger.info(f"Loading document via UNO: {file_path}")
            loaded_doc = self.document_loader.load_document(
                file_path,
                hidden=options.get('hidden', False) if options else False
            )
            
            # Get window handle for Linux
            window_info = None
            if platform.system() == "Linux":
                window_info = loaded_doc.get_window_handle_linux()
                
            if not window_info:
                logger.warning("Failed to get window handle")
            
            # Get document info
            doc_info = loaded_doc.get_document_info()
            
            # Store reference
            self.loaded_documents[loaded_doc.doc_id] = loaded_doc
            
            result = {
                'success': True,
                'doc_id': loaded_doc.doc_id,
                'window': window_info,
                'file_path': file_path,
                'info': doc_info
            }
            
            logger.info(f"Document loaded successfully: {result}")
            return result
            
        except FileNotFoundError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Document loading failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def embed_document(self, file_path, container_id):
        """Embed document in container using real UNO implementation"""
        logger.info(f"Embedding document: {file_path} in container: {container_id}")
        
        # Validate file path
        if not Path(file_path).exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in CFG.ALLOWED_EXTENSIONS:
            error_msg = f"Unsupported file type: {file_ext}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Load document via UNO
        result = self.load_document(file_path, {'hidden': False})
        
        if result['success']:
            # Add container info
            result['container'] = container_id
            result['mode'] = 'uno_document_loaded'
            
            # TODO: Implement actual window embedding using XEmbed protocol
            # For now, we have the window ID which can be used for embedding
            if result.get('window'):
                result['embedding_ready'] = True
                result['message'] = f"Document loaded with X11 window ID: {result['window']['handle']}"
            else:
                result['embedding_ready'] = False
                result['message'] = "Document loaded but window handle not available"
                
            logger.info(f"Document embed result: {result}")
            return result
            
        else:
            return {"error": result.get('error', 'Failed to load document')}
    
    def open_document_external(self, file_path):
        """Open document in external LibreOffice window"""
        try:
            libreoffice_path = self._check_libreoffice_path()
            if not libreoffice_path:
                return {"error": "LibreOffice not found"}
            
            cmd = [libreoffice_path, str(file_path)]
            process = subprocess.Popen(cmd)
            
            logger.info(f"Opened document externally: {file_path}")
            return {
                "success": True,
                "mode": "external",
                "pid": process.pid
            }
            
        except Exception as e:
            error_msg = f"Error opening document externally: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def get_status(self):
        """Get UNO bridge status"""
        return {
            "running": self.is_running,
            "port": self.port,
            "process_alive": self.process is not None and self.process.poll() is None,
            "libreoffice_path": CFG.LIBREOFFICE_PATH
        }
    
    @with_uno_error_handling
    def zoom_document(self, doc_id: str, zoom_level: int) -> Dict[str, Any]:
        """Set zoom level for a loaded document"""
        if doc_id not in self.loaded_documents:
            return {'success': False, 'error': 'Document not found'}
        
        try:
            doc = self.loaded_documents[doc_id]
            return doc.zoom_document(zoom_level)
        except Exception as e:
            logger.error(f"Zoom operation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    @with_uno_error_handling
    def scroll_to_page(self, doc_id: str, page_num: int) -> Dict[str, Any]:
        """Scroll document to specific page"""
        if doc_id not in self.loaded_documents:
            return {'success': False, 'error': 'Document not found'}
        
        try:
            doc = self.loaded_documents[doc_id]
            return doc.scroll_to_page(page_num)
        except Exception as e:
            logger.error(f"Scroll operation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    @with_uno_error_handling
    def get_document_info(self, doc_id: str) -> Dict[str, Any]:
        """Get detailed document information"""
        if doc_id not in self.loaded_documents:
            return {'success': False, 'error': 'Document not found'}
        
        try:
            doc = self.loaded_documents[doc_id]
            info = doc.get_document_info()
            info['current_page'] = doc.get_current_page()
            return {'success': True, 'info': info}
        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_document(self, doc_id: str) -> Dict[str, Any]:
        """Close a specific document"""
        if doc_id not in self.loaded_documents:
            return {'success': False, 'error': 'Document not found'}
        
        try:
            doc = self.loaded_documents[doc_id]
            doc.close()
            del self.loaded_documents[doc_id]
            logger.info(f"Document closed and removed: {doc_id}")
            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to close document: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_all_documents(self) -> Dict[str, Any]:
        """Close all loaded documents"""
        errors = []
        closed_count = 0
        
        for doc_id in list(self.loaded_documents.keys()):
            result = self.close_document(doc_id)
            if result['success']:
                closed_count += 1
            else:
                errors.append(f"{doc_id}: {result['error']}")
        
        return {
            'success': len(errors) == 0,
            'closed': closed_count,
            'errors': errors
        }
    
    def shutdown(self):
        """Shutdown LibreOffice server"""
        logger.info("Shutting down UNO bridge...")
        
        # Close all documents first
        if self.loaded_documents:
            logger.info(f"Closing {len(self.loaded_documents)} open documents...")
            self.close_all_documents()
        
        if self.process:
            try:
                # Try graceful shutdown first
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                    logger.info("LibreOffice shut down gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    logger.warning("Graceful shutdown failed, force killing...")
                    self.process.kill()
                    self.process.wait()
                    logger.info("LibreOffice force killed")
                    
            except Exception as e:
                logger.error(f"Error during LibreOffice shutdown: {e}")
            finally:
                self.process = None
                self.is_running = False
        
        logger.info("UNO bridge shutdown complete")
    
    def restart(self):
        """Restart LibreOffice server"""
        logger.info("Restarting LibreOffice server...")
        self.shutdown()
        time.sleep(1)
        return self.start_libreoffice_server()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on UNO connection"""
        health = {
            'libreoffice_running': False,
            'uno_connected': False,
            'documents_loaded': len(self.loaded_documents),
            'errors': []
        }
        
        # Check LibreOffice process
        if self.process and self.process.poll() is None:
            health['libreoffice_running'] = True
        else:
            health['errors'].append('LibreOffice process not running')
        
        # Check UNO connection
        if self.connection and self.connection._connected:
            try:
                # Try simple operation to verify connection
                if self.connection.desktop:
                    components = self.connection.desktop.getComponents()
                    health['uno_connected'] = True
            except Exception as e:
                health['errors'].append(f'UNO connection error: {str(e)}')
                health['uno_connected'] = False
        else:
            health['errors'].append('No UNO connection established')
        
        health['healthy'] = health['libreoffice_running'] and health['uno_connected']
        return health
    
    def recover_connection(self) -> bool:
        """Attempt to recover lost connection"""
        logger.info("Attempting connection recovery...")
        
        # First check if LibreOffice is still running
        if not self.is_running or not self.process or self.process.poll() is not None:
            logger.info("LibreOffice not running, restarting...")
            if not self.start_libreoffice_server():
                logger.error("Failed to restart LibreOffice")
                return False
        
        # Try to re-establish UNO connection
        try:
            self.connection = UNOConnection(port=self.port)
            if self.connection.connect():
                self.document_loader = DocumentLoader(self.connection.desktop)
                logger.info("Connection recovered successfully")
                return True
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
        
        return False