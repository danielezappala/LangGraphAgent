"""Database models and session management for the application."""
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from datetime import datetime

# Load environment variables using centralized loader
from core.env_loader import EnvironmentLoader
EnvironmentLoader.load_environment()

# Get the database URL from centralized environment loader
DATABASE_URL = EnvironmentLoader.get_database_url()

# Create a SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create a scoped session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Base class for all models
Base = declarative_base()

def get_db() -> Session:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DBProvider(Base):
    """Database model for LLM providers."""
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
    is_from_env = Column(Boolean, default=False, nullable=False)  # Indicates if loaded from .env
    is_valid = Column(Boolean, default=True, nullable=False)  # Configuration validation status
    validation_errors = Column(Text)  # JSON string of validation errors
    last_tested = Column(DateTime)  # Last connection test timestamp
    connection_status = Column(String(20), default='untested')  # 'connected', 'failed', 'untested'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Provider(id={self.id}, name='{self.name}', type='{self.provider_type}', active={self.is_active})>"

# Create all tables
def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)

# Initialize the database when this module is imported
init_db()
