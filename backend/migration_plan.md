# Database Migration Plan

## Overview
This document outlines the step-by-step plan for migrating from separate databases to a unified database architecture.

## Current State
- **Application DB**: `backend/langgraph_agent.db` (SQLAlchemy managed)
- **Checkpoint DB**: `backend/data/chatbot_memory.sqlite` (LangGraph managed)

## Target State
- **Unified DB**: `backend/data/unified_app.sqlite` (Single database for everything)

## Migration Steps

### Phase 1: Preparation ✅
1. **Design unified schema** ✅
   - Created `unified_database_design.md`
   - Analyzed existing database structures
   - Designed compatible unified schema

2. **Implement unified database system** ✅
   - Created `unified_database.py` with all models
   - Implemented `UnifiedAsyncSqliteSaver` adapter
   - Created migration script `migrate_to_unified_db.py`

### Phase 2: Migration Execution
3. **Backup existing databases**
   ```bash
   python migrate_to_unified_db.py
   ```
   - Creates timestamped backup directory
   - Copies all existing database files
   - Ensures data safety before migration

4. **Run data migration**
   - Initialize new unified database with complete schema
   - Copy data from `langgraph_agent.db` → `unified_app.sqlite`
   - Copy data from `chatbot_memory.sqlite` → `unified_app.sqlite`
   - Validate data integrity

### Phase 3: Application Updates
5. **Update database configuration**
   - Modify `database.py` to use unified database
   - Update environment loader database URL
   - Ensure all imports point to unified system

6. **Update LangGraph configuration**
   - Replace AsyncSqliteSaver with UnifiedAsyncSqliteSaver
   - Update server.py to use unified database for checkpoints
   - Test LangGraph functionality

### Phase 4: Testing & Validation
7. **Run comprehensive tests**
   - Execute all unit tests
   - Execute all integration tests
   - Verify API functionality
   - Test LangGraph checkpoint operations

8. **Performance validation**
   - Compare response times before/after
   - Monitor database performance
   - Validate memory usage

### Phase 5: Cleanup
9. **Remove old database files**
   - Archive old database files
   - Update backup scripts
   - Clean up unused code

## Detailed Migration Commands

### 1. Pre-migration Backup
```bash
# Manual backup (optional - script does this automatically)
cp backend/langgraph_agent.db backend/data/backup/
cp backend/data/chatbot_memory.sqlite backend/data/backup/
```

### 2. Run Migration Script
```bash
cd backend
python migrate_to_unified_db.py
```

### 3. Verify Migration
```bash
# Check unified database structure
sqlite3 backend/data/unified_app.sqlite ".schema"

# Count records
sqlite3 backend/data/unified_app.sqlite "SELECT COUNT(*) FROM llm_providers;"
sqlite3 backend/data/unified_app.sqlite "SELECT COUNT(*) FROM checkpoints;"
sqlite3 backend/data/unified_app.sqlite "SELECT COUNT(*) FROM writes;"
```

### 4. Test Application
```bash
# Run unit tests
python -m pytest tests/ -v

# Start server and test APIs
python server.py
```

## Rollback Plan

If migration fails or issues are discovered:

### 1. Stop Application
```bash
# Stop any running servers
pkill -f "python server.py"
```

### 2. Restore from Backup
```bash
# Restore original databases
cp backend/data/backup/TIMESTAMP/langgraph_agent.db backend/
cp backend/data/backup/TIMESTAMP/chatbot_memory.sqlite backend/data/
```

### 3. Revert Code Changes
```bash
# If code was updated, revert to use original database.py
git checkout HEAD -- backend/database.py
```

## Risk Assessment

### Low Risk ✅
- **Data Loss**: Comprehensive backup strategy
- **Schema Compatibility**: Identical schema design
- **Application Compatibility**: No API changes required

### Medium Risk ⚠️
- **Performance**: New database structure might have different performance characteristics
- **LangGraph Integration**: Adapter implementation needs thorough testing

### Mitigation Strategies
- **Comprehensive Testing**: Full test suite execution before and after
- **Gradual Rollout**: Test in development environment first
- **Monitoring**: Performance monitoring during initial deployment
- **Quick Rollback**: Automated rollback procedures

## Success Criteria

### ✅ Migration Successful When:
1. All data migrated without loss
2. All unit tests pass (54/54)
3. All integration tests pass (14/15 - same as baseline)
4. API response times within 10% of baseline
5. LangGraph checkpoint operations work correctly
6. No errors in application logs

### 📊 Metrics to Monitor:
- Database file size (should be sum of original files)
- API response times
- Memory usage
- Error rates
- Test pass rates

## Post-Migration Benefits

### Immediate Benefits
- **Single Database File**: Easier backup and deployment
- **Unified Transactions**: Atomic operations across all data
- **Simplified Architecture**: One database connection to manage

### Long-term Benefits
- **Better Performance**: Potential for cross-table optimizations
- **Easier Maintenance**: Single schema to maintain
- **Improved Monitoring**: One database to monitor
- **Simplified Scaling**: Single database scaling strategy

## Timeline

### Estimated Duration: 2-3 hours
- **Preparation**: 30 minutes (already complete)
- **Migration Execution**: 30 minutes
- **Testing & Validation**: 60-90 minutes
- **Cleanup**: 30 minutes

### Dependencies
- ✅ Unified database implementation complete
- ✅ Migration script ready
- ✅ Test baseline established
- 🔄 Application server stopped during migration
- 🔄 No active users during migration window