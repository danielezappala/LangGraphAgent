"""Database models and session management for the application.

This module provides a compatibility layer for the unified database system.
All database operations now use the unified database while maintaining
backward compatibility with existing code.
"""

from sqlalchemy.orm import Session

# Import from unified database system
from core.database.unified_database import (
    get_unified_db, 
    get_unified_session,
    DBProvider,  # Re-export for compatibility
    Base,        # Re-export for compatibility
)

# Load environment variables using centralized loader
from core.env_loader import EnvironmentLoader
EnvironmentLoader.load_environment()

# ===== COMPATIBILITY LAYER =====
# These maintain compatibility with existing code

# Get unified database instance
_unified_db = get_unified_db()
engine = _unified_db.engine
SessionLocal = _unified_db.SessionLocal

def get_db() -> Session:
    """Get a database session - maintains compatibility with existing code."""
    session = get_unified_session()
    try:
        yield session
    finally:
        session.close()

def init_db():
    """Initialize the database by creating all tables - compatibility function."""
    # The unified database handles initialization automatically
    print("Database initialization handled by unified database system")

# ===== EXPORTS =====
# Export everything that existing code expects

__all__ = [
    'DBProvider',
    'Base',
    'engine',
    'SessionLocal',
    'get_db',
    'init_db',
    'get_unified_db',
    'get_unified_session',
]

# Initialize database (compatibility)
init_db()