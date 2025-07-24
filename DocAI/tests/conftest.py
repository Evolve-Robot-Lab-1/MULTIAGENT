"""
Pytest configuration and fixtures.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from app import create_app_with_services
from app.core.config import Config, StorageConfig, AIConfig, ServerConfig
from app.services.base import Container
from app.database import init_database, create_tables, drop_tables


@pytest.fixture
def test_config():
    """Create test configuration."""
    temp_dir = tempfile.mkdtemp()
    
    config = Config(
        database=Mock(uri="sqlite:///:memory:"),
        storage=StorageConfig(
            upload_folder=Path(temp_dir) / "uploads",
            documents_folder=Path(temp_dir) / "documents",
            temp_folder=Path(temp_dir) / "temp",
            max_content_length=1024 * 1024  # 1MB for tests
        ),
        ai=AIConfig(
            groq_api_key="test-groq-key",
            groq_model="test-model",
            default_provider="groq"
        ),
        server=ServerConfig(
            host="localhost",
            port=5000,
            debug=True,
            secret_key="test-secret-key"
        ),
        logging=Mock(
            level="DEBUG",
            file_path=Path(temp_dir) / "test.log",
            error_file_path=Path(temp_dir) / "error.log"
        ),
        agent=Mock(
            browser_agent_path=Path("/fake/path"),
            auto_start_browser_agent=False
        ),
        rag=Mock(
            chunk_size=100,
            embedding_model="test-model"
        ),
        environment="test"
    )
    
    yield config
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def app(test_config):
    """Create test Flask app."""
    app = create_app_with_services(test_config)
    app.config['TESTING'] = True
    
    # Initialize database
    with app.app_context():
        init_database(test_config)
        create_tables()
    
    yield app
    
    # Cleanup
    with app.app_context():
        drop_tables()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def container(test_config):
    """Create test service container."""
    return Container(test_config)


@pytest.fixture
def mock_ai_provider():
    """Create mock AI provider."""
    provider = Mock()
    provider.name = "test"
    provider.available_models = ["test-model"]
    provider.complete = AsyncMock(return_value=Mock(
        content="Test response",
        model="test-model",
        provider="test",
        usage={"total_tokens": 100}
    ))
    provider.stream = AsyncMock()
    return provider


@pytest.fixture
def sample_document():
    """Create sample document data."""
    return {
        'id': '12345678-1234-5678-1234-567812345678',
        'filename': 'test.pdf',
        'original_filename': 'test.pdf',
        'file_type': 'pdf',
        'file_size': 1024,
        'status': 'completed'
    }


@pytest.fixture
def sample_file():
    """Create sample file upload."""
    from werkzeug.datastructures import FileStorage
    from io import BytesIO
    
    data = BytesIO(b"Test file content")
    return FileStorage(
        stream=data,
        filename="test.txt",
        content_type="text/plain"
    )