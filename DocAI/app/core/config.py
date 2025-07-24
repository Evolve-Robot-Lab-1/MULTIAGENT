"""
Configuration management for DocAI application.
Centralizes all configuration and environment variable handling.
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    uri: str = "sqlite:///docai.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30


@dataclass
class StorageConfig:
    """File storage configuration."""
    upload_folder: Path
    documents_folder: Path
    temp_folder: Path
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    allowed_extensions: set = field(default_factory=lambda: {'txt', 'pdf', 'doc', 'docx'})
    
    def __post_init__(self):
        """Ensure directories exist."""
        for folder in [self.upload_folder, self.documents_folder, self.temp_folder]:
            folder.mkdir(parents=True, exist_ok=True)


@dataclass
class AIConfig:
    """AI provider configuration."""
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    default_provider: str = "groq"
    max_tokens: int = 5000
    temperature: float = 0.7
    streaming: bool = True


@dataclass
class ServerConfig:
    """Web server configuration."""
    host: str = "0.0.0.0"
    port: int = 8090
    debug: bool = False
    secret_key: str = "change-me-in-production"
    cors_origins: list = field(default_factory=lambda: ["*"])
    session_lifetime_minutes: int = 1440  # 24 hours


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    file_path: Path = Path("logs/app.log")
    error_file_path: Path = Path("logs/error.log")
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    def __post_init__(self):
        """Ensure log directory exists."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class AgentConfig:
    """Agent configuration."""
    browser_agent_path: Path
    browser_agent_port: int = 7788
    auto_start_browser_agent: bool = True
    health_check_interval: int = 30
    startup_timeout: int = 60


@dataclass
class RAGConfig:
    """RAG (Retrieval Augmented Generation) configuration."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_type: str = "faiss"
    similarity_threshold: float = 0.7
    max_results: int = 5


@dataclass
class Config:
    """Main configuration class that aggregates all config sections."""
    database: DatabaseConfig
    storage: StorageConfig
    ai: AIConfig
    server: ServerConfig
    logging: LoggingConfig
    agent: AgentConfig
    rag: RAGConfig
    
    # Environment
    environment: str = "development"
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'Config':
        """
        Create configuration from environment variables.
        
        Args:
            env_file: Path to .env file (optional)
            
        Returns:
            Config instance
            
        Raises:
            ValueError: If required configuration is missing
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Get base paths
        base_path = Path(os.getenv('BASE_PATH', os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        upload_folder = base_path / os.getenv('UPLOAD_FOLDER', 'uploads')
        
        # Create configuration
        config = cls(
            database=DatabaseConfig(
                uri=os.getenv('DATABASE_URI', 'sqlite:///docai.db')
            ),
            storage=StorageConfig(
                upload_folder=upload_folder,
                documents_folder=upload_folder / 'documents',
                temp_folder=upload_folder / 'temp',
                max_content_length=int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
            ),
            ai=AIConfig(
                groq_api_key=os.getenv('GROQ_API_KEY'),
                groq_model=os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
                gemini_api_key=os.getenv('GEMINI_API_KEY'),
                default_provider=os.getenv('DEFAULT_AI_PROVIDER', 'groq'),
                max_tokens=int(os.getenv('MAX_TOKENS', 5000)),
                temperature=float(os.getenv('TEMPERATURE', 0.7))
            ),
            server=ServerConfig(
                host=os.getenv('HOST', '0.0.0.0'),
                port=int(os.getenv('PORT', 8090)),
                debug=os.getenv('DEBUG', 'False').lower() == 'true',
                secret_key=os.getenv('FLASK_SECRET_KEY', 'change-me-in-production')
            ),
            logging=LoggingConfig(
                level=os.getenv('LOG_LEVEL', 'INFO'),
                file_path=Path(os.getenv('LOG_FILE', 'logs/app.log')),
                error_file_path=Path(os.getenv('ERROR_LOG_FILE', 'logs/error.log'))
            ),
            agent=AgentConfig(
                browser_agent_path=base_path.parent / 'AGENT_B' / 'launch_offline.sh',
                browser_agent_port=int(os.getenv('BROWSER_AGENT_PORT', 7788)),
                auto_start_browser_agent=os.getenv('AUTO_START_BROWSER_AGENT', 'True').lower() == 'true'
            ),
            rag=RAGConfig(
                chunk_size=int(os.getenv('RAG_CHUNK_SIZE', 1000)),
                chunk_overlap=int(os.getenv('RAG_CHUNK_OVERLAP', 200)),
                embedding_model=os.getenv('RAG_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            ),
            environment=os.getenv('ENVIRONMENT', 'development')
        )
        
        # Validate configuration
        config.validate()
        
        return config
    
    def validate(self):
        """
        Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Check required AI keys
        if not any([self.ai.groq_api_key, self.ai.openai_api_key, 
                   self.ai.anthropic_api_key, self.ai.gemini_api_key]):
            raise ValueError("At least one AI provider API key must be configured")
        
        # Check if default provider has API key
        provider_keys = {
            'groq': self.ai.groq_api_key,
            'openai': self.ai.openai_api_key,
            'anthropic': self.ai.anthropic_api_key,
            'gemini': self.ai.gemini_api_key
        }
        
        if self.ai.default_provider not in provider_keys:
            raise ValueError(f"Invalid default provider: {self.ai.default_provider}")
        
        if not provider_keys[self.ai.default_provider]:
            raise ValueError(f"API key not configured for default provider: {self.ai.default_provider}")
        
        # Check browser agent path if auto-start is enabled
        if self.agent.auto_start_browser_agent and not self.agent.browser_agent_path.exists():
            raise ValueError(f"Browser agent launch script not found: {self.agent.browser_agent_path}")
        
        # Validate server configuration
        if self.server.port < 1 or self.server.port > 65535:
            raise ValueError(f"Invalid port number: {self.server.port}")
        
        # Validate storage configuration
        if self.storage.max_content_length < 1024:  # At least 1KB
            raise ValueError("Max content length too small")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'environment': self.environment,
            'database': {
                'uri': self.database.uri,
                'pool_size': self.database.pool_size
            },
            'storage': {
                'upload_folder': str(self.storage.upload_folder),
                'max_content_length': self.storage.max_content_length,
                'allowed_extensions': list(self.storage.allowed_extensions)
            },
            'ai': {
                'default_provider': self.ai.default_provider,
                'model': self.ai.groq_model,
                'max_tokens': self.ai.max_tokens,
                'temperature': self.ai.temperature
            },
            'server': {
                'host': self.server.host,
                'port': self.server.port,
                'debug': self.server.debug
            },
            'logging': {
                'level': self.logging.level,
                'file_path': str(self.logging.file_path)
            },
            'agent': {
                'browser_agent_port': self.agent.browser_agent_port,
                'auto_start': self.agent.auto_start_browser_agent
            },
            'rag': {
                'chunk_size': self.rag.chunk_size,
                'embedding_model': self.rag.embedding_model
            }
        }


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get configuration singleton."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config():
    """Reset configuration (useful for testing)."""
    global _config
    _config = None