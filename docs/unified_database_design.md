# Unified Database Design

## Overview

This document outlines the design for unifying the current two SQLite databases into a single unified database that maintains compatibility with both the application and LangGraph checkpoint system.

## Current State Analysis

### Database 1: `langgraph_agent.db`
- **Purpose**: Application data (LLM providers)
- **Tables**: 
  - `llm_providers` - LLM provider configurations
  - `alembic_version` - Database migration tracking

### Database 2: `chatbot_memory.sqlite` 
- **Purpose**: LangGraph conversation checkpoints
- **Tables**:
  - `checkpoints` - LangGraph conversation state snapshots
  - `writes` - LangGraph state write operations

## Unified Database Design

### Target Database: `unified_app.sqlite`

The unified database will contain all tables from both databases, maintaining full compatibility with existing code.

### Schema Design

#### Application Tables (from langgraph_agent.db)

```sql
-- LLM Provider configurations
CREATE TABLE llm_providers (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    provider_type VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 0,
    api_key VARCHAR(255) NOT NULL,
    model VARCHAR(100),
    endpoint VARCHAR(255),
    deployment VARCHAR(100), 
    api_version VARCHAR(20),
    is_from_env BOOLEAN NOT NULL DEFAULT 0,
    is_valid BOOLEAN NOT NULL DEFAULT 1,
    validation_errors TEXT,
    last_tested DATETIME,
    connection_status VARCHAR(20) NOT NULL DEFAULT 'untested',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Database migration tracking
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
```

#### LangGraph Tables (from chatbot_memory.sqlite)

```sql
-- LangGraph conversation checkpoints
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BLOB,
    metadata BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- LangGraph state writes
CREATE TABLE writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    type TEXT,
    value BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

#### Indexes

```sql
-- Application indexes
CREATE INDEX ix_llm_providers_id ON llm_providers (id);
CREATE UNIQUE INDEX uix_provider_type_active ON llm_providers (provider_type, is_active);

-- LangGraph indexes (for performance)
CREATE INDEX ix_checkpoints_thread_id ON checkpoints (thread_id);
CREATE INDEX ix_writes_thread_id ON writes (thread_id);
```

## Implementation Strategy

### 1. Database Location
- **Path**: `backend/data/unified_app.sqlite`
- **Rationale**: Keep in data directory for consistency with current structure

### 2. SQLAlchemy Models
Update `database.py` to include both application and LangGraph models:

```python
# Application models (existing)
class DBProvider(Base):
    __tablename__ = "llm_providers"
    # ... existing fields

# LangGraph models (new)
class Checkpoint(Base):
    __tablename__ = "checkpoints"
    # ... LangGraph checkpoint fields

class Write(Base):
    __tablename__ = "writes"  
    # ... LangGraph write fields
```

### 3. LangGraph Adapter
Create `UnifiedAsyncSqliteSaver` class that:
- Implements LangGraph's AsyncSqliteSaver interface
- Uses SQLAlchemy for database operations
- Maintains full compatibility with LangGraph

### 4. Migration Strategy
1. **Backup**: Create backups of existing databases
2. **Create**: Initialize unified database with complete schema
3. **Migrate**: Copy data from both existing databases
4. **Validate**: Ensure data integrity and functionality
5. **Switch**: Update application to use unified database
6. **Cleanup**: Remove old database files after validation

## Benefits

### 1. Simplified Architecture
- Single database file to manage
- Unified backup and maintenance
- Simplified deployment

### 2. Better Performance
- Potential for cross-table queries
- Single connection pool
- Reduced I/O overhead

### 3. Improved Reliability
- Atomic transactions across all data
- Consistent backup strategy
- Single point of truth

### 4. Maintainability
- One database schema to maintain
- Unified migration strategy
- Simplified monitoring

## Compatibility Guarantees

### Application Code
- No changes required to existing SQLAlchemy models
- All existing queries continue to work
- Database URL configuration remains the same

### LangGraph Integration
- Full compatibility with AsyncSqliteSaver interface
- No changes required to LangGraph configuration
- All checkpoint operations continue to work

## Risk Mitigation

### 1. Data Safety
- Complete backup before migration
- Validation scripts to verify data integrity
- Rollback plan if issues occur

### 2. Performance
- Indexes on frequently queried columns
- Connection pooling optimization
- Monitoring for performance regression

### 3. Compatibility
- Comprehensive testing of all functionality
- Adapter pattern for LangGraph integration
- Gradual rollout with fallback options

## Next Steps

1. Implement unified database models
2. Create UnifiedAsyncSqliteSaver adapter
3. Develop migration scripts
4. Test with existing data
5. Deploy and validate