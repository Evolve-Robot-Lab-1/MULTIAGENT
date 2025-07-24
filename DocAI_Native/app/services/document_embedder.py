"""
Document Embedder Service - Phase 2.5 Implementation
Handles LibreOffice document embedding for native viewing
"""

import platform
import subprocess
import logging
import time
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DocumentEmbedder(ABC):
    """Abstract base class for document embedding"""
    
    @abstractmethod
    def embed_document(self, parent_window, document_path: str) -> Dict[str, Any]:
        """Embed document in parent window"""
        pass
    
    @abstractmethod
    def can_embed(self) -> bool:
        """Check if embedding is supported on this platform"""
        pass


class LinuxDocumentEmbedder(DocumentEmbedder):
    """Linux-specific document embedding using X11"""
    
    def __init__(self):
        self.embedded_processes = {}
        
    def can_embed(self) -> bool:
        """Check if X11 embedding is available"""
        try:
            # Check if X11 is available
            display = os.environ.get('DISPLAY')
            if not display:
                logger.warning("No DISPLAY environment variable set")
                return False
                
            # Check if xwininfo is available
            result = subprocess.run(['which', 'xwininfo'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("xwininfo not found - X11 embedding may not work")
                return False
                
            # Check if LibreOffice is installed
            result = subprocess.run(['which', 'soffice'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("LibreOffice (soffice) not found")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking Linux embedding capability: {e}")
            return False
    
    def get_window_id(self, parent_window) -> Optional[str]:
        """Get X11 window ID from PyWebView window"""
        try:
            # PyWebView doesn't directly expose window ID, so we need to find it
            # This is a simplified approach - may need platform-specific handling
            
            # Get window title to search for
            title = parent_window.title
            
            # Use xwininfo to find window by name
            cmd = ['xwininfo', '-name', title, '-int']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse window ID from output
                for line in result.stdout.split('\n'):
                    if 'Window id:' in line:
                        # Extract the ID (in decimal)
                        parts = line.split()
                        if len(parts) >= 4:
                            return parts[3]
            
            logger.warning(f"Could not find window ID for '{title}'")
            return None
            
        except Exception as e:
            logger.error(f"Error getting window ID: {e}")
            return None
    
    def embed_document(self, parent_window, document_path: str) -> Dict[str, Any]:
        """Embed LibreOffice document viewer in parent window"""
        try:
            # Verify file exists
            if not Path(document_path).exists():
                return {
                    'success': False,
                    'error': f'Document not found: {document_path}'
                }
            
            # Get parent window ID
            window_id = self.get_window_id(parent_window)
            if not window_id:
                logger.warning("Could not get window ID, opening in separate window")
                # Fallback to separate window
                return self._open_separate_window(document_path)
            
            # Build LibreOffice command for embedding
            cmd = [
                'soffice',
                '--nologo',
                '--norestore',
                '--view',
                '--nolockcheck',
                f'--display={os.environ.get("DISPLAY", ":0")}',
                # Note: Direct X11 embedding is complex with LibreOffice
                # For now, we'll open in a separate window positioned near parent
                document_path
            ]
            
            logger.info(f"Starting LibreOffice with command: {' '.join(cmd)}")
            
            # Start LibreOffice process
            process = subprocess.Popen(cmd)
            
            # Store process reference
            self.embedded_processes[document_path] = process
            
            # Give it time to start
            time.sleep(1)
            
            # Check if process is still running
            if process.poll() is None:
                return {
                    'success': True,
                    'pid': process.pid,
                    'window_id': window_id,
                    'mode': 'separate',  # For now, using separate window
                    'message': 'Document opened in LibreOffice viewer'
                }
            else:
                return {
                    'success': False,
                    'error': 'LibreOffice process terminated unexpectedly'
                }
                
        except Exception as e:
            logger.error(f"Error embedding document on Linux: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _open_separate_window(self, document_path: str) -> Dict[str, Any]:
        """Fallback: Open document in separate LibreOffice window"""
        try:
            cmd = [
                'soffice',
                '--nologo',
                '--view',
                '--norestore',
                document_path
            ]
            
            process = subprocess.Popen(cmd)
            self.embedded_processes[document_path] = process
            
            return {
                'success': True,
                'pid': process.pid,
                'mode': 'separate',
                'message': 'Document opened in separate LibreOffice window'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to open document: {str(e)}'
            }


class WindowsDocumentEmbedder(DocumentEmbedder):
    """Windows-specific document embedding"""
    
    def __init__(self):
        self.embedded_processes = {}
        
    def can_embed(self) -> bool:
        """Check if Windows embedding is available"""
        try:
            # Check if LibreOffice is installed
            import winreg
            
            # Try to find LibreOffice in registry
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\LibreOffice\LibreOffice")
                winreg.CloseKey(key)
                return True
            except:
                pass
            
            # Try to find soffice.exe in common locations
            common_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
            ]
            
            for path in common_paths:
                if Path(path).exists():
                    return True
                    
            logger.warning("LibreOffice not found on Windows")
            return False
            
        except Exception as e:
            logger.error(f"Error checking Windows embedding capability: {e}")
            return False
    
    def embed_document(self, parent_window, document_path: str) -> Dict[str, Any]:
        """Embed document viewer on Windows"""
        try:
            # For now, use separate window approach
            # True embedding would require Win32 API integration
            
            # Find soffice.exe
            soffice_path = self._find_soffice_exe()
            if not soffice_path:
                return {
                    'success': False,
                    'error': 'LibreOffice not found on system'
                }
            
            cmd = [
                str(soffice_path),
                '--nologo',
                '--view',
                '--norestore',
                document_path
            ]
            
            process = subprocess.Popen(cmd)
            self.embedded_processes[document_path] = process
            
            return {
                'success': True,
                'pid': process.pid,
                'mode': 'separate',
                'message': 'Document opened in LibreOffice viewer'
            }
            
        except Exception as e:
            logger.error(f"Error embedding document on Windows: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_soffice_exe(self) -> Optional[Path]:
        """Find LibreOffice executable on Windows"""
        common_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        
        for path in common_paths:
            path_obj = Path(path)
            if path_obj.exists():
                return path_obj
                
        # Try to find via PATH
        try:
            result = subprocess.run(['where', 'soffice.exe'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except:
            pass
            
        return None


class MacOSDocumentEmbedder(DocumentEmbedder):
    """macOS-specific document embedding"""
    
    def __init__(self):
        self.embedded_processes = {}
        
    def can_embed(self) -> bool:
        """Check if macOS embedding is available"""
        try:
            # Check if LibreOffice is installed
            app_path = "/Applications/LibreOffice.app"
            if Path(app_path).exists():
                return True
                
            # Check via mdfind
            result = subprocess.run(['mdfind', 'kMDItemCFBundleIdentifier=org.libreoffice.script'],
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking macOS embedding capability: {e}")
            return False
    
    def embed_document(self, parent_window, document_path: str) -> Dict[str, Any]:
        """Embed document viewer on macOS"""
        try:
            # Use 'open' command with LibreOffice
            cmd = [
                'open',
                '-a', 'LibreOffice',
                '--args',
                '--view',
                '--nologo',
                document_path
            ]
            
            process = subprocess.Popen(cmd)
            
            return {
                'success': True,
                'pid': process.pid,
                'mode': 'separate',
                'message': 'Document opened in LibreOffice'
            }
            
        except Exception as e:
            logger.error(f"Error embedding document on macOS: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class FallbackDocumentEmbedder(DocumentEmbedder):
    """Fallback embedder for unsupported platforms"""
    
    def can_embed(self) -> bool:
        """Always returns True as last resort"""
        return True
    
    def embed_document(self, parent_window, document_path: str) -> Dict[str, Any]:
        """Try to open document with system default"""
        try:
            system = platform.system()
            
            if system == 'Linux':
                cmd = ['xdg-open', document_path]
            elif system == 'Windows':
                cmd = ['start', '', document_path]
            elif system == 'Darwin':
                cmd = ['open', document_path]
            else:
                return {
                    'success': False,
                    'error': f'Unsupported platform: {system}'
                }
            
            subprocess.run(cmd, shell=(system == 'Windows'))
            
            return {
                'success': True,
                'mode': 'system',
                'message': 'Document opened with system default application'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def create_document_embedder() -> DocumentEmbedder:
    """Factory function to create appropriate embedder for current platform"""
    system = platform.system()
    
    logger.info(f"Creating document embedder for platform: {system}")
    
    if system == 'Linux':
        embedder = LinuxDocumentEmbedder()
    elif system == 'Windows':
        embedder = WindowsDocumentEmbedder()
    elif system == 'Darwin':
        embedder = MacOSDocumentEmbedder()
    else:
        embedder = FallbackDocumentEmbedder()
    
    # Check if embedder can work on this system
    if not embedder.can_embed():
        logger.warning(f"{system} embedder cannot embed, using fallback")
        embedder = FallbackDocumentEmbedder()
    
    return embedder


# Global embedder instance
_embedder = None

def get_document_embedder() -> DocumentEmbedder:
    """Get or create the global document embedder instance"""
    global _embedder
    if _embedder is None:
        _embedder = create_document_embedder()
    return _embedder