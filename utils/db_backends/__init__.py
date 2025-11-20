"""
Database backend registry.

Backends register themselves here and can be retrieved by name.
"""
from typing import Dict, Type, Optional
from .base import DatabaseBackend


# Registry of available backends
_backends: Dict[str, Type[DatabaseBackend]] = {}


def register_backend(name: str, backend_class: Type[DatabaseBackend]) -> None:
    """
    Register a database backend.
    
    Args:
        name: Backend name (e.g., 'postgresql', 'sqlite')
        backend_class: Backend class implementing DatabaseBackend
    """
    _backends[name.lower()] = backend_class


def get_backend(name: str) -> DatabaseBackend:
    """
    Get a backend instance by name.
    
    Args:
        name: Backend name (e.g., 'postgresql', 'sqlite')
        
    Returns:
        Backend instance
        
    Raises:
        ValueError: If backend is not registered
    """
    backend_name = name.lower()
    if backend_name not in _backends:
        available = ', '.join(_backends.keys())
        raise ValueError(
            f"Unknown database backend '{name}'. "
            f"Available backends: {available}"
        )
    backend_class = _backends[backend_name]
    return backend_class()


def detect_backend_type(config: Dict) -> str:
    """
    Detect backend type from configuration.
    
    Detection order:
    1. Explicit 'type' field in config
    2. URL pattern detection (if 'url' field exists)
    3. Default to 'postgresql' for backward compatibility
    
    Args:
        config: Database configuration dictionary
        
    Returns:
        Backend type name (e.g., 'postgresql', 'sqlite')
    """
    # Check for explicit type field
    if 'type' in config:
        return config['type'].lower()
    
    # Check for URL pattern (if url field exists)
    if 'url' in config:
        url = str(config['url']).lower()
        if url.startswith('sqlite'):
            return 'sqlite'
        elif url.startswith('postgresql'):
            return 'postgresql'
        elif url.startswith('mysql'):
            return 'mysql'
    
    # Check for SQLite-specific fields (database path without host/port)
    if 'database' in config and 'host' not in config and 'port' not in config:
        # Could be SQLite, but we need more context
        # If it looks like a file path, assume SQLite
        db_path = str(config['database'])
        if db_path.endswith('.db') or '/' in db_path or '\\' in db_path:
            return 'sqlite'
    
    # Default to PostgreSQL for backward compatibility
    return 'postgresql'


def list_backends() -> list[str]:
    """
    List all registered backend names.
    
    Returns:
        List of backend names
    """
    return list(_backends.keys())


# Auto-register backends when module is imported
from .postgresql import PostgreSQLBackend
from .sqlite import SQLiteBackend

register_backend("postgresql", PostgreSQLBackend)
register_backend("sqlite", SQLiteBackend)

