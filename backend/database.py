"""Database models and session management for the application.

This module now uses the unified database system while maintaining full
compatibility with existing code.
"""

from sqlalchemy.orm import Session
from datetime import datetime

# Import from unified database system
from unified_database import (
    UnifiedDatabase, 
    get_unified_db, 
    get_unified_session,
    DBProvider,  # Re-export for compatibility
    Checkpoint,  # Available for future use
    Write,       # Available for future use
)

# Load environment variables using centralized loader
from core.env_loader import EnvironmentLoader
EnvironmentLoader.load_environment()

# ===== COMPATIBILITY LAYER =====
# These maintain compatibility with existing code

# Legacy engine and session references (for compatibility)
_unified_db = get_unified_db()
engine = _unified_db.engine
SessionLocal = _unified_db.SessionLocal

# Legacy Base reference (for compatibility)
from unified_database import Base

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
    'Checkpoint', 
    'Write',
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
