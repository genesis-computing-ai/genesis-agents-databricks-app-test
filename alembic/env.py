from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import our database configuration and schema
from utils.db_migrations import get_sync_engine
from db_schema import metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
#
# FIXED: Logger Configuration Issue
# =================================
# Previous behavior (POTENTIAL ISSUE):
# - Used fileConfig(config.config_file_name) without disable_existing_loggers parameter
# - This defaults to True, which disables all existing loggers
#
# Why this could cause hangs:
# - When Alembic disables existing loggers (especially application loggers), it can
#   interfere with FastAPI's logging setup and cause deadlocks or hangs during
#   migration execution, particularly when migrations run during application startup
# - Logger conflicts can prevent proper cleanup and transaction finalization
#
# Current solution (FIXED):
# - Set disable_existing_loggers=False to preserve existing loggers
# - This allows Alembic's logging to coexist with the application's logging system
# - Prevents logger conflicts that could interfere with migration completion
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Get database URL from our configuration."""
    from utils.database_config import get_database_url
    return get_database_url()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use sync engine for Alembic (Alembic requires sync operations)
    connectable = get_sync_engine()
    
    # Get backend-specific migration settings
    from utils.database_config import get_backend_type
    from utils.db_backends import get_backend
    
    backend_type = get_backend_type()
    backend = get_backend(backend_type)
    migration_settings = backend.get_migration_settings()
    
    # Apply backend-specific pragmas if needed (e.g., SQLite)
    pragmas = migration_settings.get("pragmas", [])
    if pragmas:
        from sqlalchemy import event
        @event.listens_for(connectable, "connect")
        def set_pragmas(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            for pragma in pragmas:
                try:
                    cursor.execute(pragma)
                except Exception:
                    pass  # Ignore errors for pragmas that may already be set
            cursor.close()

    with connectable.connect() as connection:
        # Get render_as_batch setting from backend (for SQLite compatibility)
        render_as_batch = migration_settings.get("render_as_batch", False)
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=render_as_batch
        )
        
        # Use Alembic's transaction management
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

