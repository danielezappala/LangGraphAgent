# Implementation Plan

- [x] 1. Create backend configuration and provider services
  - Implement ConfigService to handle .env and database synchronization
  - Implement ProviderService for CRUD operations and provider management
  - Add configuration validation and provider connection testing logic
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2_

- [x] 2. Enhance database model and add missing API endpoints
  - Add missing fields to DBProvider model (is_from_env, validation status)
  - Implement DELETE endpoint for provider deletion
  - Add provider activation endpoint and connection testing endpoint
  - Add provider status endpoint for overall configuration status
  - _Requirements: 7.1, 7.2, 8.1, 8.2, 6.1_

- [x] 3. Fix frontend API configuration and error handling
  - Fix NEXT_PUBLIC_API_BASE_URL configuration issue causing API failures
  - Implement proper error handling for API calls with specific error messages
  - Add retry logic and timeout handling for network issues
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 4. Create provider status hook and enhance settings component
  - Implement useProviderStatus hook for real-time provider status
  - Enhance LLMProviderSettings component with proper data loading and error states
  - Add provider deletion functionality with confirmation dialogs
  - Add provider activation controls and connection testing UI
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 6.2, 7.3, 8.3_

- [x] 5. Implement provider alert component and status indicator for home page
  - Create ProviderAlert component to replace generic configuration warnings
  - Create ProviderStatusIndicator component to show active provider on homepage
  - Integrate with provider status to show accurate configuration state
  - Add navigation to settings and dismiss functionality
  - Update home page to use new alert and status indicator components
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 6. Implement Database-First bootstrap and simplify configuration logic
  - Create BootstrapService for one-time .env import to database
  - Simplify ConfigService to read only from database (remove mixed mode)
  - Add startup logic to detect first run and import .env automatically
  - Update all services to use database as single source of truth
  - _Requirements: 3.4, 4.3, 1.4_

- [ ] 7. Implement comprehensive testing and validation
  - Add unit tests for ConfigService and ProviderService
  - Add integration tests for API endpoints and database operations
  - Add frontend component tests for settings and alert components
  - Add end-to-end tests for provider management workflow
  - _Requirements: 4.4, 2.3, 2.4_