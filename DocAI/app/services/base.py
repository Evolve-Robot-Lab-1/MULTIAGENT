"""
Base service classes and dependency injection framework.
Provides foundation for all service classes in the application.
"""
import logging
from typing import TypeVar, Type, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from contextvars import ContextVar

from app.core.config import Config, get_config
from app.core.logging import get_logger
from app.core.exceptions import DocAIException


# Type variable for generic service types
TService = TypeVar('TService', bound='BaseService')


# Context variable for dependency injection container
_container_var: ContextVar[Optional['Container']] = ContextVar('container', default=None)


class BaseService(ABC):
    """
    Base class for all services.
    Provides common functionality like logging and configuration access.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize base service.
        
        Args:
            config: Application configuration (uses default if not provided)
        """
        self.config = config or get_config()
        self.logger = get_logger(self.__class__.__module__)
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize service resources.
        Override in subclasses for async initialization.
        """
        self._initialized = True
        self.logger.info(f"{self.__class__.__name__} initialized")
    
    async def cleanup(self) -> None:
        """
        Clean up service resources.
        Override in subclasses for cleanup logic.
        """
        self._initialized = False
        self.logger.info(f"{self.__class__.__name__} cleaned up")
    
    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized
    
    def ensure_initialized(self) -> None:
        """
        Ensure service is initialized.
        
        Raises:
            RuntimeError: If service is not initialized
        """
        if not self._initialized:
            raise RuntimeError(f"{self.__class__.__name__} is not initialized")


class Container:
    """
    Simple dependency injection container.
    Manages service instances and their lifecycles.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize container.
        
        Args:
            config: Application configuration
        """
        self.config = config or get_config()
        self._services: Dict[Type[BaseService], BaseService] = {}
        self._factories: Dict[Type[BaseService], Any] = {}
        self.logger = get_logger(__name__)
    
    def register(self, service_class: Type[TService], 
                factory: Optional[Any] = None) -> None:
        """
        Register a service class with optional factory.
        
        Args:
            service_class: Service class to register
            factory: Optional factory function or class
        """
        self._factories[service_class] = factory or service_class
        self.logger.debug(f"Registered service: {service_class.__name__}")
    
    def get(self, service_class: Type[TService]) -> TService:
        """
        Get or create a service instance.
        
        Args:
            service_class: Service class to get
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        # Return existing instance if available
        if service_class in self._services:
            return self._services[service_class]
        
        # Create new instance
        if service_class not in self._factories:
            raise KeyError(f"Service not registered: {service_class.__name__}")
        
        factory = self._factories[service_class]
        
        # Create instance
        if callable(factory):
            instance = factory(self.config)
        else:
            instance = factory
        
        # Store and return
        self._services[service_class] = instance
        self.logger.debug(f"Created service instance: {service_class.__name__}")
        
        return instance
    
    async def initialize_all(self) -> None:
        """Initialize all registered services."""
        for service in self._services.values():
            if hasattr(service, 'initialize') and not service.is_initialized:
                await service.initialize()
    
    async def cleanup_all(self) -> None:
        """Clean up all services."""
        for service in reversed(list(self._services.values())):
            if hasattr(service, 'cleanup'):
                await service.cleanup()
        
        self._services.clear()
    
    def __enter__(self):
        """Context manager entry."""
        _container_var.set(self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        _container_var.set(None)


def get_container() -> Container:
    """
    Get current container from context.
    
    Returns:
        Current container
        
    Raises:
        RuntimeError: If no container in context
    """
    container = _container_var.get()
    if container is None:
        raise RuntimeError("No container in context")
    return container


def inject(service_class: Type[TService]) -> TService:
    """
    Inject a service from the current container.
    
    Args:
        service_class: Service class to inject
        
    Returns:
        Service instance
    """
    container = get_container()
    return container.get(service_class)


@dataclass
class ServiceResult:
    """
    Standard result type for service operations.
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def ok(cls, data: Any = None, **metadata) -> 'ServiceResult':
        """Create successful result."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def fail(cls, error: str, **metadata) -> 'ServiceResult':
        """Create failed result."""
        return cls(success=False, error=error, metadata=metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'success': self.success,
            'data': self.data,
            'error': self.error
        }
        if self.metadata:
            result['metadata'] = self.metadata
        return result


class TransactionalService(BaseService):
    """
    Base service with transaction support.
    Provides commit/rollback functionality.
    """
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self._in_transaction = False
        self._transaction_data = {}
    
    async def begin_transaction(self) -> None:
        """Begin a new transaction."""
        self.ensure_initialized()
        if self._in_transaction:
            raise RuntimeError("Transaction already in progress")
        
        self._in_transaction = True
        self._transaction_data = {}
        await self._on_begin_transaction()
    
    async def commit_transaction(self) -> None:
        """Commit current transaction."""
        if not self._in_transaction:
            raise RuntimeError("No transaction in progress")
        
        try:
            await self._on_commit_transaction()
            self._in_transaction = False
            self._transaction_data = {}
        except Exception:
            await self.rollback_transaction()
            raise
    
    async def rollback_transaction(self) -> None:
        """Rollback current transaction."""
        if not self._in_transaction:
            raise RuntimeError("No transaction in progress")
        
        await self._on_rollback_transaction()
        self._in_transaction = False
        self._transaction_data = {}
    
    @abstractmethod
    async def _on_begin_transaction(self) -> None:
        """Override to implement transaction begin logic."""
        pass
    
    @abstractmethod
    async def _on_commit_transaction(self) -> None:
        """Override to implement transaction commit logic."""
        pass
    
    @abstractmethod
    async def _on_rollback_transaction(self) -> None:
        """Override to implement transaction rollback logic."""
        pass


class CachedService(BaseService):
    """
    Base service with caching support.
    Provides simple in-memory caching.
    """
    
    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)
        self._cache: Dict[str, Any] = {}
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(key)
    
    def cache_set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self._cache[key] = value
    
    def cache_delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)
    
    def cache_clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
    
    async def cleanup(self) -> None:
        """Clean up service resources."""
        self.cache_clear()
        await super().cleanup()