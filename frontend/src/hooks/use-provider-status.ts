import { useState, useEffect, useCallback } from 'react';
import { config } from '@/lib/config';

export interface ProviderConfig {
  id: number;
  name: string;
  provider_type: 'openai' | 'azure';
  is_active: boolean;
  is_from_env: boolean;
  is_valid: boolean;
  connection_status: 'connected' | 'failed' | 'untested';
  api_key: string;
  model?: string;
  endpoint?: string;
  deployment?: string;
  api_version?: string;
  last_tested?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ProviderStatus {
  hasActiveProvider: boolean;
  activeProvider?: ProviderConfig;
  allProviders: ProviderConfig[];
  configurationIssues: string[];
  isLoading: boolean;
  error?: string;
  totalProviders: number;
  configurationSource: string;
}

export interface UseProviderStatusReturn extends ProviderStatus {
  refreshStatus: () => Promise<void>;
  testProviderConnection: (providerId: number) => Promise<{ success: boolean; message: string }>;
  deleteProvider: (providerId: number) => Promise<boolean>;
  activateProvider: (providerId: number) => Promise<boolean>;
}

export function useProviderStatus(): UseProviderStatusReturn {
  const [status, setStatus] = useState<ProviderStatus>({
    hasActiveProvider: false,
    allProviders: [],
    configurationIssues: [],
    isLoading: true,
    totalProviders: 0,
    configurationSource: 'database'
  });

  const fetchProviderStatus = useCallback(async () => {
    try {
      setStatus(prev => ({ ...prev, isLoading: true, error: undefined }));

      const baseUrl = config.apiBaseUrl;
      
      // Fetch all data in parallel
      const [statusRes, activeRes, listRes] = await Promise.all([
        fetch(`${baseUrl}/api/providers/status`),
        fetch(`${baseUrl}/api/providers/active`).catch(() => null), // Active provider might not exist
        fetch(`${baseUrl}/api/providers/list`)
      ]);

      if (!statusRes.ok || !listRes.ok) {
        throw new Error('Failed to fetch provider data');
      }

      const statusData = await statusRes.json();
      const listData = await listRes.json();
      const activeData = activeRes?.ok ? await activeRes.json() : null;

      setStatus({
        hasActiveProvider: statusData.has_active_provider,
        activeProvider: activeData,
        allProviders: listData,
        configurationIssues: statusData.issues || [],
        isLoading: false,
        totalProviders: statusData.total_providers,
        configurationSource: statusData.configuration_source
      });

    } catch (error) {
      console.error('Error fetching provider status:', error);
      setStatus(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch provider status'
      }));
    }
  }, []);

  const testProviderConnection = useCallback(async (providerId: number): Promise<{ success: boolean; message: string }> => {
    try {
      const baseUrl = config.apiBaseUrl;
      const response = await fetch(`${baseUrl}/api/providers/${providerId}/test`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Failed to test provider connection');
      }

      const result = await response.json();
      
      // Refresh status after test
      await fetchProviderStatus();
      
      return {
        success: result.success,
        message: result.message
      };

    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Connection test failed'
      };
    }
  }, [fetchProviderStatus]);

  const deleteProvider = useCallback(async (providerId: number): Promise<boolean> => {
    try {
      const baseUrl = config.apiBaseUrl;
      const response = await fetch(`${baseUrl}/api/providers/${providerId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete provider');
      }

      // Refresh status after deletion
      await fetchProviderStatus();
      return true;

    } catch (error) {
      console.error('Error deleting provider:', error);
      return false;
    }
  }, [fetchProviderStatus]);

  const activateProvider = useCallback(async (providerId: number): Promise<boolean> => {
    try {
      const baseUrl = config.apiBaseUrl;
      const response = await fetch(`${baseUrl}/api/providers/${providerId}/activate`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to activate provider');
      }

      // Refresh status after activation
      await fetchProviderStatus();
      return true;

    } catch (error) {
      console.error('Error activating provider:', error);
      return false;
    }
  }, [fetchProviderStatus]);

  const refreshStatus = useCallback(async () => {
    await fetchProviderStatus();
  }, [fetchProviderStatus]);

  // Initial fetch
  useEffect(() => {
    fetchProviderStatus();
  }, [fetchProviderStatus]);

  return {
    ...status,
    refreshStatus,
    testProviderConnection,
    deleteProvider,
    activateProvider
  };
}