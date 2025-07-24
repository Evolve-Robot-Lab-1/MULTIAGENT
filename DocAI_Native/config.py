"""
Configuration module for DocAI Native
Centralized settings for ports, paths, and application configuration
"""

import os
import platform
from pathlib import Path

class Config:
    """Application configuration"""
    
    # App Info
    APP_NAME = "Durga AI Native"
    VERSION = "0.1.0"
    
    # Base directories
    BASE_DIR = Path(__file__).parent
    FRONTEND_DIR = BASE_DIR / "frontend"
    
    # User directories
    DOCUMENTS_DIR = Path.home() / "Documents" / "DurgaAI"
    CACHE_DIR = Path.home() / ".cache" / "DurgaAI"
    CONFIG_DIR = Path.home() / ".config" / "DurgaAI"
    
    # Ensure directories exist
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        for dir_path in [cls.DOCUMENTS_DIR, cls.CACHE_DIR, cls.CONFIG_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # Ports (0 = random assignment)
    FLASK_PORT = 8090  # Fixed port for consistency with frontend
    UNO_PORT = 0
    
    # LibreOffice configuration
    @property
    def LIBREOFFICE_PATH(self):
        """Get LibreOffice path based on platform"""
        system = platform.system()
        if system == "Linux":
            return "/usr/bin/libreoffice"
        elif system == "Windows":
            return "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
        elif system == "Darwin":  # macOS
            return "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        else:
            return "libreoffice"  # Fallback
    
    # Auto-update configuration
    UPDATE_URL = "https://api.github.com/repos/yourusername/docai-native/releases/latest"
    AUTO_UPDATE = True
    
    # Development settings
    DEBUG = os.getenv("DOCAI_DEBUG", "False").lower() == "true"
    HOT_RELOAD = DEBUG
    
    # Logging
    LOG_FILE = BASE_DIR / "logs" / "docai.log"
    LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Flask settings
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-key-change-in-production")
    
    # AI Provider settings (copied from original)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Document processing
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'.doc', '.docx', '.odt', '.pdf', '.txt'}
    
    # Window settings
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    WINDOW_MIN_WIDTH = 800
    WINDOW_MIN_HEIGHT = 600
    
    # UNO settings
    UNO_TIMEOUT = 30
    UNO_RETRY_COUNT = 3
    UNO_RETRY_DELAY = 2
    
    # Startup settings
    BACKEND_STARTUP_TIMEOUT = 30  # seconds
    STARTUP_FILE = None  # Set via CLI args
    
    # Timeouts
    WINDOW_READY_TIMEOUT = 10
    SHUTDOWN_TIMEOUT = 5

# Global configuration instance
CFG = Config()

# Initialize directories on import
CFG.ensure_directories()