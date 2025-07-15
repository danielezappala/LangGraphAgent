import { LLMProvider } from "@/types/provider";

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:30010'}/api/providers`;

export interface ProviderConfig {
  id: number;
  name: string;
  provider_type: "openai" | "azure";
  is_active: boolean;
  api_key: string;
  model?: string;
  endpoint?: string;
  deployment?: string;
  api_version?: string;
}

export interface CreateProviderData {
  name: string;
  provider_type: "openai" | "azure";
  api_key: string;
  model?: string;
  endpoint?: string;
  deployment?: string;
  api_version?: string;
  is_active?: boolean;
}

export const getActiveProvider = async (): Promise<ProviderConfig> => {
  const response = await fetch(`${API_BASE_URL}/active`);
  if (!response.ok) {
    throw new Error('Failed to fetch active provider');
  }
  return response.json();
};

export const listProviders = async (): Promise<ProviderConfig[]> => {
  const response = await fetch(`${API_BASE_URL}/list`);
  if (!response.ok) {
    throw new Error('Failed to fetch providers');
  }
  return response.json();
};

export const addProvider = async (data: CreateProviderData): Promise<ProviderConfig> => {
  const response = await fetch(`${API_BASE_URL}/add`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error('Failed to add provider');
  }
  
  return response.json();
};

export const switchProvider = async (providerId: number): Promise<ProviderConfig> => {
  const response = await fetch(`${API_BASE_URL}/switch/${providerId}`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error('Failed to switch provider');
  }
  
  return response.json();
};

// Convert between frontend and backend types
export const toLLMProvider = (config: ProviderConfig): LLMProvider => ({
  id: config.id.toString(),
  name: config.name,
  type: config.provider_type,
  isActive: config.is_active,
  config: {
    apiKey: config.api_key,
    model: config.model,
    endpoint: config.endpoint,
    deployment: config.deployment,
    apiVersion: config.api_version,
  },
});

export const fromLLMProvider = (provider: Partial<LLMProvider>): Partial<CreateProviderData> => ({
  name: provider.name || '',
  provider_type: provider.type || 'openai',
  api_key: provider.config?.apiKey || '',
  model: provider.config?.model,
  endpoint: provider.config?.endpoint,
  deployment: provider.config?.deployment,
  api_version: provider.config?.apiVersion,
  is_active: provider.isActive,
});
