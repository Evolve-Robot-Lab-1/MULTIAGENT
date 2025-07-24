#!/usr/bin/env python3
"""
Unit tests for UNO Bridge functionality
Tests connection management, document loading, and error recovery
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uno_bridge import (
    UNOConnection, LoadedDocument, DocumentLoader, 
    UNOSocketBridge, create_property, create_properties
)


class TestUNOHelpers(unittest.TestCase):
    """Test helper functions"""
    
    @patch('uno_bridge.uno')
    def test_create_property(self, mock_uno):
        """Test property creation"""
        # Mock PropertyValue
        mock_prop = Mock()
        mock_uno.PropertyValue = Mock(return_value=mock_prop)
        
        # Import after patching
        from uno_bridge import create_property
        
        prop = create_property("TestName", "TestValue")
        
        # Verify property was created correctly
        self.assertEqual(prop.Name, "TestName")
        self.assertEqual(prop.Value, "TestValue")
    
    def test_create_properties(self):
        """Test multiple property creation"""
        with patch('uno_bridge.create_property') as mock_create:
            mock_create.side_effect = lambda n, v: Mock(Name=n, Value=v)
            
            props = create_properties(Hidden=True, ReadOnly=False, FilterName="")
            
            self.assertEqual(len(props), 3)
            self.assertEqual(mock_create.call_count, 3)


class TestUNOConnection(unittest.TestCase):
    """Test UNO connection management"""
    
    @patch('uno_bridge.uno')
    def test_connection_init(self, mock_uno):
        """Test connection initialization"""
        conn = UNOConnection(host='testhost', port=9999)
        
        self.assertEqual(conn.host, 'testhost')
        self.assertEqual(conn.port, 9999)
        self.assertFalse(conn._connected)
        self.assertIsNone(conn.desktop)
    
    @patch('uno_bridge.uno')
    def test_successful_connection(self, mock_uno):
        """Test successful UNO connection"""
        # Setup mocks
        mock_context = Mock()
        mock_resolver = Mock()
        mock_desktop = Mock()
        
        mock_uno.getComponentContext.return_value = mock_context
        mock_context.ServiceManager.createInstanceWithContext.return_value = mock_resolver
        mock_resolver.resolve.return_value = mock_context
        
        conn = UNOConnection()
        result = conn.connect(max_retries=1)
        
        self.assertTrue(result)
        self.assertTrue(conn._connected)
        
        # Verify connection string
        mock_resolver.resolve.assert_called_once()
        call_args = mock_resolver.resolve.call_args[0][0]
        self.assertIn("uno:socket,host=localhost,port=2002", call_args)
    
    @patch('uno_bridge.uno')
    def test_connection_retry_logic(self, mock_uno):
        """Test connection retry with exponential backoff"""
        # Mock NoConnectException
        class NoConnectException(Exception):
            pass
        
        mock_uno.getComponentContext.return_value = Mock()
        
        # Simulate connection failure then success
        mock_resolver = Mock()
        mock_resolver.resolve.side_effect = [
            NoConnectException("Connection failed"),
            Mock()  # Success on second attempt
        ]
        
        with patch('uno_bridge.time.sleep') as mock_sleep:
            conn = UNOConnection()
            
            # Patch the exception type
            with patch('uno_bridge.NoConnectException', NoConnectException):
                conn.local_context = Mock()
                conn.local_context.ServiceManager.createInstanceWithContext.return_value = mock_resolver
                
                # Should succeed on retry
                result = conn.connect(max_retries=2)
                
                # Verify backoff was applied
                mock_sleep.assert_called_once_with(1)  # 2^0 = 1


class TestLoadedDocument(unittest.TestCase):
    """Test loaded document wrapper"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.mock_component = Mock()
        self.mock_controller = Mock()
        self.mock_frame = Mock()
        self.mock_window = Mock()
        
        # Setup mock chain
        self.mock_component.getCurrentController.return_value = self.mock_controller
        self.mock_controller.getFrame.return_value = self.mock_frame
        self.mock_frame.getContainerWindow.return_value = self.mock_window
    
    def test_document_init(self):
        """Test document initialization"""
        with patch.object(LoadedDocument, '_extract_window_info'):
            doc = LoadedDocument(self.mock_component, "/test/path.docx")
            
            self.assertEqual(doc.component, self.mock_component)
            self.assertEqual(doc.file_path, "/test/path.docx")
            self.assertIsNotNone(doc.doc_id)
    
    def test_extract_window_info_success(self):
        """Test successful window info extraction"""
        doc = LoadedDocument(self.mock_component, "/test/path.docx")
        
        self.assertEqual(doc.controller, self.mock_controller)
        self.assertEqual(doc.frame, self.mock_frame)
        self.assertEqual(doc.window, self.mock_window)
    
    def test_extract_window_info_no_controller(self):
        """Test window extraction with no controller"""
        self.mock_component.getCurrentController.return_value = None
        
        with self.assertRaises(RuntimeError) as cm:
            LoadedDocument(self.mock_component, "/test/path.docx")
        
        self.assertIn("No controller available", str(cm.exception))
    
    @patch('uno_bridge.platform.system')
    @patch('uno_bridge.subprocess.run')
    def test_get_window_handle_linux(self, mock_run, mock_platform):
        """Test Linux X11 window handle extraction"""
        mock_platform.return_value = "Linux"
        
        # Mock xwininfo output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Window id: 12345 (0x3039)"
        mock_run.return_value = mock_result
        
        # Setup frame title
        self.mock_frame.getTitle.return_value = "Test Document"
        
        doc = LoadedDocument(self.mock_component, "/test/path.docx")
        handle = doc.get_window_handle_linux()
        
        self.assertIsNotNone(handle)
        self.assertEqual(handle['type'], 'x11')
        self.assertEqual(handle['handle'], 12345)
    
    def test_get_document_info(self):
        """Test document info retrieval"""
        # Mock document properties
        mock_props = Mock()
        mock_props.Title = "Test Document"
        mock_props.Author = "Test Author"
        mock_props.Subject = "Test Subject"
        mock_props.ModificationDate = None
        mock_props.CreationDate = None
        
        self.mock_component.getDocumentProperties.return_value = mock_props
        
        doc = LoadedDocument(self.mock_component, "/test/path.docx")
        info = doc.get_document_info()
        
        self.assertEqual(info['title'], "Test Document")
        self.assertEqual(info['author'], "Test Author")
        self.assertEqual(info['subject'], "Test Subject")
        self.assertEqual(info['doc_id'], doc.doc_id)
    
    def test_zoom_document(self):
        """Test document zoom functionality"""
        mock_view_settings = Mock()
        self.mock_controller.getViewSettings.return_value = mock_view_settings
        
        doc = LoadedDocument(self.mock_component, "/test/path.docx")
        result = doc.zoom_document(150)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['zoom'], 150)
        self.assertEqual(mock_view_settings.ZoomValue, 150)
    
    def test_close_document(self):
        """Test document closing"""
        self.mock_component.close = Mock()
        
        doc = LoadedDocument(self.mock_component, "/test/path.docx")
        doc.close()
        
        self.mock_component.close.assert_called_once_with(True)


