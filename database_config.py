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
    """Extract database configuration from app.yaml."""
    config = load_app_yaml()
    
    # Check for database section in config
    database_config = config.get("database")
    
    if not database_config:
        raise ValueError(
            "Database configuration not found in app.yaml. "
            "Please add a 'database:' section with host, port, database, user, and password fields."
        )
    
    # Validate required fields
    required_fields = ["host", "port", "database", "user", "password"]
    missing_fields = [field for field in required_fields if field not in database_config]
    
    if missing_fields:
        raise ValueError(
            f"Missing required database configuration fields: {', '.join(missing_fields)}. "
            "Please ensure all fields (host, port, database, user, password) are present in app.yaml."
        )
    
    return {
        "host": str(database_config["host"]),
        "port": str(database_config["port"]),
        "database": str(database_config["database"]),
        "user": str(database_config["user"]),
        "password": str(database_config["password"]),
    }


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

