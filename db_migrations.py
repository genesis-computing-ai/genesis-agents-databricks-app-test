"""
Automatic database migration runner using Alembic.
Runs migrations automatically on application startup.

Note: Alembic requires a synchronous engine, so we create a sync engine
specifically for migrations while the application uses async.
"""
import logging
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, text, create_engine, Engine
from database_config import get_database_url

logger = logging.getLogger(__name__)

# Sync engine for migrations (Alembic requires sync)
_sync_engine: Engine | None = None


def get_sync_engine() -> Engine:
    """Get or create sync engine for Alembic migrations."""
    global _sync_engine
    if _sync_engine is None:
        database_url = get_database_url()
        _sync_engine = create_engine(
            database_url,
            pool_size=5,  # Smaller pool for migrations
            max_overflow=5,
            pool_pre_ping=True,
            echo=False,
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=60000"  # 60 second timeout for index creation
            }
        )
    return _sync_engine

logger = logging.getLogger(__name__)


def run_migrations():
    """
    Run Alembic migrations automatically to bring database schema up to date.
    
    This function:
    1. Checks current database revision
    2. Compares with latest migration
    3. Applies any pending migrations automatically
    
    This is safe to run on every startup - it only applies pending migrations.
    """
    try:
        logger.info("Getting database engine for migrations...")
        engine = get_sync_engine()
        
        # Test database connection first
        logger.info("Testing database connection...")
        try:
            with engine.connect() as test_conn:
                test_conn.execute(text("SELECT 1"))
                test_conn.commit()
            logger.info("Database connection successful")
        except Exception as conn_error:
            logger.error(f"Failed to connect to database: {conn_error}")
            raise
        
        # Check if alembic_version table exists (indicates migrations have been run before)
        logger.info("Checking for existing Alembic version table...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        has_alembic_version = 'alembic_version' in tables
        
        if not has_alembic_version:
            logger.info("No Alembic version table found. This appears to be a fresh database.")
            logger.info("Creating initial migration state...")
        
        # Configure Alembic
        logger.info("Configuring Alembic...")
        alembic_cfg = Config("alembic.ini")
        
        # Get current database revision
        logger.info("Checking current database revision...")
        script = ScriptDirectory.from_config(alembic_cfg)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
            head_rev = script.get_current_head()
        
        logger.info(f"Current revision: {current_rev}, Head revision: {head_rev}")
        
        if current_rev == head_rev:
            logger.info(f"Database schema is up to date (revision: {current_rev})")
            return
        
        if current_rev is None:
            logger.info("No migrations have been applied yet. Applying initial migration...")
        else:
            logger.info(f"Database revision: {current_rev}, Latest revision: {head_rev}")
            logger.info("Applying pending migrations...")
        
        # Run migrations to bring database to latest revision
        logger.info("Starting migration upgrade to head...")
        logger.info("Note: This may take a moment if creating tables...")
        try:
            # Temporarily enable SQL logging to see what's happening
            import logging
            sql_logger = logging.getLogger('sqlalchemy.engine')
            original_level = sql_logger.level
            sql_logger.setLevel(logging.INFO)
            
            command.upgrade(alembic_cfg, "head")
            
            # Restore original logging level
            sql_logger.setLevel(original_level)
            logger.info("Migration upgrade command completed successfully")
        except Exception as upgrade_error:
            logger.error(f"Error during upgrade command: {upgrade_error}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        logger.info("Database migrations completed successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Database error during migration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

