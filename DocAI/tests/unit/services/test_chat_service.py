"""
Unit tests for ChatService.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from app.services.chat_service import ChatService
from app.services.ai_providers import Message, MessageRole
from app.core.exceptions import ChatSessionNotFoundError, AIProviderError


@pytest.fixture
async def chat_service(test_config, mock_ai_provider):
    """Create chat service instance."""
    service = ChatService(test_config)
    
    # Mock AI provider factory
    with patch('app.services.chat_service.AIProviderFactory') as mock_factory:
        mock_factory.create_default.return_value = mock_ai_provider
        await service.initialize()
    
    return service


@pytest.mark.asyncio
class TestChatService:
    """Test ChatService functionality."""
    
    async def test_initialize(self, chat_service, mock_ai_provider):
        """Test service initialization."""
        assert chat_service.is_initialized
        assert chat_service._ai_provider == mock_ai_provider
    
    async def test_create_session(self, chat_service):
        """Test creating a new chat session."""
        session_id = await chat_service.create_session()
        
        assert session_id
        assert session_id in chat_service._sessions
        assert len(chat_service._sessions[session_id]) == 1  # System message
        assert chat_service._sessions[session_id][0]['role'] == 'system'
    
    async def test_get_session_exists(self, chat_service):
        """Test getting existing session."""
        session_id = await chat_service.create_session()
        
        history = await chat_service.get_session(session_id)
        
        assert len(history) == 1
        assert history[0]['role'] == 'system'
    
    async def test_get_session_not_found(self, chat_service):
        """Test getting non-existent session."""
        with pytest.raises(ChatSessionNotFoundError):
            await chat_service.get_session('non-existent-id')
    
    async def test_add_message(self, chat_service):
        """Test adding message to session."""
        session_id = await chat_service.create_session()
        
        await chat_service.add_message(session_id, 'user', 'Hello')
        await chat_service.add_message(session_id, 'assistant', 'Hi there!')
        
        history = await chat_service.get_session(session_id)
        assert len(history) == 3  # System + user + assistant
        assert history[1]['role'] == 'user'
        assert history[1]['content'] == 'Hello'
        assert history[2]['role'] == 'assistant'
        assert history[2]['content'] == 'Hi there!'
    
    async def test_clear_session(self, chat_service):
        """Test clearing session history."""
        session_id = await chat_service.create_session()
        
        # Add some messages
        await chat_service.add_message(session_id, 'user', 'Hello')
        await chat_service.add_message(session_id, 'assistant', 'Hi')
        
        # Clear session
        await chat_service.clear_session(session_id)
        
        history = await chat_service.get_session(session_id)
        assert len(history) == 1  # Only system message remains
    
    async def test_chat_completion_success(self, chat_service, mock_ai_provider):
        """Test successful chat completion."""
        session_id = await chat_service.create_session()
        
        result = await chat_service.chat_completion(
            session_id=session_id,
            message="Hello AI",
            model="test-model"
        )
        
        assert result.success
        assert result.data['response'] == "Test response"
        assert result.data['model'] == "test-model"
        assert result.data['provider'] == "test"
        assert result.data['session_id'] == session_id
        
        # Verify message was added to history
        history = await chat_service.get_session(session_id)
        assert len(history) == 3  # System + user + assistant
        assert history[1]['content'] == "Hello AI"
        assert history[2]['content'] == "Test response"
    
    async def test_chat_completion_with_rag(self, chat_service, mock_ai_provider):
        """Test chat completion with RAG."""
        session_id = await chat_service.create_session()
        
        # Mock RAG service
        mock_rag_service = Mock()
        mock_rag_service.search = AsyncMock(return_value=Mock(
            success=True,
            data={'results': [
                {'chunk': {'content': 'Relevant context'}, 'score': 0.9}
            ]}
        ))
        
        with patch('app.services.chat_service.get_container') as mock_get_container:
            mock_container = Mock()
            mock_container.get.return_value = mock_rag_service
            mock_get_container.return_value = mock_container
            
            result = await chat_service.chat_completion(
                session_id=session_id,
                message="Question about documents",
                use_rag=True
            )
        
        assert result.success
        # Verify RAG was called
        mock_rag_service.search.assert_called_once()
    
    async def test_chat_completion_ai_error(self, chat_service, mock_ai_provider):
        """Test chat completion with AI provider error."""
        session_id = await chat_service.create_session()
        
        # Make AI provider raise error
        mock_ai_provider.complete.side_effect = AIProviderError("test", "API error")
        
        result = await chat_service.chat_completion(
            session_id=session_id,
            message="Hello"
        )
        
        assert not result.success
        assert "API error" in result.error
    
    async def test_stream_completion(self, chat_service, mock_ai_provider):
        """Test streaming chat completion."""
        session_id = await chat_service.create_session()
        
        # Mock streaming response
        async def mock_stream(*args, **kwargs):
            for word in ["Hello", " ", "world"]:
                yield Mock(content=word, is_final=False)
            yield Mock(content="", is_final=True)
        
        mock_ai_provider.stream.return_value = mock_stream()
        
        # Collect stream responses
        responses = []
        async for chunk in chat_service.stream_completion(
            session_id=session_id,
            message="Test"
        ):
            responses.append(json.loads(chunk))
        
        assert len(responses) == 4  # 3 content + 1 final
        assert responses[0]['text'] == "Hello"
        assert responses[1]['text'] == " "
        assert responses[2]['text'] == "world"
        assert responses[3]['is_final'] is True
        
        # Verify message was added to history
        history = await chat_service.get_session(session_id)
        assert history[-1]['content'] == "Hello world"
    
    async def test_different_provider(self, chat_service, mock_ai_provider):
        """Test using different AI provider."""
        session_id = await chat_service.create_session()
        
        # Mock alternative provider
        alt_provider = Mock()
        alt_provider.complete = AsyncMock(return_value=Mock(
            content="Alternative response",
            model="alt-model",
            provider="alternative",
            usage={}
        ))
        
        with patch('app.services.chat_service.AIProviderFactory') as mock_factory:
            mock_factory.create.return_value = alt_provider
            
            result = await chat_service.chat_completion(
                session_id=session_id,
                message="Hello",
                provider="alternative",
                model="alt-model"
            )
        
        assert result.success
        assert result.data['response'] == "Alternative response"
        assert result.data['provider'] == "alternative"
        
        # Verify factory was called correctly
        mock_factory.create.assert_called_once_with(
            "alternative",
            chat_service.config,
            "alt-model"
        )