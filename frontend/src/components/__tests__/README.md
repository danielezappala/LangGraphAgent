# Frontend Component Tests

This directory contains comprehensive tests for the consolidated frontend components created during the codebase cleanup refactor.

## Test Coverage

### Components Tested

1. **ProviderStatusDisplay** (`provider-status-display.test.tsx`)
   - Tests all three display modes: indicator, alert, and full
   - Verifies proper rendering of different provider states
   - Tests user interactions (navigation, dismissal)
   - Validates connection status icons and badges
   - Ensures proper error handling and loading states

2. **ConversationHistory** (`conversation-history-consolidated.test.tsx`)
   - Tests conversation list rendering and interactions
   - Validates date formatting logic (relative and absolute)
   - Tests debug mode functionality
   - Verifies accessibility features
   - Tests hover effects and delete functionality

### Hooks Tested

1. **useProviderStatus** (`../hooks/__tests__/use-provider-status.test.ts`)
   - Tests data fetching and caching logic
   - Validates error handling scenarios
   - Tests provider actions (test connection, delete, activate)
   - Verifies debouncing and timeout handling
   - Tests cache invalidation and refresh functionality

## Running Tests

To run these tests, you would need to install the required testing dependencies:

```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom
```

Then run tests with:

```bash
npm test
```

## Test Structure

Each test file follows this structure:

1. **Setup and Mocking**: Mock external dependencies (Next.js router, API calls, etc.)
2. **Test Suites**: Organized by functionality (rendering, interactions, error handling)
3. **Assertions**: Comprehensive checks for component behavior and state
4. **Cleanup**: Proper cleanup of mocks and timers

## Key Testing Patterns

### Component Testing
- Mock external dependencies (hooks, router, icons)
- Test different prop combinations and states
- Verify user interactions and event handling
- Check accessibility attributes and structure

### Hook Testing
- Use `renderHook` from React Testing Library
- Mock fetch and external APIs
- Test async operations with proper waiting
- Verify state changes and side effects

### Error Scenarios
- Network failures and timeouts
- Invalid data formats
- Missing required props
- Edge cases and boundary conditions

## Mocking Strategy

### External Dependencies
- **Next.js Router**: Mocked to prevent navigation during tests
- **Lucide Icons**: Replaced with simple div elements for testing
- **API Calls**: Mocked fetch with configurable responses
- **Timers**: Use fake timers for testing debouncing and timeouts

### Component Dependencies
- **Custom Hooks**: Mocked to control return values
- **UI Components**: Use actual components to test integration
- **Config**: Mocked to provide consistent test environment

## Coverage Goals

These tests aim to achieve:
- **Line Coverage**: >90% for tested components
- **Branch Coverage**: >85% for conditional logic
- **Function Coverage**: 100% for public methods
- **Statement Coverage**: >90% overall

## Test Data

Tests use realistic mock data that represents:
- Different provider types (OpenAI, Azure)
- Various connection states (connected, failed, untested)
- Different conversation formats and timestamps
- Error scenarios and edge cases

## Continuous Integration

These tests are designed to run in CI environments with:
- Consistent timing using fake timers
- Deterministic mock data
- Proper cleanup to prevent test interference
- Clear error messages for debugging failures