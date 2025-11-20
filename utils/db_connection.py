"""
Database connection management using SQLAlchemy Async.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from .database_config import get_database_config, get_backend_type
from .db_backends import get_backend


# Global async engine instance (created lazily)
_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_engine() -> AsyncEngine:
    """
    Get or create async SQLAlchemy engine instance.
    
    Uses the configured database backend to get backend-specific settings.
    
    Returns:
        SQLAlchemy AsyncEngine instance with connection pooling
    """
    global _async_engine, _async_session_factory
    
    if _async_engine is None:
        # Get backend instance for current configuration
        db_config = get_database_config()
        backend_type = get_backend_type()
        backend = get_backend(backend_type)
        
        # Get async URL from backend
        async_database_url = backend.get_async_url(db_config)
        
        # Get pool configuration from backend
        pool_config = backend.get_pool_config()
        
        # Get connection arguments from backend
        connect_args = backend.get_connect_args()
        
        # Create async engine with backend-specific settings
        _async_engine = create_async_engine(
            async_database_url,
            **pool_config,
            connect_args=connect_args
        )
        
        # Create async session factory
        _async_session_factory = async_sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )
    
    return _async_engine


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    
    Usage:
        async with get_async_session() as session:
            result = await session.execute(select(todos_table))
            await session.commit()
    """
    if _async_session_factory is None:
        get_async_engine()
    
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_async_engine():
    """Close the async database engine and cleanup connections."""
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None

