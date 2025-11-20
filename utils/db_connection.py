"""
Database connection management using SQLAlchemy Async.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from .database_config import get_database_url


# Global async engine instance (created lazily)
_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_engine() -> AsyncEngine:
    """
    Get or create async SQLAlchemy engine instance.
    
    Returns:
        SQLAlchemy AsyncEngine instance with connection pooling
    """
    global _async_engine, _async_session_factory
    
    if _async_engine is None:
        database_url = get_database_url()
        # Convert postgresql:// to postgresql+asyncpg:// for async driver
        async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # Create async engine with connection pooling
        # pool_size=50 as requested, with overflow for peak loads
        _async_engine = create_async_engine(
            async_database_url,
            pool_size=50,  # Increased from 5
            max_overflow=20,  # Additional connections for peak loads
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,  # Set to True for SQL query logging
            connect_args={
                "command_timeout": 30,  # 30 second command timeout
            }
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

