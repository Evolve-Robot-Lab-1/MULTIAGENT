"""
AI Provider factory for creating provider instances.
"""
from typing import Optional, Dict, Type

from app.services.ai_providers.base import AIProvider
from app.services.ai_providers.groq_provider import GroqProvider
from app.services.ai_providers.openai_provider import OpenAIProvider
from app.core.config import Config
from app.core.exceptions import AIProviderError


class AIProviderFactory:
    """
    Factory for creating AI provider instances.
    """
    
    # Registry of available providers
    _providers: Dict[str, Type[AIProvider]] = {
        'groq': GroqProvider,
        'openai': OpenAIProvider,
    }
    
    @classmethod
    def create(
        cls,
        provider_name: str,
        config: Config,
        default_model: Optional[str] = None
    ) -> AIProvider:
        """
        Create an AI provider instance.
        
        Args:
            provider_name: Name of the provider
            config: Application configuration
            default_model: Default model to use
            
        Returns:
            AIProvider instance
            
        Raises:
            AIProviderError: If provider is not available or not configured
        """
        # Validate provider name
        if provider_name not in cls._providers:
            raise AIProviderError(
                provider_name,
                f"Unknown provider. Available: {list(cls._providers.keys())}"
            )
        
        # Get API key from config
        api_key = cls._get_api_key(provider_name, config)
        if not api_key:
            raise AIProviderError(
                provider_name,
                f"API key not configured for provider '{provider_name}'"
            )
        
        # Create provider instance
        provider_class = cls._providers[provider_name]
        return provider_class(api_key, default_model)
    
    @classmethod
    def create_default(cls, config: Config) -> AIProvider:
        """
        Create the default AI provider from config.
        
        Args:
            config: Application configuration
            
        Returns:
            Default AIProvider instance
        """
        return cls.create(
            config.ai.default_provider,
            config,
            cls._get_default_model(config.ai.default_provider, config)
        )
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[AIProvider]) -> None:
        """
        Register a new AI provider.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
    
    @staticmethod
    def _get_api_key(provider_name: str, config: Config) -> Optional[str]:
        """Get API key for provider from config."""
        key_mapping = {
            'groq': config.ai.groq_api_key,
            'openai': config.ai.openai_api_key,
            'anthropic': config.ai.anthropic_api_key,
            'gemini': config.ai.gemini_api_key,
        }
        return key_mapping.get(provider_name)
    
    @staticmethod
    def _get_default_model(provider_name: str, config: Config) -> Optional[str]:
        """Get default model for provider."""
        model_mapping = {
            'groq': config.ai.groq_model,
            'openai': 'gpt-4-turbo-preview',
            'anthropic': 'claude-3-opus-20240229',
            'gemini': 'gemini-pro',
        }
        return model_mapping.get(provider_name)