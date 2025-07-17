/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { ProviderStatusDisplay } from '../provider-status-display';
import { useProviderStatus } from '@/hooks/use-provider-status';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock the provider status hook
jest.mock('@/hooks/use-provider-status', () => ({
  useProviderStatus: jest.fn(),
}));

const mockPush = jest.fn();
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
const mockUseProviderStatus = useProviderStatus as jest.MockedFunction<typeof useProviderStatus>;

describe('ProviderStatusDisplay', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRouter.mockReturnValue({
      push: mockPush,
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
    });
  });

  describe('Indicator Mode', () => {
    it('shows loading state', () => {
      mockUseProviderStatus.mockReturnValue({
        activeProvider: undefined,
        hasActiveProvider: false,
        configurationIssues: [],
        isLoading: true,
        error: undefined,
        allProviders: [],
        totalProviders: 0,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="indicator" />);
      
      expect(screen.getByText('Loading provider...')).toBeInTheDocument();
      expect(screen.getByRole('generic')).toHaveClass('animate-pulse');
    });

    it('shows no active provider state', () => {
      mockUseProviderStatus.mockReturnValue({
        activeProvider: undefined,
        hasActiveProvider: false,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [],
        totalProviders: 0,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="indicator" />);
      
      expect(screen.getByText('No Active Provider')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /configure/i })).toBeInTheDocument();
    });

    it('shows active OpenAI provider', () => {
      const mockProvider = {
        id: 1,
        name: 'Test OpenAI',
        provider_type: 'openai' as const,
        is_active: true,
        is_from_env: false,
        is_valid: true,
        connection_status: 'connected' as const,
        api_key: 'sk-test',
        model: 'gpt-4',
      };

      mockUseProviderStatus.mockReturnValue({
        activeProvider: mockProvider,
        hasActiveProvider: true,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [mockProvider],
        totalProviders: 1,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="indicator" />);
      
      expect(screen.getByText('Test OpenAI')).toBeInTheDocument();
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Active AI Provider • gpt-4')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /manage/i })).toBeInTheDocument();
    });

    it('shows active Azure provider with environment badge', () => {
      const mockProvider = {
        id: 2,
        name: 'Test Azure',
        provider_type: 'azure' as const,
        is_active: true,
        is_from_env: true,
        is_valid: true,
        connection_status: 'connected' as const,
        api_key: 'azure-key',
        model: 'gpt-4',
        endpoint: 'https://test.openai.azure.com/',
        deployment: 'gpt-4',
      };

      mockUseProviderStatus.mockReturnValue({
        activeProvider: mockProvider,
        hasActiveProvider: true,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [mockProvider],
        totalProviders: 1,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="indicator" />);
      
      expect(screen.getByText('Test Azure')).toBeInTheDocument();
      expect(screen.getByText('Azure OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Environment')).toBeInTheDocument();
    });

    it('navigates to settings when configure button is clicked', () => {
      mockUseProviderStatus.mockReturnValue({
        activeProvider: undefined,
        hasActiveProvider: false,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [],
        totalProviders: 0,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="indicator" />);
      
      fireEvent.click(screen.getByRole('button', { name: /configure/i }));
      expect(mockPush).toHaveBeenCalledWith('/settings');
    });
  });

  describe('Alert Mode', () => {
    it('does not render when no issues exist', () => {
      mockUseProviderStatus.mockReturnValue({
        activeProvider: {
          id: 1,
          name: 'Test Provider',
          provider_type: 'openai',
          is_active: true,
          is_from_env: false,
          is_valid: true,
          connection_status: 'connected',
          api_key: 'sk-test',
        },
        hasActiveProvider: true,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [],
        totalProviders: 1,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      const { container } = render(<ProviderStatusDisplay mode="alert" />);
      expect(container.firstChild).toBeNull();
    });

    it('shows alert when no active provider', () => {
      mockUseProviderStatus.mockReturnValue({
        activeProvider: undefined,
        hasActiveProvider: false,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [],
        totalProviders: 0,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="alert" />);
      
      expect(screen.getByText(/No active LLM provider configured/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /fix settings/i })).toBeInTheDocument();
    });

    it('shows alert with configuration issues', () => {
      mockUseProviderStatus.mockReturnValue({
        activeProvider: {
          id: 1,
          name: 'Test Provider',
          provider_type: 'openai',
          is_active: true,
          is_from_env: false,
          is_valid: false,
          connection_status: 'failed',
          api_key: 'invalid-key',
        },
        hasActiveProvider: true,
        configurationIssues: ['Invalid API key', 'Connection failed'],
        isLoading: false,
        error: undefined,
        allProviders: [],
        totalProviders: 1,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="alert" />);
      
      expect(screen.getByText(/Configuration issues: Invalid API key, Connection failed/)).toBeInTheDocument();
    });

    it('shows alert with error message', () => {
      mockUseProviderStatus.mockReturnValue({
        activeProvider: undefined,
        hasActiveProvider: false,
        configurationIssues: [],
        isLoading: false,
        error: 'Network connection failed',
        allProviders: [],
        totalProviders: 0,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="alert" />);
      
      expect(screen.getByText(/Configuration error: Network connection failed/)).toBeInTheDocument();
    });

    it('can be dismissed', async () => {
      const mockOnDismiss = jest.fn();
      
      mockUseProviderStatus.mockReturnValue({
        activeProvider: undefined,
        hasActiveProvider: false,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [],
        totalProviders: 0,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      const { rerender } = render(
        <ProviderStatusDisplay mode="alert" onDismiss={mockOnDismiss} />
      );
      
      // Click dismiss button
      fireEvent.click(screen.getByRole('button', { name: '' })); // X button
      
      expect(mockOnDismiss).toHaveBeenCalled();
      
      // Component should be hidden after dismiss
      rerender(<ProviderStatusDisplay mode="alert" onDismiss={mockOnDismiss} />);
      
      await waitFor(() => {
        expect(screen.queryByText(/No active LLM provider configured/)).not.toBeInTheDocument();
      });
    });
  });

  describe('Full Mode', () => {
    it('renders both indicator and alert when there are issues', () => {
      mockUseProviderStatus.mockReturnValue({
        activeProvider: undefined,
        hasActiveProvider: false,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [],
        totalProviders: 0,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="full" />);
      
      // Should show both indicator and alert
      expect(screen.getByText('No Active Provider')).toBeInTheDocument();
      expect(screen.getByText(/No active LLM provider configured/)).toBeInTheDocument();
    });

    it('renders only indicator when no issues', () => {
      const mockProvider = {
        id: 1,
        name: 'Test Provider',
        provider_type: 'openai' as const,
        is_active: true,
        is_from_env: false,
        is_valid: true,
        connection_status: 'connected' as const,
        api_key: 'sk-test',
        model: 'gpt-4',
      };

      mockUseProviderStatus.mockReturnValue({
        activeProvider: mockProvider,
        hasActiveProvider: true,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [mockProvider],
        totalProviders: 1,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="full" />);
      
      // Should show indicator but not alert
      expect(screen.getByText('Test Provider')).toBeInTheDocument();
      expect(screen.queryByText(/No active LLM provider configured/)).not.toBeInTheDocument();
    });
  });

  describe('Connection Status Icons', () => {
    it('shows correct icon for connected status', () => {
      const mockProvider = {
        id: 1,
        name: 'Test Provider',
        provider_type: 'openai' as const,
        is_active: true,
        is_from_env: false,
        is_valid: true,
        connection_status: 'connected' as const,
        api_key: 'sk-test',
      };

      mockUseProviderStatus.mockReturnValue({
        activeProvider: mockProvider,
        hasActiveProvider: true,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [mockProvider],
        totalProviders: 1,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="indicator" />);
      
      // Check for green checkmark icon (connected status)
      const icon = screen.getByRole('generic').querySelector('.text-green-500');
      expect(icon).toBeInTheDocument();
    });

    it('shows correct icon for failed status', () => {
      const mockProvider = {
        id: 1,
        name: 'Test Provider',
        provider_type: 'openai' as const,
        is_active: true,
        is_from_env: false,
        is_valid: true,
        connection_status: 'failed' as const,
        api_key: 'sk-test',
      };

      mockUseProviderStatus.mockReturnValue({
        activeProvider: mockProvider,
        hasActiveProvider: true,
        configurationIssues: [],
        isLoading: false,
        error: undefined,
        allProviders: [mockProvider],
        totalProviders: 1,
        configurationSource: 'database',
        refreshStatus: jest.fn(),
        testProviderConnection: jest.fn(),
        deleteProvider: jest.fn(),
        activateProvider: jest.fn(),
      });

      render(<ProviderStatusDisplay mode="indicator" />);
      
      // Check for red X icon (failed status)
      const icon = screen.getByRole('generic').querySelector('.text-red-500');
      expect(icon).toBeInTheDocument();
    });
  });
});