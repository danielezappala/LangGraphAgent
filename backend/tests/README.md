# Test Suite Organization

This directory contains all tests organized by type and scope.

## Structure

### `/unit/`
Unit tests that test individual components in isolation:
- `test_unified_database.py` - Tests for the unified database system
- `test_unified_server_startup.py` - Tests for server startup process
- `test_azure_openai.py` - Tests for Azure OpenAI integration

### `/integration/`
Integration tests that test multiple components working together:
- `test_integration_final.py` - Complete integration test suite
- `test_e2e_workflows.py` - End-to-end workflow tests
- `test_providers_api.py` - Provider management API tests
- `test_history_api.py` - Chat history API tests
- `test_chat_deletion.py` - Chat deletion functionality tests

### `/performance/`
Performance and load tests:
- `test_performance_validation.py` - Database and API performance validation

## Running Tests

### All tests:
```bash
# From backend directory
python -m pytest tests/ -v
```

### Specific test categories:
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# Performance tests only
python -m pytest tests/performance/ -v
```

### Individual test files:
```bash
# Run specific test file
python tests/unit/test_unified_database.py
```

## Test Requirements

Make sure you have the test dependencies installed:
```bash
pip install pytest pytest-asyncio httpx
```

## Database for Testing

Tests use temporary databases or test-specific database instances to avoid affecting the main application database.