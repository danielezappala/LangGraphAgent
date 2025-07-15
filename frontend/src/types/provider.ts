// Type definitions for LLM Provider configuration

export type ProviderType = 'openai' | 'azure';

export interface ProviderConfig {
  apiKey: string;
  model?: string;
  endpoint?: string;
  deployment?: string;
  apiVersion?: string;
}

export interface LLMProvider {
  id: string;
  name: string;
  type: ProviderType;
  isActive: boolean;
  config: ProviderConfig;
}

export interface ProviderFormData {
  name: string;
  type: ProviderType;
  apiKey: string;
  model?: string;
  endpoint?: string;
  deployment?: string;
  apiVersion?: string;
}

// Default provider configuration
export const defaultProviderConfig: ProviderFormData = {
  name: '',
  type: 'openai',
  apiKey: '',
  model: 'gpt-4',
};

// Validation schema for provider form
export const providerValidation = {
  name: (value: string) => (value.trim() ? null : 'Name is required'),
  apiKey: (value: string) => (value.trim() ? null : 'API Key is required'),
  endpoint: (value: string, type: ProviderType) => 
    type === 'azure' && !value ? 'Endpoint is required for Azure' : null,
  deployment: (value: string, type: ProviderType) =>
    type === 'azure' && !value ? 'Deployment name is required for Azure' : null,
  model: (value: string) => (value ? null : 'Model is required'),
};
