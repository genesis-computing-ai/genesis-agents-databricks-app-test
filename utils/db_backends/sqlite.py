"""
SQLite database backend implementation.
"""
from typing import Dict, Any
from pathlib import Path
from .base import DatabaseBackend


class SQLiteBackend(DatabaseBackend):
    """SQLite database backend."""
    
    def get_sync_url(self, config: Dict[str, Any]) -> str:
        """
        Generate SQLite synchronous connection URL.
        
        Format: sqlite:///path/to/database.db
        """
        database = str(config.get("database", ":memory:"))
        
        # Ensure absolute path for SQLite
        if database != ":memory:":
            db_path = Path(database)
            if not db_path.is_absolute():
                # Make relative to current working directory
                db_path = Path.cwd() / db_path
            database = str(db_path.resolve())
        
        # SQLite URLs always use 3 slashes: sqlite:///path/to/file.db
        return f"sqlite:///{database}"
    
    def get_async_url(self, config: Dict[str, Any]) -> str:
        """
        Generate SQLite asynchronous connection URL.
        
        Format: sqlite+aiosqlite:///path/to/database.db
        """
        sync_url = self.get_sync_url(config)
        # Replace sqlite:// with sqlite+aiosqlite://
        return sync_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    
    def get_pool_config(self) -> Dict[str, Any]:
        """
        Get SQLite connection pool configuration.
        
        SQLite doesn't benefit from large connection pools since it's file-based.
        Returns:
            Dictionary with pool settings optimized for SQLite
        """
        return {
            "pool_size": 1,  # SQLite doesn't benefit from large pools
            "max_overflow": 0,  # No overflow needed for file-based database
            "pool_pre_ping": False,  # Not needed for file-based
            "echo": False,
        }
    
    def get_connect_args(self) -> Dict[str, Any]:
        """
        Get SQLite connection arguments.
        
        Returns:
            Dictionary with SQLite-specific connection arguments
        """
        return {
            "check_same_thread": False,  # Required for async SQLite
            "timeout": 20.0,  # Lock timeout in seconds
        }
    
    def get_migration_settings(self) -> Dict[str, Any]:
        """
        Get SQLite migration-specific settings.
        
        Returns:
            Dictionary with migration settings for SQLite
        """
        return {
            "render_as_batch": True,  # SQLite has limited ALTER TABLE support
            "pragmas": [
                "PRAGMA foreign_keys=ON",
                "PRAGMA journal_mode=WAL",  # Enable WAL mode for better concurrency
                "PRAGMA busy_timeout=20000",  # 20 second busy timeout
            ],
        }
    
    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate SQLite configuration.
        
        Required fields: database (file path)
        
        Raises:
            ValueError: If required fields are missing
        """
        if "database" not in config or not config.get("database"):
            raise ValueError(
                "Missing required SQLite configuration field: 'database'. "
                "Please provide a file path (e.g., './todos.db' or '/path/to/database.db') "
                "in app.yaml or set via DB_NAME environment variable."
            )
    
    def ensure_database_exists(self, config: Dict[str, Any]) -> None:
        """
        Ensure SQLite database directory exists.
        
        Creates parent directory if it doesn't exist (for file-based databases).
        
        Args:
            config: Database configuration dictionary
        """
        database = str(config.get("database", ""))
        
        if database and database != ":memory:":
            db_path = Path(database)
            if not db_path.is_absolute():
                db_path = Path.cwd() / db_path
            
            # Create parent directory if it doesn't exist
            parent_dir = db_path.parent
            if parent_dir and not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)

