"""
Database setup and helper functions for SQLAlchemy.

This module configures the SQLAlchemy engine and session factory
based on the ``DATABASE_URL`` setting. For SQLite, special
``connect_args`` are required to allow usage in a multithreaded
environment (which occurs when using FastAPI with uvicorn). The
``get_db`` dependency yields a database session for each request and
ensures that it is closed after the request is finished.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from ..core.config import settings


# Determine whether to pass special connect arguments for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # Use default engine configuration for other databases
    engine = create_engine(settings.DATABASE_URL)


# Base class for model declarations
Base = declarative_base()


# Session factory configuration. autocommit=False and autoflush=False
# ensure that data is committed manually and flushes occur explicitly.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency that provides a transactional scope around a series of
    operations. Ensures that the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
