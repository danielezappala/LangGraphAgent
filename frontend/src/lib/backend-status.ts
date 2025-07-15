import { fetchVersion } from './api';

export type BackendStatus = 'connected' | 'inactive' | 'error' | 'checking';

/**
 * Checks the backend status by calling the version endpoint
 * @returns Promise that resolves to the backend status
 */
export const checkBackendStatus = async (): Promise<BackendStatus> => {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:30010';
    const response = await fetch(`${baseUrl}/api/ping`, {
      method: 'GET',
      cache: 'no-store',
      // Add a timeout to avoid hanging if the backend is not responding
      signal: AbortSignal.timeout(2000),
    });

    if (response.ok) {
      return 'connected';
    } else {
      return 'error';
    }
  } catch (error) {
    // Check if the error is a timeout or network error
    if (error instanceof Error && (error.name === 'TimeoutError' || error.name === 'TypeError')) {
      return 'inactive';
    }
    return 'error';
  }
};

/**
 * Gets the status color based on the backend status
 * @param status The backend status
 * @returns Tailwind color class
 */
export const getStatusColor = (status: BackendStatus): string => {
  switch (status) {
    case 'connected':
      return 'bg-green-500';
    case 'inactive':
      return 'bg-gray-400';
    case 'error':
      return 'bg-red-500';
    case 'checking':
      return 'bg-yellow-500 animate-pulse';
    default:
      return 'bg-gray-400';
  }
};

/**
 * Gets the status tooltip text based on the backend status
 * @param status The backend status
 * @returns Tooltip text
 */
export const getStatusTooltip = (status: BackendStatus): string => {
  switch (status) {
    case 'connected':
      return 'Backend connesso';
    case 'inactive':
      return 'Backend non raggiungibile';
    case 'error':
      return 'Errore del backend';
    case 'checking':
      return 'Verifica connessione in corso...';
    default:
      return 'Stato sconosciuto';
  }
};
