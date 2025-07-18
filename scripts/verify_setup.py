#!/usr/bin/env python3
"""
Script di verifica per controllare che la nuova struttura organizzata funzioni correttamente.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test che tutti gli import principali funzionino."""
    print("🧪 Testing imports...")
    
    try:
        # Test core database import
        from core.database.unified_database import get_unified_db, UnifiedAsyncSqliteSaver, DBProvider
        print("✅ Core database import successful")
        
        # Test core langgraph import
        from core.langgraph.graph_definition import build_graph
        print("✅ Core langgraph import successful")
        
        # Test core tools import
        from core.tools.tools import search_web
        print("✅ Core tools import successful")
        
        # Test compatibility layer
        from database import get_db, SessionLocal
        print("✅ Database compatibility layer import successful")
        
        # Test services
        from services.provider_service import get_provider_service
        from services.bootstrap_service import get_bootstrap_service
        print("✅ Services import successful")
        
        # Test API modules
        from api.providers import router as providers_router
        from api.history import router as history_router
        print("✅ API modules import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_connection():
    """Test connessione al database."""
    print("\n🗄️ Testing database connection...")
    
    try:
        from core.database.unified_database import get_unified_db
        
        db = get_unified_db()
        print(f"✅ Database connection successful: {db.db_path}")
        
        # Test basic query
        with db.get_session() as session:
            from core.database.unified_database import DBProvider
            providers = session.query(DBProvider).count()
            print(f"✅ Database query successful: {providers} providers found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_server_startup():
    """Test che il server si avvii senza errori."""
    print("\n🚀 Testing server startup...")
    
    try:
        from app import app
        print("✅ Server module import successful")
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

def main():
    """Esegue tutti i test di verifica."""
    print("🔍 Verifying organized project structure...")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test database
    if not test_database_connection():
        success = False
    
    # Test server
    if not test_server_startup():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All verification tests passed!")
        print("✅ The organized project structure is working correctly.")
    else:
        print("💥 Some verification tests failed.")
        print("❌ Please check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())