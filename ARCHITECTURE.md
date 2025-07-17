# LangGraph Agent - Simplified Architecture

## Overview

This document describes the simplified and consolidated architecture after the codebase cleanup and refactoring process completed in January 2025.

## Architecture Principles

### Database-First Approach
- **Single Source of Truth**: All provider configurations are stored in the database
- **Environment Variables**: Used only for initial bootstrap and fallback
- **Dynamic Configuration**: Providers can be managed through the UI without server restarts

### Centralized Configuration
- **Single .env File**: All environment variables consolidated in root `.env`
- **EnvironmentLoader**: Centralized environment variable loading with consistent override logic
- **No Duplicate Config**: Removed legacy configuration systems and duplicate files

### Service Consolidation
- **ProviderService**: Primary manager for all provider operations (CRUD, validation, testing)
- **BootstrapService**: Handles initial setup and environment import
- **Removed ConfigService**: Functionality consolidated into ProviderService

## Directory Structure

```
├── .env                          # Consolidated environment configuration
├── backend/
│   ├── core/
│   │   └── env_loader.py        # Centralized environment loading
│   ├── services/
│   │   ├── provider_service.py  # Primary provider management
│   │   └── bootstrap_service.py # Initial setup and bootstrap
│   ├── api/
│   │   ├── providers.py         # Consolidated provider API endpoints
│   │   ├── history.py          # Chat history management
│   │   ├── chat.py             # Chat functionality
│   │   └── ping.py             # Health check
│   ├── database.py             # Database models and connection
│   ├── server.py               # FastAPI application
│   └── tools.py                # LangChain tools
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── provider-status-display.tsx    # Unified provider status
│   │   │   ├── conversation-history-consolidated.tsx # Unified history
│   │   │   └── llm-provider-settings.tsx      # Provider management UI
│   │   ├── hooks/
│   │   │   └── use-provider-status.ts         # Enhanced provider hook
│   │   └── app/
│   │       ├── page.tsx                       # Main application
│   │       └── settings/page.tsx              # Settings page
│   └── package.json            # Cleaned dependencies
```

## Key Components

### Backend Services

#### ProviderService (`backend/services/provider_service.py`)
- **Primary Responsibility**: All provider CRUD operations
- **Key Methods**:
  - `list_all_providers()`: Get all providers from database
  - `get_active_provider()`: Get currently active provider
  - `create_provider()`: Add new provider
  - `update_provider()`: Update existing provider
  - `delete_provider()`: Remove provider
  - `set_active_provider()`: Activate a provider
  - `test_provider_connection()`: Test provider connectivity
  - `validate_provider_config()`: Validate provider configuration

#### BootstrapService (`backend/services/bootstrap_service.py`)
- **Primary Responsibility**: Initial setup and environment import
- **Key Methods**:
  - `run_bootstrap_if_needed()`: Run bootstrap on first startup
  - `import_env_to_database()`: Import .env config to database
  - `create_default_providers()`: Create default provider entries

#### EnvironmentLoader (`backend/core/env_loader.py`)
- **Primary Responsibility**: Centralized environment variable loading
- **Key Methods**:
  - `load_environment()`: Load environment with proper precedence
  - `get_database_url()`: Get database connection string
  - `get_api_config()`: Get API server configuration
  - `get_llm_provider()`: Get active LLM provider type
  - `get_openai_config()`: Get OpenAI configuration
  - `get_azure_config()`: Get Azure OpenAI configuration

### Frontend Components

#### ProviderStatusDisplay (`frontend/src/components/provider-status-display.tsx`)
- **Unified Component**: Replaces separate indicator and alert components
- **Modes**: 
  - `indicator`: Always show current status
  - `alert`: Show only when there are issues
  - `full`: Show both indicator and alert

#### ConversationHistory (`frontend/src/components/conversation-history-consolidated.tsx`)
- **Unified Component**: Replaces separate normal and debug components
- **Features**: 
  - Sophisticated date formatting
  - Optional debug mode
  - Delete functionality

#### useProviderStatus (`frontend/src/hooks/use-provider-status.ts`)
- **Enhanced Hook**: Consolidated provider state management
- **Features**:
  - Intelligent caching (30 seconds)
  - Request debouncing (500ms)
  - Timeout handling (10 seconds)
  - Automatic refresh after operations

