"""
Database compatibility layer.
This module maintains backward compatibility by re-exporting 
everything from the core database system.
"""

# Re-export everything from the core database compatibility layer
from core.database_compat import *

# This ensures existing imports like "from database import get_db" continue to work