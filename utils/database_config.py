"""
Database configuration module for reading connection settings from app.yaml.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote_plus


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
    """
    config = load_app_yaml()
    
    # Determine which database config to use based on DB_ENV
    db_env = os.getenv("DB_ENV", "databricks").lower()
    
    if db_env == "local":
        config_key = "database_local"
    else:
        config_key = "database_databricks"
    
    # Check for database section in config
    database_config = config.get(config_key)
    
    if not database_config:
        raise ValueError(
            f"Database configuration '{config_key}' not found in app.yaml. "
            f"Please add a '{config_key}:' section with host, port, database, user, and password fields."
        )
    
    # Allow environment variables to override config file values
    db_config = {
        "host": os.getenv("DB_HOST") or str(database_config.get("host", "")),
        "port": os.getenv("DB_PORT") or str(database_config.get("port", "")),
        "database": os.getenv("DB_NAME") or str(database_config.get("database", "")),
        "user": os.getenv("DB_USER") or str(database_config.get("user", "")),
        "password": os.getenv("DB_PASSWORD") or str(database_config.get("password", "")),
    }
    
    # Validate required fields
    required_fields = ["host", "port", "database", "user"]
    missing_fields = [field for field in required_fields if not db_config[field]]
    
    if missing_fields:
        raise ValueError(
            f"Missing required database configuration fields: {', '.join(missing_fields)}. "
            f"Please ensure all fields (host, port, database, user) are present in app.yaml '{config_key}' section "
            "or set via environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER)."
        )
    
    return db_config


def get_database_url() -> str:
    """
    Construct SQLAlchemy database connection URL from app.yaml configuration.
    
    Returns:
        PostgreSQL connection URL in format: postgresql://user:password@host:port/database
    """
    db_config = get_database_config()
    
    # URL-encode password and username to handle special characters
    user = quote_plus(db_config["user"])
    password = quote_plus(db_config["password"])
    host = db_config["host"]
    port = db_config["port"]
    database = db_config["database"]
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

