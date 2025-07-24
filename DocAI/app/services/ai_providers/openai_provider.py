"""
OpenAI AI provider implementation.
"""
from typing import List, Optional, AsyncGenerator
from openai import AsyncOpenAI

from app.services.ai_providers.base import (
    AIProvider, AIResponse, AIStreamResponse, Message
)
from app.core.logging import get_logger
from app.core.exceptions import AIProviderError


logger = get_logger(__name__)


class OpenAIProvider(AIProvider):
    """
    OpenAI provider implementation.
    """
    
    def __init__(self, api_key: str, default_model: Optional[str] = None):
        super().__init__(api_key, default_model or "gpt-4-turbo-preview")
        self.client = AsyncOpenAI(api_key=api_key)
    
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def available_models(self) -> List[str]:
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    async def complete(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """Get completion from OpenAI."""
        model = model or self.default_model
        
        if not self.validate_model(model):
            raise AIProviderError(
                "openai",
                f"Model '{model}' is not available"
            )
        
        try:
            formatted_messages = self.format_messages(messages)
            
            response = await self.client.chat.completions.create(
                messages=formatted_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            content = response.choices[0].message.content
            
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
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}", exc_info=True)
            raise AIProviderError("openai", str(e))
    
    async def stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[AIStreamResponse, None]:
        """Stream completion from OpenAI."""
        model = model or self.default_model
        
        if not self.validate_model(model):
            raise AIProviderError(
                "openai",
                f"Model '{model}' is not available"
            )
        
        try:
            formatted_messages = self.format_messages(messages)
            
            stream = await self.client.chat.completions.create(
                messages=formatted_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield AIStreamResponse(
                            content=content,
                            is_final=False,
                            metadata={'chunk_id': chunk.id}
                        )
            
            yield AIStreamResponse(
                content="",
                is_final=True,
                metadata={'model': model, 'provider': self.name}
            )
            
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}", exc_info=True)
            raise AIProviderError("openai", str(e))