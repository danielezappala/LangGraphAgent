/**
 * @jest-environment jsdom
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { useProviderStatus } from '../use-provider-status';
import { config } from '@/lib/config';

// Mock the config
jest.mock('@/lib/config', () => ({
  config: {
    apiBaseUrl: 'http://localhost:8000',
  },
}));

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('useProviderStatus', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const mockProviderStatusResponse = {
    has_active_provider: true,
    total_providers: 2,
    configuration_source: 'database',
    issues: [],
  };

  const mockActiveProviderResponse = {
    id: 1,
    name: 'Test OpenAI',
    provider_type: 'openai',
    is_active: true,
    is_from_env: false,
    is_valid: true,
    connection_status: 'connected',
    api_key: 'sk-test',
    model: 'gpt-4',
  };

  const mockProvidersListResponse = [
    mockActiveProviderResponse,
    {
      id: 2,
      name: 'Test Azure',
      provider_type: 'azure',
      is_active: false,
      is_from_env: true,
      is_valid: true,
      connection_status: 'untested',
      api_key: 'azure-key',
      model: 'gpt-4',
      endpoint: 'https://test.openai.azure.com/',
    },
  ];

  const setupSuccessfulFetch = () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProviderStatusResponse),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockActiveProviderResponse),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProvidersListResponse),
      });
  };

  describe('Initial State', () => {
    it('starts with loading state', () => {
      setupSuccessfulFetch();
      
      const { result } = renderHook(() => useProviderStatus());
      
      expect(result.current.isLoading).toBe(true);
      expect(result.current.hasActiveProvider).toBe(false);
      expect(result.current.allProviders).toEqual([]);
    });
  });

  describe('Successful Data Fetching', () => {
    it('fetches and sets provider status correctly', async () => {
      setupSuccessfulFetch();
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.hasActiveProvider).toBe(true);
      expect(result.current.activeProvider).toEqual(mockActiveProviderResponse);
      expect(result.current.allProviders).toEqual(mockProvidersListResponse);
      expect(result.current.totalProviders).toBe(2);
      expect(result.current.configurationSource).toBe('database');
      expect(result.current.configurationIssues).toEqual([]);
      expect(result.current.error).toBeUndefined();
    });

    it('makes correct API calls', async () => {
      setupSuccessfulFetch();
      
      renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(3);
      });
      
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/providers/status');
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/providers/active');
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/providers/list');
    });
  });

  describe('Error Handling', () => {
    it('handles fetch errors gracefully', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.error).toBe('Network error');
      expect(result.current.hasActiveProvider).toBe(false);
    });

    it('handles HTTP errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 500,
      });
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.error).toBe('Failed to fetch provider data');
    });

    it('handles missing active provider gracefully', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ ...mockProviderStatusResponse, has_active_provider: false }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 404,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        });
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.hasActiveProvider).toBe(false);
      expect(result.current.activeProvider).toBeUndefined();
      expect(result.current.error).toBeUndefined();
    });
  });

  describe('Caching', () => {
    it('uses cached data within cache duration', async () => {
      setupSuccessfulFetch();
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      // Clear mock calls
      mockFetch.mockClear();
      
      // Trigger another fetch within cache duration
      act(() => {
        result.current.refreshStatus();
      });
      
      // Should not make new API calls due to caching
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('bypasses cache when force refresh is used', async () => {
      setupSuccessfulFetch();
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      // Setup new fetch responses
      setupSuccessfulFetch();
      
      // Force refresh should bypass cache
      await act(async () => {
        await result.current.refreshStatus();
      });
      
      expect(mockFetch).toHaveBeenCalledTimes(3);
    });
  });

  describe('Provider Actions', () => {
    beforeEach(() => {
      setupSuccessfulFetch();
    });

    it('tests provider connection successfully', async () => {
      const mockTestResponse = {
        success: true,
        message: 'Connection successful',
        response_time_ms: 150,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTestResponse),
      });
      
      // Setup refresh fetch
      setupSuccessfulFetch();
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const testResult = await act(async () => {
        return await result.current.testProviderConnection(1);
      });
      
      expect(testResult.success).toBe(true);
      expect(testResult.message).toBe('Connection successful');
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/providers/1/test',
        { method: 'POST' }
      );
    });

    it('handles connection test failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const testResult = await act(async () => {
        return await result.current.testProviderConnection(1);
      });
      
      expect(testResult.success).toBe(false);
      expect(testResult.message).toBe('Failed to test provider connection');
    });

    it('deletes provider successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
      });
      
      // Setup refresh fetch
      setupSuccessfulFetch();
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const deleteResult = await act(async () => {
        return await result.current.deleteProvider(2);
      });
      
      expect(deleteResult).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/providers/2',
        { method: 'DELETE' }
      );
    });

    it('handles delete provider failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'Cannot delete active provider' }),
      });
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const deleteResult = await act(async () => {
        return await result.current.deleteProvider(1);
      });
      
      expect(deleteResult).toBe(false);
    });

    it('activates provider successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
      });
      
      // Setup refresh fetch
      setupSuccessfulFetch();
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const activateResult = await act(async () => {
        return await result.current.activateProvider(2);
      });
      
      expect(activateResult).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/providers/2/activate',
        { method: 'POST' }
      );
    });
  });

  describe('Timeout Handling', () => {
    it('handles request timeout', async () => {
      // Mock a slow response
      mockFetch.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 15000))
      );
      
      const { result } = renderHook(() => useProviderStatus());
      
      // Fast-forward past timeout
      act(() => {
        jest.advanceTimersByTime(11000);
      });
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.error).toBe('Request timeout');
    });
  });

  describe('Debouncing', () => {
    it('debounces rapid refresh calls', async () => {
      setupSuccessfulFetch();
      
      const { result } = renderHook(() => useProviderStatus());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      // Clear initial fetch calls
      mockFetch.mockClear();
      setupSuccessfulFetch();
      
      // Make multiple rapid refresh calls
      act(() => {
        result.current.refreshStatus();
        result.current.refreshStatus();
        result.current.refreshStatus();
      });
      
      // Fast-forward past debounce delay
      act(() => {
        jest.advanceTimersByTime(600);
      });
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(3);
      });
    });
  });
});