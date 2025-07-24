"""
Base AI provider interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Chat message."""
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """AI provider response."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None  # tokens used
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIStreamResponse:
    """Streaming response chunk."""
    content: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None


class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    """
    
    def __init__(self, api_key: str, default_model: Optional[str] = None):
        """
        Initialize AI provider.
        
        Args:
            api_key: API key for the provider
            default_model: Default model to use
        """
        self.api_key = api_key
        self.default_model = default_model
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name."""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """Get list of available models."""
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Get completion from AI provider.
        
        Args:
            messages: Conversation messages
            model: Model to use (uses default if not specified)
            temperature: Temperature for sampling
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            AIResponse
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[AIStreamResponse, None]:
        """
        Stream completion from AI provider.
        
        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Temperature for sampling
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Yields:
            AIStreamResponse chunks
        """
        pass
    
    def validate_model(self, model: str) -> bool:
        """
        Validate if model is available.
        
        Args:
            model: Model name
            
        Returns:
            True if model is available
        """
        return model in self.available_models
    
    def format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Format messages for API request.
        
        Args:
            messages: List of Message objects
            
        Returns:
            List of message dictionaries
        """
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in messages
        ]