## API Endpoints

### Provider Management (`/api/providers`)
- `GET /status` - Get overall provider status
- `GET /list` - List all providers
- `GET /active` - Get active provider
- `POST /add` - Add new provider
- `PUT /{id}` - Update provider
- `DELETE /{id}` - Delete provider
- `POST /{id}/activate` - Activate provider
- `POST /{id}/test` - Test provider connection

### Chat History (`/api/history`)
- `GET /` - List conversations
- `GET /{thread_id}` - Get conversation details
- `DELETE /{thread_id}` - Delete conversation

### Other Endpoints
- `GET /api/version` - Get backend version
- `GET /api/ping` - Health check
- `POST /api/chat` - Chat with agent

## Configuration

### Environment Variables (.env)
```bash
# Port configurations
BACKEND_PORT=8000
FRONTEND_PORT=9002

# Frontend configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# LLM Provider Configuration
LLM_PROVIDER=azure  # or openai

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.0

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# External API Keys
TAVILY_API_KEY=your_tavily_key
NOTION_API_KEY=your_notion_key
```

## Database Schema

### llm_providers Table
- `id`: Primary key
- `name`: Provider display name
- `provider_type`: 'openai' or 'azure'
- `api_key`: API key for the provider
- `model`: Model name
- `endpoint`: API endpoint (Azure only)
- `deployment`: Deployment name (Azure only)
- `api_version`: API version (Azure only)
- `is_active`: Whether this is the active provider
- `is_from_env`: Whether imported from environment
- `is_valid`: Whether configuration is valid
- `connection_status`: 'connected', 'failed', or 'untested'
- `last_tested`: Last connection test timestamp
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Performance Characteristics

Based on performance validation:

- **API Response Times**: ~2ms average (excellent)
- **Memory Usage**: ~44MB (excellent for Python backend)
- **Database Queries**: <1ms average (excellent)
- **Frontend Bundle**: ~23MB (acceptable for full-featured Next.js app)

## Removed Components

### Backend
- `backend/config.py` - Legacy environment-based configuration
- `backend/api/config.py` - Duplicate API endpoints
- `backend/services/config_service.py` - Functionality moved to ProviderService
- `backend/init_providers.py` - Functionality moved to BootstrapService
- `backend/check_config.py` - Replaced by provider status endpoints

### Frontend
- `frontend/src/components/provider-status-indicator.tsx` - Consolidated
- `frontend/src/components/provider-alert.tsx` - Consolidated
- `frontend/src/components/conversation-history.tsx` - Consolidated
- `frontend/src/components/conversation-history-debug.tsx` - Consolidated
- `frontend/src/components/ui/carousel.tsx` - Unused component
- `frontend/src/components/ui/chart.tsx` - Unused component

### Dependencies
- `@genkit-ai/googleai` and `@genkit-ai/next` - Unused Genkit packages
- `firebase` - Unused Firebase package
- `embla-carousel-react` - Unused carousel package
- `recharts` - Unused charts package

## Migration Benefits

1. **Simplified Architecture**: Fewer files, clearer responsibilities
2. **Better Performance**: Faster API responses, lower memory usage
3. **Easier Maintenance**: Consolidated components, less duplication
4. **Database-First**: Dynamic configuration without server restarts
5. **Cleaner Dependencies**: Removed ~5-6 unused packages
6. **Unified Components**: Less code duplication in frontend
7. **Enhanced Error Handling**: Better validation and error messages
8. **Improved Testing**: Comprehensive test suite for all components

## Development Workflow

1. **Environment Setup**: Single `.env` file in root
2. **Provider Management**: Use UI at `/settings` or API endpoints
3. **Database-First**: All configuration stored in database
4. **Testing**: Use provided test scripts for validation
5. **Deployment**: Standard Next.js + FastAPI deployment

## Testing

The codebase includes comprehensive tests:

- `backend/test_integration_final.py` - Full integration testing
- `backend/test_performance_validation.py` - Performance validation
- `backend/test_providers_api.py` - Provider API testing
- `backend/test_history_api.py` - History API testing
- `backend/tests/test_env_loader.py` - Environment loader unit tests

Run tests with:
```bash
python3 backend/test_integration_final.py
python3 backend/test_performance_validation.py
```