class TestDocumentLoader(unittest.TestCase):
    """Test document loader functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.mock_desktop = Mock()
        self.loader = DocumentLoader(self.mock_desktop)
    
    @patch('uno_bridge.uno')
    @patch('uno_bridge.Path')
    def test_load_document_success(self, mock_path_class, mock_uno):
        """Test successful document loading"""
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tf:
            test_file = tf.name
        
        try:
            # Setup mocks
            mock_path = Mock()
            mock_path.resolve.return_value = mock_path
            mock_path.exists.return_value = True
            mock_path_class.return_value = mock_path
            
            mock_uno.systemPathToFileUrl.return_value = f"file://{test_file}"
            
            # Mock document
            mock_document = Mock()
            self.mock_desktop.loadComponentFromURL.return_value = mock_document
            
            # Mock LoadedDocument
            with patch('uno_bridge.LoadedDocument') as mock_loaded_doc_class:
                mock_loaded_doc = Mock()
                mock_loaded_doc.doc_id = "test-id"
                mock_loaded_doc_class.return_value = mock_loaded_doc
                
                result = self.loader.load_document(test_file)
                
                self.assertEqual(result, mock_loaded_doc)
                self.assertIn("test-id", self.loader.loaded_documents)
                
                # Verify load properties
                self.mock_desktop.loadComponentFromURL.assert_called_once()
                call_args = self.mock_desktop.loadComponentFromURL.call_args
                self.assertEqual(call_args[0][1], "_blank")  # Target frame
                
        finally:
            Path(test_file).unlink(missing_ok=True)
    
    def test_load_document_file_not_found(self):
        """Test loading non-existent document"""
        with self.assertRaises(FileNotFoundError):
            self.loader.load_document("/non/existent/file.docx")
    
    @patch('uno_bridge.uno')
    @patch('uno_bridge.Path')
    def test_load_document_uno_error(self, mock_path_class, mock_uno):
        """Test handling UNO loading errors"""
        # Mock path exists
        mock_path = Mock()
        mock_path.resolve.return_value = mock_path
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path
        
        # Mock loading failure
        self.mock_desktop.loadComponentFromURL.return_value = None
        
        with self.assertRaises(RuntimeError) as cm:
            self.loader.load_document("/test/file.docx")
        
        self.assertIn("Failed to load document", str(cm.exception))


class TestUNOSocketBridge(unittest.TestCase):
    """Test UNO socket bridge"""
    
    def test_init_with_port(self):
        """Test initialization with specific port"""
        bridge = UNOSocketBridge(port=8888)
        self.assertEqual(bridge.port, 8888)
        self.assertFalse(bridge.is_running)
        self.assertEqual(len(bridge.loaded_documents), 0)
    
    @patch('uno_bridge.socket.socket')
    def test_find_free_port(self, mock_socket_class):
        """Test automatic port allocation"""
        mock_socket = Mock()
        mock_socket.getsockname.return_value = ('', 12345)
        mock_socket_class.return_value.__enter__.return_value = mock_socket
        
        bridge = UNOSocketBridge()
        self.assertEqual(bridge.port, 12345)
    
    @patch('uno_bridge.subprocess.Popen')
    @patch.object(UNOSocketBridge, '_test_uno_connection')
    @patch.object(UNOSocketBridge, '_check_libreoffice_path')
    def test_start_libreoffice_server(self, mock_check_path, mock_test_conn, mock_popen):
        """Test LibreOffice server startup"""
        mock_check_path.return_value = "/usr/bin/libreoffice"
        mock_test_conn.return_value = True
        
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running
        mock_popen.return_value = mock_process
        
        bridge = UNOSocketBridge(port=7777)
        result = bridge.start_libreoffice_server()
        
        self.assertTrue(result)
        self.assertTrue(bridge.is_running)
        self.assertEqual(bridge.process, mock_process)
        
        # Verify command
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        self.assertIn('--accept=socket,host=localhost,port=7777', ' '.join(cmd))
    
    def test_health_check(self):
        """Test health check functionality"""
        bridge = UNOSocketBridge()
        
        # Initial state - not healthy
        health = bridge.health_check()
        self.assertFalse(health['healthy'])
        self.assertFalse(health['libreoffice_running'])
        self.assertFalse(health['uno_connected'])
        
        # Mock running state
        bridge.process = Mock()
        bridge.process.poll.return_value = None
        bridge.connection = Mock()
        bridge.connection._connected = True
        bridge.connection.desktop = Mock()
        bridge.connection.desktop.getComponents.return_value = []
        
        health = bridge.health_check()
        self.assertTrue(health['healthy'])
        self.assertTrue(health['libreoffice_running'])
        self.assertTrue(health['uno_connected'])
    
    @patch.object(UNOSocketBridge, 'ensure_connection')
    def test_error_recovery_decorator(self, mock_ensure):
        """Test automatic error recovery"""
        bridge = UNOSocketBridge()
        
        # Add a document to test with
        mock_doc = Mock()
        mock_doc.zoom_document.side_effect = [
            Exception("Connection lost"),  # First attempt fails
            {'success': True, 'zoom': 150}  # Second attempt succeeds
        ]
        bridge.loaded_documents['test-id'] = mock_doc
        
        # Mock recovery
        bridge.recover_connection = Mock(return_value=True)
        
        # Should recover and retry
        result = bridge.zoom_document('test-id', 150)
        
        # Verify recovery was attempted
        bridge.recover_connection.assert_called_once()


if __name__ == '__main__':
    unittest.main()