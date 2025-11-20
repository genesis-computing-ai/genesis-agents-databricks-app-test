"""
Database configuration module for reading connection settings from app.yaml.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote_plus
from .db_backends import detect_backend_type, get_backend


def load_app_yaml() -> Dict:
    """Load and parse app.yaml configuration file."""
    # Try multiple possible locations for app.yaml
    possible_paths = [
        Path("app.yaml"),
        Path(__file__).parent / "app.yaml",
        Path(os.getcwd()) / "app.yaml",
    ]
    
    for yaml_path in possible_paths:
        if yaml_path.exists():
            try:
                with open(yaml_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                raise ValueError(f"Failed to parse app.yaml at {yaml_path}: {e}")
    
    raise FileNotFoundError(
        f"app.yaml not found in any of these locations: {[str(p) for p in possible_paths]}"
    )


def get_database_config() -> Dict[str, str]:
    """
    Extract database configuration from app.yaml.
    
    Uses DB_ENV environment variable to determine which database config to use:
    - 'local' -> uses database_local section
    - 'databricks' or unset -> uses database_databricks section
    
    Individual database settings can be overridden via environment variables:
    - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    
    Returns:
        Dictionary with database configuration (backend-agnostic format)
    """
    config = load_app_yaml()
    
    # Determine which database config to use based on DB_ENV
    db_env = os.getenv("DB_ENV", "databricks").lower()
    
    if db_env == "local":
        config_key = "database_local"
    elif db_env == "sqlite":
        config_key = "database_sqlite"
    else:
        config_key = "database_databricks"
    
    # Check for database section in config
    database_config = config.get(config_key)
    
    if not database_config:
        raise ValueError(
            f"Database configuration '{config_key}' not found in app.yaml. "
            f"Please add a '{config_key}:' section with appropriate fields for your database backend."
        )
    
    # Convert to dict if needed (YAML might return different types)
    if not isinstance(database_config, dict):
        database_config = dict(database_config) if hasattr(database_config, '__dict__') else {}
    
    # Allow environment variables to override config file values
    db_config = {
        "host": os.getenv("DB_HOST") or str(database_config.get("host", "")),
        "port": os.getenv("DB_PORT") or str(database_config.get("port", "")),
        "database": os.getenv("DB_NAME") or str(database_config.get("database", "")),
        "user": os.getenv("DB_USER") or str(database_config.get("user", "")),
        "password": os.getenv("DB_PASSWORD") or str(database_config.get("password", "")),
    }
    
    # Preserve type field if present (for backend detection)
    if "type" in database_config:
        db_config["type"] = database_config["type"]
    
    # Detect backend type and validate using backend
    backend_type = detect_backend_type(db_config)
    backend = get_backend(backend_type)
    
    # Ensure database exists (for file-based databases like SQLite)
    backend.ensure_database_exists(db_config)
    
    # Validate configuration using backend
    backend.validate_config(db_config)
    
    return db_config


def get_backend_type() -> str:
    """
    Get the database backend type from configuration.
    
    Returns:
        Backend type name (e.g., 'postgresql', 'sqlite')
    """
    config = get_database_config()
    return detect_backend_type(config)


def get_database_url() -> str:
    """
    Construct SQLAlchemy database connection URL from app.yaml configuration.
    
    Uses the appropriate backend to generate the connection URL.
    
    Returns:
        SQLAlchemy connection URL (sync) for the configured backend
    """
    db_config = get_database_config()
    backend_type = detect_backend_type(db_config)
    backend = get_backend(backend_type)
    
    return backend.get_sync_url(db_config)

