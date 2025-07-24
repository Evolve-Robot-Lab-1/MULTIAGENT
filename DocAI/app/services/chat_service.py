"""
Chat service for handling conversations and AI interactions.
"""
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import uuid
import json

from app.services.base import BaseService, ServiceResult
from app.services.ai_providers import AIProviderFactory, AIProvider, Message, MessageRole
from app.services.rag_service import RAGService
from app.core.config import Config
from app.core.exceptions import ChatSessionNotFoundError, AIProviderError


class ChatService(BaseService):
    """
    Service for managing chat sessions and AI interactions.
    """
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        
        # Chat session storage (in-memory for now)
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}
        
        # AI provider
        self._ai_provider: Optional[AIProvider] = None
        
    async def create_session(self) -> str:
        """
        Create a new chat session.
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = [
            {
                "role": "system",
                "content": "You are Durga AI, a helpful document processing assistant. Please respond in English."
            }
        ]
        
        self.logger.info(f"Created new chat session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get chat session history.
        
        Args:
            session_id: Session ID
            
        Returns:
            Chat history
            
        Raises:
            ChatSessionNotFoundError: If session not found
        """
        if session_id not in self._sessions:
            raise ChatSessionNotFoundError(session_id)
        
        return self._sessions[session_id]
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Add message to chat session.
        
        Args:
            session_id: Session ID
            role: Message role ('user', 'assistant', 'system')
            content: Message content
        """
        if session_id not in self._sessions:
            raise ChatSessionNotFoundError(session_id)
        
        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def clear_session(self, session_id: str) -> None:
        """
        Clear chat session history.
        
        Args:
            session_id: Session ID
        """
        if session_id in self._sessions:
            # Keep system message
            system_msg = self._sessions[session_id][0]
            self._sessions[session_id] = [system_msg]
            self.logger.info(f"Cleared chat session: {session_id}")
    
    async def initialize(self) -> None:
        """Initialize the chat service."""
        await super().initialize()
        
        # Create AI provider
        self._ai_provider = AIProviderFactory.create_default(self.config)
        self.logger.info(f"Initialized with AI provider: {self._ai_provider.name}")
    
    async def chat_completion(
        self,
        session_id: str,
        message: str,
        model: Optional[str] = None,
        use_rag: bool = False,
        provider: Optional[str] = None
    ) -> ServiceResult:
        """
        Get chat completion.
        
        Args:
            session_id: Session ID
            message: User message
            model: Model to use (uses default if not specified)
            use_rag: Whether to use RAG
            provider: AI provider to use (uses default if not specified)
            
        Returns:
            ServiceResult with response
        """
        try:
            # Get or create AI provider
            if provider and provider != self.config.ai.default_provider:
                ai_provider = AIProviderFactory.create(provider, self.config, model)
            else:
                ai_provider = self._ai_provider
            
            # Add user message
            await self.add_message(session_id, "user", message)
            
            # Get session history
            history = await self.get_session(session_id)
            
            # Convert to Message objects
            messages = []
            for msg in history:
                messages.append(Message(
                    role=MessageRole(msg["role"]),
                    content=msg["content"]
                ))
            
            # Check if we should use RAG
            if use_rag:
                # Get RAG service from container
                from app.services.base import get_container
                try:
                    container = get_container()
                    rag_service = container.get(RAGService)
                    
                    # Search for relevant content
                    search_result = await rag_service.search(message, limit=3)
                    
                    if search_result.success and search_result.data['results']:
                        # Add context to the system message
                        context_parts = []
                        for result in search_result.data['results']:
                            context_parts.append(result['chunk']['content'])
                        
                        context = "\n\n".join(context_parts)
                        rag_prompt = f"Use the following context to answer the question:\n\n{context}\n\nQuestion: {message}"
                        
                        # Replace last user message with RAG-enhanced version
                        messages[-1] = Message(
                            role=MessageRole.USER,
                            content=rag_prompt
                        )
                except Exception as e:
                    self.logger.warning(f"RAG enhancement failed: {e}")
                    # Continue without RAG
            
            # Get completion from AI provider
            response = await ai_provider.complete(
                messages=messages,
                model=model,
                temperature=self.config.ai.temperature,
                max_tokens=self.config.ai.max_tokens
            )
            
            # Add assistant response
            await self.add_message(session_id, "assistant", response.content)
            
            return ServiceResult.ok({
                "response": response.content,
                "model": response.model,
                "provider": response.provider,
                "session_id": session_id,
                "usage": response.usage
            })
            
        except AIProviderError as e:
            self.logger.error(f"AI provider error: {e}")
            return ServiceResult.fail(str(e))
        except Exception as e:
            self.logger.error(f"Chat completion error: {e}", exc_info=True)
            return ServiceResult.fail(f"Chat completion failed: {str(e)}")
    
    async def stream_completion(
        self,
        session_id: str,
        message: str,
        model: Optional[str] = None,
        use_rag: bool = False,
        provider: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion.
        
        Args:
            session_id: Session ID
            message: User message
            model: Model to use
            use_rag: Whether to use RAG
            provider: AI provider to use
            
        Yields:
            Response chunks
        """
        try:
            # Get or create AI provider
            if provider and provider != self.config.ai.default_provider:
                ai_provider = AIProviderFactory.create(provider, self.config, model)
            else:
                ai_provider = self._ai_provider
            
            # Add user message
            await self.add_message(session_id, "user", message)
            
            # Get session history
            history = await self.get_session(session_id)
            
            # Convert to Message objects
            messages = []
            for msg in history:
                messages.append(Message(
                    role=MessageRole(msg["role"]),
                    content=msg["content"]
                ))
            
            # Apply RAG if requested
            if use_rag:
                # Similar to chat_completion RAG logic
                pass  # Simplified for now
            
            # Stream completion from AI provider
            full_response = ""
            async for chunk in ai_provider.stream(
                messages=messages,
                model=model,
                temperature=self.config.ai.temperature,
                max_tokens=self.config.ai.max_tokens
            ):
                if chunk.content:
                    full_response += chunk.content
                    yield json.dumps({
                        'text': chunk.content,
                        'is_final': chunk.is_final
                    }) + '\n'
            
            # Add complete response to history
            await self.add_message(session_id, "assistant", full_response)
            
            # Send final marker
            yield json.dumps({
                'text': '',
                'is_final': True,
                'model': model or ai_provider.default_model,
                'provider': ai_provider.name
            }) + '\n'
            
        except Exception as e:
            self.logger.error(f"Stream completion error: {e}", exc_info=True)
            yield json.dumps({
                'error': str(e),
                'is_final': True
            }) + '\n'