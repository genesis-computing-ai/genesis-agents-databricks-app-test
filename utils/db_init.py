"""
Database initialization module with automatic migrations.
"""
import logging
from sqlalchemy.exc import SQLAlchemyError
from .db_migrations import run_migrations

logger = logging.getLogger(__name__)


async def init_database():
    """
    Initialize database and run automatic migrations.
    
    This function:
    1. Checks if alembic_version table exists
    2. If yes, runs Alembic migrations to apply schema changes
    3. If no, creates tables using create_all() (faster for fresh databases)
    
    This ensures the database schema is always up to date with the code.
    
    Note: Alembic migrations run synchronously (Alembic requires sync engine).
    We run them in a thread pool to avoid blocking the event loop.
    """
    try:
        import asyncio
        logger.info("Initializing database...")
        
        # Run migrations in thread pool since Alembic requires sync operations
        # This prevents blocking the async event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_migrations)
        
        logger.info("Database initialization complete")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise

