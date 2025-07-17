"""
Proposta per database unificato che combina SQLAlchemy e LangGraph checkpoints.
Questo approccio mantiene un singolo database SQLite per tutto.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pathlib

# Percorso unificato del database
UNIFIED_DB_PATH = str(pathlib.Path(__file__).parent / "data" / "unified_app.sqlite")
UNIFIED_DB_URL = f"sqlite:///{UNIFIED_DB_PATH}"

Base = declarative_base()

# ===== TABELLE APPLICAZIONE (SQLAlchemy) =====

class DBProvider(Base):
    """Provider LLM configuration - gestito da SQLAlchemy."""
    __tablename__ = "llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    provider_type = Column(String(20), nullable=False)  # 'openai', 'azure'
    api_key = Column(String(500), nullable=False)
    model = Column(String(100))
    endpoint = Column(String(500))
    deployment = Column(String(100))
    api_version = Column(String(20))
    is_active = Column(Boolean, default=False)
    is_from_env = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True)
    connection_status = Column(String(20), default='untested')
    last_tested = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ===== TABELLE LANGGRAPH (Compatibili) =====

class Checkpoint(Base):
    """Checkpoints LangGraph - compatibile con AsyncSqliteSaver."""
    __tablename__ = "checkpoints"
    
    thread_id = Column(String, primary_key=True)
    checkpoint_ns = Column(String, primary_key=True)
    checkpoint_id = Column(String, primary_key=True)
    parent_checkpoint_id = Column(String)
    type = Column(String)
    checkpoint = Column(LargeBinary)  # Serialized checkpoint data
    metadata = Column(Text)  # JSON metadata

class Write(Base):
    """Writes LangGraph - compatibile con AsyncSqliteSaver."""
    __tablename__ = "writes"
    
    thread_id = Column(String, primary_key=True)
    checkpoint_ns = Column(String, primary_key=True)
    checkpoint_id = Column(String, primary_key=True)
    task_id = Column(String, primary_key=True)
    idx = Column(Integer, primary_key=True)
    channel = Column(String)
    type = Column(String)
    value = Column(LargeBinary)  # Serialized value

# ===== CONFIGURAZIONE =====

def create_unified_engine():
    """Crea engine per database unificato."""
    engine = create_engine(
        UNIFIED_DB_URL,
        connect_args={"check_same_thread": False},  # Per SQLite
        echo=False  # Set True per debug SQL
    )
    return engine

def create_tables(engine):
    """Crea tutte le tabelle nel database unificato."""
    Base.metadata.create_all(bind=engine)

def get_unified_session():
    """Ottieni sessione per database unificato."""
    engine = create_unified_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

# ===== ADAPTER PER LANGGRAPH =====

class UnifiedAsyncSqliteSaver:
    """
    Adapter che permette a LangGraph di usare il database unificato.
    Implementa l'interfaccia di AsyncSqliteSaver ma usa il nostro database.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
    
    @classmethod
    def from_conn_string(cls, conn_string: str):
        """Factory method compatibile con LangGraph."""
        return cls(conn_string)
    
    async def __aenter__(self):
        """Context manager entry."""
        # Assicurati che le tabelle esistano
        create_tables(self.engine)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
    
    # Implementa i metodi richiesti da LangGraph
    async def aget_tuple(self, config):
        """Ottieni checkpoint tuple."""
        # Implementazione che usa SQLAlchemy per leggere dalla tabella checkpoints
        pass
    
    async def aput(self, config, checkpoint, metadata):
        """Salva checkpoint."""
        # Implementazione che usa SQLAlchemy per scrivere nella tabella checkpoints
        pass

# ===== VANTAGGI =====
"""
VANTAGGI di questo approccio:

1. **Database Singolo**: Un solo file SQLite per tutto
2. **Gestione Unificata**: SQLAlchemy per tutto, inclusi i checkpoints
3. **Compatibilità**: LangGraph continua a funzionare tramite adapter
4. **Backup Semplificato**: Un solo file da fare backup
5. **Transazioni Atomiche**: Possibilità di transazioni cross-tabelle
6. **Monitoring Unificato**: Un solo database da monitorare
7. **Deployment Semplificato**: Un solo file database da gestire

SVANTAGGI:
1. **Complessità Iniziale**: Serve implementare l'adapter
2. **Rischio**: Modifiche al formato LangGraph potrebbero richiedere aggiornamenti
3. **Performance**: Potenziale contention su un singolo file (ma SQLite gestisce bene)
"""