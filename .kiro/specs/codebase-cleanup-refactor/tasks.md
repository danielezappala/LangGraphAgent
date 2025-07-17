# Implementation Plan

## Phase 1: Backend Cleanup (Low Risk)

- [x] 1. Remove redundant test and development files
  - Delete unused test server files (test_server*.py, simple_server*.py)
  - Remove development utilities (test_bind.py, socket_test.py)
  - Clean up duplicate Azure test files
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.1 Delete redundant test server files
  - Remove backend/test_server.py, backend/test_server_30001.py, backend/test_server_8080.py, backend/test_server_high_port.py
  - Remove backend/simple_http_server.py, backend/simple_server_30010.py
  - Verify no imports or references to these files exist
  - _Requirements: 1.1, 1.2_

- [x] 1.2 Remove development utility files
  - Delete backend/test_bind.py and backend/socket_test.py
  - Remove backend/test_azure_connection.py (keep test_azure_openai.py as it's more comprehensive)
  - Clean up any references to deleted files
  - _Requirements: 1.3, 1.4_

- [x] 1.3 Create centralized environment loader
  - Create backend/core/env_loader.py with EnvironmentLoader class
  - Implement load_environment(), get_database_url(), get_api_config() methods
  - Add proper error handling and logging
  - Write unit tests for environment loading logic
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 1.4 Replace environment loading across codebase
  - Update backend/server.py to use centralized env loader
  - Update backend/run.py to use centralized env loader
  - Update backend/tools.py to use centralized env loader
  - Remove duplicate load_dotenv() calls from all files
  - _Requirements: 2.1, 2.4, 2.5_

- [x] 1.5 Clean up unused imports in backend files
  - Remove unused imports from all Python files
  - Fix any linting warnings about unused variables
  - Ensure all remaining imports are actually used
  - _Requirements: 9.1, 9.2, 9.3_

## Phase 2: Service Consolidation (Medium Risk)

- [ ] 2. Consolidate backend services with clear boundaries
  - Enhance ProviderService to handle all provider operations
  - Remove redundant initialization logic from init_providers.py
  - Consolidate validation logic in ConfigService
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 2.1 Enhance ProviderService as primary provider manager
  - Move all provider CRUD operations to ProviderService
  - Add comprehensive provider validation to ProviderService
  - Implement connection testing logic in ProviderService
  - Remove duplicate provider management code from other services
  - _Requirements: 6.1, 6.4_

- [ ] 2.2 Consolidate provider initialization logic
  - Move initialization logic from init_providers.py to BootstrapService
  - Remove backend/init_providers.py file
  - Update BootstrapService to handle all provider setup scenarios
  - Ensure first-time setup works correctly with consolidated logic
  - _Requirements: 6.2, 6.3_

- [ ] 2.3 Streamline ConfigService responsibilities
  - Focus ConfigService on validation and status reporting only
  - Remove CRUD operations from ConfigService (move to ProviderService)
  - Consolidate all validation logic in ConfigService
  - Update service dependencies to reflect new boundaries
  - _Requirements: 6.1, 6.4, 6.5_

- [ ] 2.4 Consolidate database files
  - Identify and merge any duplicate database content
  - Standardize on backend/langgraph_agent.db for main application data
  - Keep backend/data/chatbot_memory.sqlite for conversation checkpoints
  - Remove any duplicate database files from root directory
  - Update all database connection strings to use consolidated files
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

## Phase 3: API Consolidation (Medium Risk)

- [ ] 3. Remove duplicate API endpoints and consolidate provider APIs
  - Remove backend/api/config.py entirely
  - Consolidate all provider functionality in backend/api/providers.py
  - Update API routing in server.py
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3.1 Remove legacy config API endpoints
  - Delete backend/api/config.py file
  - Remove config router import and inclusion from server.py
  - Verify no frontend components are calling /api/config endpoints
  - _Requirements: 4.2, 4.4_

- [ ] 3.2 Consolidate provider API endpoints
  - Ensure all provider operations are available through /api/providers
  - Remove any duplicate endpoint logic
  - Standardize response formats across all provider endpoints
  - Add comprehensive error handling to consolidated endpoints
  - _Requirements: 4.1, 4.3, 4.5_

- [ ] 3.3 Update API documentation and testing
  - Update API documentation to reflect consolidated endpoints
  - Remove references to deleted /api/config endpoints
  - Test all provider API endpoints for functionality
  - Verify error handling works correctly for all scenarios
  - _Requirements: 4.4, 4.5_

## Phase 4: Frontend Consolidation (Low Risk)

- [ ] 4. Merge redundant React components and clean up dependencies
  - Consolidate provider status components into unified component
  - Merge conversation history components
  - Remove unused frontend dependencies
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 4.1 Create unified provider status component
  - Create new ProviderStatusDisplay component that handles indicator, alert, and full modes
  - Migrate functionality from provider-status-indicator.tsx and provider-alert.tsx
  - Update all components that use provider status to use unified component
  - Remove old provider-status-indicator.tsx and provider-alert.tsx files
  - _Requirements: 5.1, 5.4, 5.5_

- [ ] 4.2 Consolidate conversation history components
  - Merge conversation-history.tsx and conversation-history-debug.tsx into single component
  - Add debugMode prop to control debug functionality
  - Update components that use conversation history to use consolidated component
  - Remove duplicate conversation-history-debug.tsx file
  - _Requirements: 5.2, 5.4, 5.5_

- [ ] 4.3 Clean up provider status hook
  - Consolidate all provider-related state management in useProviderStatus hook
  - Remove duplicate logic across components
  - Add proper error handling and caching to the hook
  - Update all components to use the enhanced hook
  - _Requirements: 5.3, 5.4, 5.5_

- [ ] 4.4 Remove unused frontend dependencies
  - Remove @genkit-ai/googleai and @genkit-ai/next packages
  - Remove firebase package
  - Remove embla-carousel-react and recharts packages
  - Remove other unused dependencies identified in package.json
  - Update package-lock.json and verify build still works
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 4.5 Clean up unused imports in frontend components
  - Remove unused React hooks imports (useState, useEffect where not used)
  - Remove unused Lucide icon imports
  - Remove unused utility imports
  - Fix any TypeScript warnings about unused variables
  - _Requirements: 9.1, 9.4, 9.5_

## Phase 5: Configuration Cleanup (High Risk)

- [ ] 5. Remove legacy configuration system and finalize consolidation
  - Remove legacy env-based configuration system
  - Clean up configuration file structure
  - Final testing and validation
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 5.1 Remove legacy configuration system
  - Remove backend/config.py file (legacy env-based config)
  - Update any remaining imports of config.py to use database-first approach
  - Remove check_config.py utility (replaced by provider status endpoints)
  - Verify all configuration now flows through database system
  - _Requirements: 3.2, 3.3, 3.5_

- [ ] 5.2 Consolidate configuration files
  - Standardize on single .env file in root directory
  - Remove duplicate .env files from backend and frontend directories
  - Update documentation to reflect simplified configuration structure
  - Ensure environment loading works correctly with consolidated files
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 5.3 Final integration testing
  - Test complete provider management workflow (add, edit, delete, activate)
  - Test provider connection testing functionality
  - Test conversation functionality with consolidated components
  - Verify all API endpoints work correctly
  - _Requirements: 3.4, 4.5, 5.5_

- [ ] 5.4 Performance validation
  - Measure frontend bundle size reduction
  - Verify API response times are maintained or improved
  - Check memory usage of backend services
  - Validate database query performance
  - _Requirements: All requirements - performance impact_

- [ ] 5.5 Final cleanup and documentation
  - Remove any remaining unused files or code
  - Update README and documentation to reflect changes
  - Create migration guide for developers
  - Document new simplified architecture
  - _Requirements: All requirements - documentation and cleanup_

## Testing and Validation Tasks

- [ ] 6. Comprehensive testing after each phase
  - Unit tests for all consolidated components
  - Integration tests for API endpoints
  - End-to-end tests for user workflows
  - _Requirements: All requirements - testing validation_

- [ ] 6.1 Create unit tests for consolidated backend services
  - Write tests for centralized environment loader
  - Write tests for consolidated ProviderService
  - Write tests for streamlined ConfigService and BootstrapService
  - Ensure all service boundaries are properly tested
  - _Requirements: 2.5, 6.5_

- [ ] 6.2 Create integration tests for consolidated APIs
  - Test all /api/providers endpoints
  - Test error handling and edge cases
  - Test provider connection testing functionality
  - Verify API responses match expected formats
  - _Requirements: 4.5_

- [ ] 6.3 Create frontend component tests
  - Test unified provider status component in all modes
  - Test consolidated conversation history component
  - Test provider status hook functionality
  - Verify all user interactions work correctly
  - _Requirements: 5.5_

- [ ] 6.4 End-to-end workflow testing
  - Test complete provider setup workflow
  - Test provider switching and management
  - Test conversation functionality with new components
  - Test error scenarios and recovery
  - _Requirements: All requirements - end-to-end validation_