"""
PostgreSQL database backend implementation.
"""
from typing import Dict, Any
from urllib.parse import quote_plus
from .base import DatabaseBackend


class PostgreSQLBackend(DatabaseBackend):
    """PostgreSQL database backend."""
    
    def get_sync_url(self, config: Dict[str, Any]) -> str:
        """
        Generate PostgreSQL synchronous connection URL.
        
        Format: postgresql://user:password@host:port/database
        """
        user = quote_plus(str(config.get("user", "")))
        password = quote_plus(str(config.get("password", "")))
        host = str(config.get("host", ""))
        port = str(config.get("port", "5432"))
        database = str(config.get("database", ""))
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def get_async_url(self, config: Dict[str, Any]) -> str:
        """
        Generate PostgreSQL asynchronous connection URL.
        
        Format: postgresql+asyncpg://user:password@host:port/database
        """
        sync_url = self.get_sync_url(config)
        # Replace postgresql:// with postgresql+asyncpg://
        return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    def get_pool_config(self) -> Dict[str, Any]:
        """
        Get PostgreSQL connection pool configuration.
        
        Returns:
            Dictionary with pool settings optimized for PostgreSQL
        """
        return {
            "pool_size": 50,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "echo": False,
        }
    
    def get_connect_args(self) -> Dict[str, Any]:
        """
        Get PostgreSQL connection arguments.
        
        Returns:
            Dictionary with PostgreSQL-specific connection arguments
        """
        return {
            "command_timeout": 30,  # 30 second command timeout
        }
    
    def get_migration_settings(self) -> Dict[str, Any]:
        """
        Get PostgreSQL migration-specific settings.
        
        Returns:
            Dictionary with migration settings for PostgreSQL
        """
        return {
            "render_as_batch": False,  # PostgreSQL supports full ALTER TABLE
            "connect_args": {
                "connect_timeout": 10,
                "options": "-c statement_timeout=60000",  # 60 second timeout for index creation
            },
        }
    
    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate PostgreSQL configuration.
        
        Required fields: host, port, database, user
        Optional fields: password
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["host", "port", "database", "user"]
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            raise ValueError(
                f"Missing required PostgreSQL configuration fields: {', '.join(missing_fields)}. "
                f"Please ensure all fields (host, port, database, user) are present in app.yaml "
                "or set via environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER)."
            )

