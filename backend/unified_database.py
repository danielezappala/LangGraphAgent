"""
Unified database implementation combining application data and LangGraph checkpoints.
This module provides a single database solution for the entire application.
"""

import pathlib
import json
import pickle
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, AsyncIterator, NamedTuple
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError

# Base class for all models
Base = declarative_base()

# ===== APPLICATION MODELS =====

class DBProvider(Base):
    """LLM Provider configuration - application data."""
    __tablename__ = "llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    provider_type = Column(String(20), nullable=False)  # 'openai' or 'azure'
    is_active = Column(Boolean, default=False, nullable=False)
    
    # Common fields for all providers
    api_key = Column(String(255), nullable=False)
    model = Column(String(100))
    
    # Azure-specific fields
    endpoint = Column(String(255))
    deployment = Column(String(100))
    api_version = Column(String(20))
    
    # Enhanced fields for better functionality
    is_from_env = Column(Boolean, default=False, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    validation_errors = Column(Text)
    last_tested = Column(DateTime)
    connection_status = Column(String(20), default='untested')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Provider(id={self.id}, name='{self.name}', type='{self.provider_type}', active={self.is_active})>"

# ===== LANGGRAPH MODELS =====

class Checkpoint(Base):
    """LangGraph checkpoints - conversation state snapshots."""
    __tablename__ = "checkpoints"
    
    thread_id = Column(String, primary_key=True)
    checkpoint_ns = Column(String, primary_key=True, default='')
    checkpoint_id = Column(String, primary_key=True)
    parent_checkpoint_id = Column(String)
    type = Column(String)
    checkpoint = Column(LargeBinary)  # Serialized checkpoint data
    checkpoint_metadata = Column(LargeBinary)    # Serialized metadata (renamed to avoid conflict)
    
    def __repr__(self) -> str:
        return f"<Checkpoint(thread_id='{self.thread_id}', checkpoint_id='{self.checkpoint_id}')>"

class Write(Base):
    """LangGraph writes - state write operations."""
    __tablename__ = "writes"
    
    thread_id = Column(String, primary_key=True)
    checkpoint_ns = Column(String, primary_key=True, default='')
    checkpoint_id = Column(String, primary_key=True)
    task_id = Column(String, primary_key=True)
    idx = Column(Integer, primary_key=True)
    channel = Column(String)
    type = Column(String)
    value = Column(LargeBinary)  # Serialized value
    
    def __repr__(self) -> str:
        return f"<Write(thread_id='{self.thread_id}', task_id='{self.task_id}', idx={self.idx})>"

# ===== DATABASE CONFIGURATION =====

class UnifiedDatabase:
    """Unified database manager for application and LangGraph data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize unified database.
        
        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            backend_dir = pathlib.Path(__file__).parent
            data_dir = backend_dir / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "unified_app.sqlite")
        
        self.db_path = db_path
        self.db_url = f"sqlite:///{db_path}"
        
        # Create engine with optimized settings for SQLite
        self.engine = create_engine(
            self.db_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,
                # SQLite optimizations
                "isolation_level": None,  # Autocommit mode
            },
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )
        
        # Initialize database
        self.init_db()
    
    def init_db(self):
        """Initialize database by creating all tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            print(f"Unified database initialized at: {self.db_path}")
        except Exception as e:
            print(f"Error initializing unified database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    @asynccontextmanager
    async def get_async_session(self):
        """Get an async database session context manager."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connections."""
        self.SessionLocal.remove()
        self.engine.dispose()

# ===== CHECKPOINT TUPLE =====

class CheckpointTuple(NamedTuple):
    """Named tuple for checkpoint data compatible with LangGraph."""
    config: Dict[str, Any]
    checkpoint: Any
    metadata: Dict[str, Any]
    parent_config: Optional[Dict[str, Any]] = None
    pending_writes: Optional[List[Tuple]] = None

# ===== LANGGRAPH ADAPTER =====

class UnifiedAsyncSqliteSaver:
    """
    Adapter that allows LangGraph to use the unified database.
    Implements the AsyncSqliteSaver interface using SQLAlchemy.
    """
    
    def __init__(self, unified_db: UnifiedDatabase):
        """Initialize with unified database instance."""
        self.unified_db = unified_db
    
    @classmethod
    def from_conn_string(cls, conn_string: str) -> 'UnifiedAsyncSqliteSaver':
        """Factory method compatible with LangGraph.
        
        Args:
            conn_string: Database connection string (file path for SQLite)
        """
        # Extract path from connection string
        if conn_string.startswith("sqlite:///"):
            db_path = conn_string[10:]  # Remove "sqlite:///"
        else:
            db_path = conn_string
        
        unified_db = UnifiedDatabase(db_path)
        return cls(unified_db)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    async def aget_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """Get checkpoint tuple for LangGraph.
        
        Args:
            config: LangGraph configuration containing thread_id
            
        Returns:
            CheckpointTuple with checkpoint and metadata or None if not found
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None
        
        try:
            async with self.unified_db.get_async_session() as session:
                # Get the latest checkpoint for this thread
                checkpoint_record = session.query(Checkpoint).filter(
                    Checkpoint.thread_id == thread_id
                ).order_by(Checkpoint.checkpoint_id.desc()).first()
                
                if not checkpoint_record:
                    return None
                
                # Deserialize checkpoint and metadata
                checkpoint_data = pickle.loads(checkpoint_record.checkpoint) if checkpoint_record.checkpoint else None
                metadata = pickle.loads(checkpoint_record.checkpoint_metadata) if checkpoint_record.checkpoint_metadata else {}
                
                return CheckpointTuple(config=config, checkpoint=checkpoint_data, metadata=metadata, parent_config=None, pending_writes=None)
        
        except Exception as e:
            print(f"Error getting checkpoint tuple: {e}")
            return None
    
    async def aput(self, config: Dict[str, Any], checkpoint: Any, metadata: Dict[str, Any], new_versions: Optional[Dict[str, Any]] = None):
        """Save checkpoint for LangGraph.
        
        Args:
            config: LangGraph configuration containing thread_id
            checkpoint: Checkpoint data to save
            metadata: Metadata to save with checkpoint
            new_versions: Version information (optional, for LangGraph compatibility)
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return
        
        try:
            async with self.unified_db.get_async_session() as session:
                # Generate checkpoint ID (timestamp-based)
                checkpoint_id = str(int(datetime.utcnow().timestamp() * 1000000))
                
                # Serialize data
                checkpoint_blob = pickle.dumps(checkpoint) if checkpoint else None
                metadata_blob = pickle.dumps(metadata) if metadata else None
                
                # Create checkpoint record
                checkpoint_record = Checkpoint(
                    thread_id=thread_id,
                    checkpoint_ns='',  # Default namespace
                    checkpoint_id=checkpoint_id,
                    parent_checkpoint_id=None,  # Could be enhanced to track parent
                    type='checkpoint',
                    checkpoint=checkpoint_blob,
                    checkpoint_metadata=metadata_blob
                )
                
                session.add(checkpoint_record)
                # Session will be committed by context manager
        
        except Exception as e:
            print(f"Error saving checkpoint: {e}")
            raise
    
    async def aput_writes(self, config: Dict[str, Any], writes: List[Tuple], task_id: str):
        """Save writes for LangGraph.
        
        Args:
            config: LangGraph configuration containing thread_id
            writes: List of write operations
            task_id: Task identifier
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return
        
        try:
            async with self.unified_db.get_async_session() as session:
                checkpoint_id = str(int(datetime.utcnow().timestamp() * 1000000))
                
                for idx, (channel, value) in enumerate(writes):
                    write_record = Write(
                        thread_id=thread_id,
                        checkpoint_ns='',
                        checkpoint_id=checkpoint_id,
                        task_id=task_id,
                        idx=idx,
                        channel=channel,
                        type='write',
                        value=pickle.dumps(value) if value else None
                    )
                    session.add(write_record)
                
                # Session will be committed by context manager
        
        except Exception as e:
            print(f"Error saving writes: {e}")
            raise
    
    async def alist(self, config: Dict[str, Any], limit: int = 10, before: Optional[str] = None) -> List[CheckpointTuple]:
        """List checkpoints for a thread.
        
        Args:
            config: LangGraph configuration containing thread_id
            limit: Maximum number of checkpoints to return
            before: Return checkpoints before this checkpoint_id
            
        Returns:
            List of CheckpointTuple objects
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return []
        
        try:
            async with self.unified_db.get_async_session() as session:
                query = session.query(Checkpoint).filter(
                    Checkpoint.thread_id == thread_id
                )
                
                if before:
                    query = query.filter(Checkpoint.checkpoint_id < before)
                
                checkpoints = query.order_by(Checkpoint.checkpoint_id.desc()).limit(limit).all()
                
                result = []
                for checkpoint_record in checkpoints:
                    checkpoint_data = pickle.loads(checkpoint_record.checkpoint) if checkpoint_record.checkpoint else None
                    metadata = pickle.loads(checkpoint_record.checkpoint_metadata) if checkpoint_record.checkpoint_metadata else {}
                    result.append(CheckpointTuple(config=config, checkpoint=checkpoint_data, metadata=metadata, parent_config=None, pending_writes=None))
                
                return result
        
        except Exception as e:
            print(f"Error listing checkpoints: {e}")
            return []
    
    def get_next_version(self, current: Optional[str], channel: str) -> str:
        """Get next version for a channel.
        
        Args:
            current: Current version
            channel: Channel name
            
        Returns:
            Next version string
        """
        # Simple timestamp-based versioning
        return str(int(datetime.utcnow().timestamp() * 1000000))
    
    async def asearch(self, metadata_filter: Dict[str, Any]) -> AsyncIterator[CheckpointTuple]:
        """Search checkpoints by metadata.
        
        Args:
            metadata_filter: Filter criteria for metadata
            
        Yields:
            CheckpointTuple objects matching the filter
        """
        try:
            async with self.unified_db.get_async_session() as session:
                checkpoints = session.query(Checkpoint).all()
                
                for checkpoint_record in checkpoints:
                    try:
                        metadata = pickle.loads(checkpoint_record.checkpoint_metadata) if checkpoint_record.checkpoint_metadata else {}
                        
                        # Simple metadata filtering
                        match = True
                        for key, value in metadata_filter.items():
                            if metadata.get(key) != value:
                                match = False
                                break
                        
                        if match:
                            checkpoint_data = pickle.loads(checkpoint_record.checkpoint) if checkpoint_record.checkpoint else None
                            # For search, we need to reconstruct a config - use a basic one
                            search_config = {"configurable": {"thread_id": checkpoint_record.thread_id}}
                            yield CheckpointTuple(config=search_config, checkpoint=checkpoint_data, metadata=metadata, parent_config=None, pending_writes=None)
                    
                    except Exception as e:
                        print(f"Error processing checkpoint in search: {e}")
                        continue
        
        except Exception as e:
            print(f"Error searching checkpoints: {e}")
            return

# ===== GLOBAL INSTANCE =====

# Global unified database instance
_unified_db: Optional[UnifiedDatabase] = None

def get_unified_db() -> UnifiedDatabase:
    """Get the global unified database instance."""
    global _unified_db
    if _unified_db is None:
        _unified_db = UnifiedDatabase()
    return _unified_db

def get_unified_session() -> Session:
    """Get a session from the unified database."""
    return get_unified_db().get_session()

# Compatibility function for existing code
def get_db() -> Session:
    """Get a database session - compatibility with existing code."""
    session = get_unified_session()
    try:
        yield session
    finally:
        session.close()