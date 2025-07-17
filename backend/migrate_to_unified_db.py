#!/usr/bin/env python3
"""
Migration script to move data from separate databases to unified database.
This script safely migrates data from langgraph_agent.db and chatbot_memory.sqlite
to the new unified_app.sqlite database.
"""

import os
import shutil
import sqlite3
import pathlib
from datetime import datetime
from typing import List, Tuple, Optional

from unified_database import UnifiedDatabase, get_unified_db
from core.env_loader import EnvironmentLoader

# Load environment
EnvironmentLoader.load_environment()

class DatabaseMigrator:
    """Handles migration from separate databases to unified database."""
    
    def __init__(self):
        self.backend_dir = pathlib.Path(__file__).parent
        self.data_dir = self.backend_dir / "data"
        
        # Source database paths
        self.app_db_path = self.backend_dir / "langgraph_agent.db"
        self.checkpoint_db_path = self.data_dir / "chatbot_memory.sqlite"
        
        # Target unified database
        self.unified_db_path = self.data_dir / "unified_app.sqlite"
        
        # Backup directory
        self.backup_dir = self.data_dir / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Migration setup:")
        print(f"  App DB: {self.app_db_path}")
        print(f"  Checkpoint DB: {self.checkpoint_db_path}")
        print(f"  Unified DB: {self.unified_db_path}")
        print(f"  Backup Dir: {self.backup_dir}")
    
    def backup_existing_databases(self) -> bool:
        """Create backups of existing databases."""
        print("\n=== Creating Backups ===")
        
        try:
            # Backup application database
            if self.app_db_path.exists():
                backup_app_path = self.backup_dir / "langgraph_agent.db"
                shutil.copy2(self.app_db_path, backup_app_path)
                print(f"✅ Backed up app database to: {backup_app_path}")
            else:
                print("⚠️  App database not found - skipping backup")
            
            # Backup checkpoint database
            if self.checkpoint_db_path.exists():
                backup_checkpoint_path = self.backup_dir / "chatbot_memory.sqlite"
                shutil.copy2(self.checkpoint_db_path, backup_checkpoint_path)
                print(f"✅ Backed up checkpoint database to: {backup_checkpoint_path}")
            else:
                print("⚠️  Checkpoint database not found - skipping backup")
            
            # Backup unified database if it exists
            if self.unified_db_path.exists():
                backup_unified_path = self.backup_dir / "unified_app.sqlite.old"
                shutil.copy2(self.unified_db_path, backup_unified_path)
                print(f"✅ Backed up existing unified database to: {backup_unified_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating backups: {e}")
            return False
    
    def migrate_app_data(self, unified_db: UnifiedDatabase) -> bool:
        """Migrate application data from langgraph_agent.db."""
        print("\n=== Migrating Application Data ===")
        
        if not self.app_db_path.exists():
            print("⚠️  App database not found - skipping app data migration")
            return True
        
        try:
            # Connect to source database
            source_conn = sqlite3.connect(str(self.app_db_path))
            source_cursor = source_conn.cursor()
            
            # Get all providers
            source_cursor.execute("SELECT * FROM llm_providers")
            providers = source_cursor.fetchall()
            
            # Get column names
            source_cursor.execute("PRAGMA table_info(llm_providers)")
            columns = [col[1] for col in source_cursor.fetchall()]
            
            print(f"Found {len(providers)} providers to migrate")
            
            # Migrate to unified database
            session = unified_db.get_session()
            try:
                for provider_data in providers:
                    # Create provider dict from row data
                    provider_dict = dict(zip(columns, provider_data))
                    
                    # Create new provider record
                    from unified_database import DBProvider
                    provider = DBProvider(**provider_dict)
                    session.add(provider)
                
                session.commit()
                print(f"✅ Successfully migrated {len(providers)} providers")
                
            except Exception as e:
                session.rollback()
                print(f"❌ Error migrating providers: {e}")
                return False
            finally:
                session.close()
                source_conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error migrating app data: {e}")
            return False
    
    def migrate_checkpoint_data(self, unified_db: UnifiedDatabase) -> bool:
        """Migrate checkpoint data from chatbot_memory.sqlite."""
        print("\n=== Migrating Checkpoint Data ===")
        
        if not self.checkpoint_db_path.exists():
            print("⚠️  Checkpoint database not found - skipping checkpoint migration")
            return True
        
        try:
            # Connect to source database
            source_conn = sqlite3.connect(str(self.checkpoint_db_path))
            source_cursor = source_conn.cursor()
            
            # Migrate checkpoints
            source_cursor.execute("SELECT * FROM checkpoints")
            checkpoints = source_cursor.fetchall()
            
            source_cursor.execute("SELECT * FROM writes")
            writes = source_cursor.fetchall()
            
            print(f"Found {len(checkpoints)} checkpoints and {len(writes)} writes to migrate")
            
            # Migrate to unified database
            session = unified_db.get_session()
            try:
                # Migrate checkpoints
                from unified_database import Checkpoint, Write
                
                for checkpoint_data in checkpoints:
                    checkpoint = Checkpoint(
                        thread_id=checkpoint_data[0],
                        checkpoint_ns=checkpoint_data[1] or '',
                        checkpoint_id=checkpoint_data[2],
                        parent_checkpoint_id=checkpoint_data[3],
                        type=checkpoint_data[4],
                        checkpoint=checkpoint_data[5],
                        checkpoint_metadata=checkpoint_data[6]  # Use correct field name
                    )
                    session.add(checkpoint)
                
                # Migrate writes
                for write_data in writes:
                    write = Write(
                        thread_id=write_data[0],
                        checkpoint_ns=write_data[1] or '',
                        checkpoint_id=write_data[2],
                        task_id=write_data[3],
                        idx=write_data[4],
                        channel=write_data[5],
                        type=write_data[6],
                        value=write_data[7]
                    )
                    session.add(write)
                
                session.commit()
                print(f"✅ Successfully migrated {len(checkpoints)} checkpoints and {len(writes)} writes")
                
            except Exception as e:
                session.rollback()
                print(f"❌ Error migrating checkpoint data: {e}")
                return False
            finally:
                session.close()
                source_conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error migrating checkpoint data: {e}")
            return False
    
    def validate_migration(self, unified_db: UnifiedDatabase) -> bool:
        """Validate that migration was successful."""
        print("\n=== Validating Migration ===")
        
        try:
            session = unified_db.get_session()
            
            # Count records in unified database
            from unified_database import DBProvider, Checkpoint, Write
            
            provider_count = session.query(DBProvider).count()
            checkpoint_count = session.query(Checkpoint).count()
            write_count = session.query(Write).count()
            
            print(f"Unified database contains:")
            print(f"  - {provider_count} providers")
            print(f"  - {checkpoint_count} checkpoints")
            print(f"  - {write_count} writes")
            
            # Validate against source databases
            validation_passed = True
            
            # Validate app data
            if self.app_db_path.exists():
                source_conn = sqlite3.connect(str(self.app_db_path))
                source_cursor = source_conn.cursor()
                source_cursor.execute("SELECT COUNT(*) FROM llm_providers")
                source_provider_count = source_cursor.fetchone()[0]
                source_conn.close()
                
                if provider_count != source_provider_count:
                    print(f"❌ Provider count mismatch: {provider_count} vs {source_provider_count}")
                    validation_passed = False
                else:
                    print(f"✅ Provider count matches: {provider_count}")
            
            # Validate checkpoint data
            if self.checkpoint_db_path.exists():
                source_conn = sqlite3.connect(str(self.checkpoint_db_path))
                source_cursor = source_conn.cursor()
                
                source_cursor.execute("SELECT COUNT(*) FROM checkpoints")
                source_checkpoint_count = source_cursor.fetchone()[0]
                
                source_cursor.execute("SELECT COUNT(*) FROM writes")
                source_write_count = source_cursor.fetchone()[0]
                
                source_conn.close()
                
                if checkpoint_count != source_checkpoint_count:
                    print(f"❌ Checkpoint count mismatch: {checkpoint_count} vs {source_checkpoint_count}")
                    validation_passed = False
                else:
                    print(f"✅ Checkpoint count matches: {checkpoint_count}")
                
                if write_count != source_write_count:
                    print(f"❌ Write count mismatch: {write_count} vs {source_write_count}")
                    validation_passed = False
                else:
                    print(f"✅ Write count matches: {write_count}")
            
            session.close()
            return validation_passed
            
        except Exception as e:
            print(f"❌ Error validating migration: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process."""
        print("🚀 Starting Database Migration to Unified Database")
        print("=" * 60)
        
        # Step 1: Create backups
        if not self.backup_existing_databases():
            print("❌ Migration failed at backup stage")
            return False
        
        # Step 2: Initialize unified database
        print("\n=== Initializing Unified Database ===")
        try:
            # Remove existing unified database if it exists
            if self.unified_db_path.exists():
                self.unified_db_path.unlink()
                print("🗑️  Removed existing unified database")
            
            unified_db = UnifiedDatabase(str(self.unified_db_path))
            print("✅ Unified database initialized")
        except Exception as e:
            print(f"❌ Error initializing unified database: {e}")
            return False
        
        # Step 3: Migrate application data
        if not self.migrate_app_data(unified_db):
            print("❌ Migration failed at app data stage")
            return False
        
        # Step 4: Migrate checkpoint data
        if not self.migrate_checkpoint_data(unified_db):
            print("❌ Migration failed at checkpoint data stage")
            return False
        
        # Step 5: Validate migration
        if not self.validate_migration(unified_db):
            print("❌ Migration validation failed")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 Migration completed successfully!")
        print(f"📁 Backups stored in: {self.backup_dir}")
        print(f"🗄️  Unified database: {self.unified_db_path}")
        
        return True

def main():
    """Main migration function."""
    migrator = DatabaseMigrator()
    
    # Ask for confirmation
    print("\nThis will migrate your databases to a unified structure.")
    print("Backups will be created automatically.")
    
    response = input("\nProceed with migration? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Migration cancelled.")
        return
    
    # Run migration
    success = migrator.run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now update your application to use the unified database.")
    else:
        print("\n❌ Migration failed!")
        print("Check the error messages above and restore from backups if needed.")

if __name__ == "__main__":
    main()