"""
Abstract base class for database backends.

Each database backend (PostgreSQL, SQLite, etc.) implements this interface
to provide backend-specific connection URLs, pool settings, and migration configuration.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class DatabaseBackend(ABC):
    """Abstract base class for database backend implementations."""
    
    @abstractmethod
    def get_sync_url(self, config: Dict[str, Any]) -> str:
        """
        Generate synchronous connection URL for this backend.
        
        Args:
            config: Database configuration dictionary from app.yaml
            
        Returns:
            SQLAlchemy connection URL string (e.g., 'postgresql://...' or 'sqlite:///...')
        """
        pass
    
    @abstractmethod
    def get_async_url(self, config: Dict[str, Any]) -> str:
        """
        Generate asynchronous connection URL for this backend.
        
        Args:
            config: Database configuration dictionary from app.yaml
            
        Returns:
            SQLAlchemy async connection URL string (e.g., 'postgresql+asyncpg://...' or 'sqlite+aiosqlite:///...')
        """
        pass
    
    @abstractmethod
    def get_pool_config(self) -> Dict[str, Any]:
        """
        Get connection pool configuration for this backend.
        
        Returns:
            Dictionary with pool settings (pool_size, max_overflow, pool_pre_ping, etc.)
        """
        pass
    
    @abstractmethod
    def get_connect_args(self) -> Dict[str, Any]:
        """
        Get connection-specific arguments for this backend.
        
        Returns:
            Dictionary with connection arguments (timeouts, options, etc.)
        """
        pass
    
    @abstractmethod
    def get_migration_settings(self) -> Dict[str, Any]:
        """
        Get migration-specific settings for this backend.
        
        Returns:
            Dictionary with migration settings (render_as_batch, pragmas, etc.)
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate backend-specific configuration.
        
        Args:
            config: Database configuration dictionary from app.yaml
            
        Raises:
            ValueError: If configuration is invalid or missing required fields
        """
        pass
    
    def ensure_database_exists(self, config: Dict[str, Any]) -> None:
        """
        Ensure database file/directory exists (for file-based databases like SQLite).
        
        Default implementation does nothing. Override in subclasses if needed.
        
        Args:
            config: Database configuration dictionary from app.yaml
        """
        pass

