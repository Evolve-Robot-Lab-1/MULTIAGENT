"""
Groq AI provider implementation.
"""
import asyncio
from typing import List, Optional, AsyncGenerator
import groq
from groq import AsyncGroq

from app.services.ai_providers.base import (
    AIProvider, AIResponse, AIStreamResponse, Message
)
from app.core.logging import get_logger
from app.core.exceptions import AIProviderError


logger = get_logger(__name__)


class GroqProvider(AIProvider):
    """
    Groq AI provider implementation.
    """
    
    def __init__(self, api_key: str, default_model: Optional[str] = None):
        super().__init__(api_key, default_model or "llama-3.3-70b-versatile")
        self.client = groq.Groq(api_key=api_key)
        self.async_client = AsyncGroq(api_key=api_key)
    
    @property
    def name(self) -> str:
        return "groq"
    
    @property
    def available_models(self) -> List[str]:
        return [
            "llama-3.3-70b-versatile",
            "llama3-groq-70b-8192-tool-use-preview",
            "llama3-groq-8b-8192-tool-use-preview",
            "mixtral-8x7b-32768",
            "gemma-7b-it",
            "deepseek-r1-distill-llama-70b"
        ]
    
    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Get completion from Groq.
        
        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Temperature for sampling
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Groq-specific parameters
            
        Returns:
            AIResponse
        """
        model = model or self.default_model
        
        if not self.validate_model(model):
            raise AIProviderError(
                "groq",
                f"Model '{model}' is not available"
            )
        
        try:
            # Format messages
            formatted_messages = self.format_messages(messages)
            
            # Make API call
            response = await self.async_client.chat.completions.create(
                messages=formatted_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens or 2000,
                **kwargs
            )
            
            # Extract response
            content = response.choices[0].message.content
            
            # Build usage info
            usage = None
            if response.usage:
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            
            return AIResponse(
                content=content,
                model=model,
                provider=self.name,
                usage=usage,
                metadata={
                    'finish_reason': response.choices[0].finish_reason,
                    'response_id': response.id
                }
            )
            
        except groq.APIError as e:
            logger.error(f"Groq API error: {e}")
            raise AIProviderError("groq", f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Groq provider: {e}", exc_info=True)
            raise AIProviderError("groq", f"Unexpected error: {str(e)}")
    
    async def stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[AIStreamResponse, None]:
        """
        Stream completion from Groq.
        
        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Temperature for sampling
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Groq-specific parameters
            
        Yields:
            AIStreamResponse chunks
        """
        model = model or self.default_model
        
        if not self.validate_model(model):
            raise AIProviderError(
                "groq",
                f"Model '{model}' is not available"
            )
        
        try:
            # Format messages
            formatted_messages = self.format_messages(messages)
            
            # Make streaming API call
            stream = await self.async_client.chat.completions.create(
                messages=formatted_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens or 2000,
                stream=True,
                **kwargs
            )
            
            # Stream responses
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield AIStreamResponse(
                            content=content,
                            is_final=False,
                            metadata={'chunk_id': chunk.id}
                        )
            
            # Send final chunk
            yield AIStreamResponse(
                content="",
                is_final=True,
                metadata={'model': model, 'provider': self.name}
            )
            
        except groq.APIError as e:
            logger.error(f"Groq streaming error: {e}")
            raise AIProviderError("groq", f"Streaming error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected streaming error: {e}", exc_info=True)
            raise AIProviderError("groq", f"Unexpected error: {str(e)}")