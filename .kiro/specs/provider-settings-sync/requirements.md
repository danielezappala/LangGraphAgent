# Requirements Document

## Introduction

The application currently has a disconnect between the backend LLM provider configuration and the frontend settings interface. While the chatbot functions correctly using the default provider configured in the backend .env file, the frontend settings page shows errors and missing information, creating confusion for users about which provider is actually active and configured.

This feature will establish proper synchronization between backend provider configuration and frontend display, ensuring users have accurate visibility into the current provider status and can manage provider settings effectively.

## Requirements

### Requirement 1

**User Story:** As a user, I want to see the currently active LLM provider clearly displayed in the UI, so that I know which provider is being used for my conversations.

#### Acceptance Criteria

1. WHEN the application loads THEN the frontend SHALL display the currently active provider name from the backend configuration
2. WHEN the backend has a default provider configured THEN the frontend SHALL show this provider as "Active" or "Current"
3. WHEN no provider is properly configured THEN the frontend SHALL display a clear warning message
4. WHEN the provider configuration changes THEN the frontend SHALL update the display without requiring a page refresh

### Requirement 2

**User Story:** As a user, I want to see all available LLM providers loaded in the settings interface, so that I can understand my configuration options.

#### Acceptance Criteria

1. WHEN I navigate to the settings page THEN the system SHALL load and display all configured providers from the backend
2. WHEN providers are loaded THEN each provider SHALL show its configuration status (configured/not configured)
3. WHEN a provider has missing required fields THEN the system SHALL clearly indicate which fields are missing
4. WHEN providers fail to load THEN the system SHALL display a meaningful error message instead of generic errors

### Requirement 3

**User Story:** As a user, I want the settings interface to reflect the actual backend configuration, so that I can trust the information displayed.

#### Acceptance Criteria

1. WHEN the settings page loads THEN it SHALL fetch current provider configurations from the backend API
2. WHEN displaying provider settings THEN the form fields SHALL be populated with actual values from the backend
3. WHEN the backend has environment variables configured THEN these SHALL be reflected in the UI appropriately
4. WHEN there are configuration conflicts THEN the system SHALL clearly indicate the source of truth

### Requirement 4

**User Story:** As a user, I want to be able to save provider settings through the UI, so that I can manage my configuration without editing files directly.

#### Acceptance Criteria

1. WHEN I modify provider settings THEN the system SHALL validate the configuration before saving
2. WHEN I save valid provider settings THEN they SHALL be persisted to the backend
3. WHEN I save provider settings THEN the active provider SHALL be updated if necessary
4. WHEN saving fails THEN the system SHALL display specific error messages about what went wrong

### Requirement 5

**User Story:** As a user, I want the home page alert to accurately reflect the configuration status, so that I'm not confused by false warnings.

#### Acceptance Criteria

1. WHEN all required providers are properly configured THEN no alert SHALL be displayed on the home page
2. WHEN there are missing provider configurations THEN the alert SHALL specify exactly what is missing
3. WHEN the chatbot is working with a default provider THEN the alert SHALL reflect this status accurately
4. WHEN I fix configuration issues THEN the alert SHALL disappear without requiring a page refresh

### Requirement 6

**User Story:** As a user, I want to add new LLM providers to my configuration, so that I can expand my available options.

#### Acceptance Criteria

1. WHEN I click "Add Provider" THEN the system SHALL display a form to configure a new provider
2. WHEN I select a provider type THEN the form SHALL show the appropriate fields for that provider type
3. WHEN I save a new provider THEN it SHALL be added to the available providers list
4. WHEN I add a provider with invalid configuration THEN the system SHALL show validation errors

### Requirement 7

**User Story:** As a user, I want to delete providers I no longer need, so that I can keep my configuration clean.

#### Acceptance Criteria

1. WHEN I select a provider to delete THEN the system SHALL ask for confirmation
2. WHEN I confirm deletion THEN the provider SHALL be removed from the configuration
3. WHEN I try to delete the currently active provider THEN the system SHALL warn me and require selecting a new active provider first
4. WHEN I delete a provider THEN it SHALL be removed from all UI lists immediately

### Requirement 8

**User Story:** As a user, I want to change which provider is currently active, so that I can switch between different LLM services.

#### Acceptance Criteria

1. WHEN I select a different provider as active THEN the system SHALL update the active provider configuration
2. WHEN I change the active provider THEN new chat conversations SHALL use the new provider
3. WHEN I set a provider as active THEN the UI SHALL immediately reflect this change
4. WHEN I try to activate a provider with incomplete configuration THEN the system SHALL prevent the change and show what's missing

### Requirement 9

**User Story:** As a user, I want to see the currently active LLM provider displayed on the homepage, so that I always know which AI service is powering my conversations.

#### Acceptance Criteria

1. WHEN I visit the homepage THEN I SHALL see a clear indicator showing the currently active LLM provider
2. WHEN the active provider is from environment configuration THEN it SHALL be labeled as "Environment" or "Default"
3. WHEN the active provider is from database configuration THEN it SHALL show the custom provider name
4. WHEN I click on the provider indicator THEN I SHALL be able to navigate to the provider settings
5. WHEN the provider changes THEN the homepage indicator SHALL update immediately without page refresh
6. WHEN no provider is configured THEN the indicator SHALL show a warning state with a link to settings

### Requirement 10

**User Story:** As a developer, I want proper error handling for provider API calls, so that users receive helpful feedback when things go wrong.

#### Acceptance Criteria

1. WHEN the frontend cannot connect to the backend provider API THEN it SHALL display a connection error message
2. WHEN the backend provider API returns an error THEN the frontend SHALL display the specific error details
3. WHEN API calls timeout THEN the system SHALL provide appropriate feedback to the user
4. WHEN there are network issues THEN the system SHALL allow users to retry the operation