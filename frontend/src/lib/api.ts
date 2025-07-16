/**
 * API service for interacting with the backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * Fetches the current version information from the backend
 * @returns Promise with version information
 */
export const fetchVersion = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/version/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Don't cache the version information
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // If the response has a data field with version info, return that
    if (data && data.data) {
      return data.data;
    }
    
    // Otherwise return the whole response
    return data;
  } catch (error) {
    console.error('Error fetching version:', error);
    // Return a default version object in case of error
    return {
      version: '0.0.0',
      status: 'error',
      message: 'Failed to fetch version information',
      error: error instanceof Error ? error.message : String(error)
    };
  }
};

/**
 * Gets the frontend version from package.json via environment variable
 * @returns Frontend version string (e.g., '0.1.0')
 */
export const getFrontendVersion = (): string => {
  // Get version from environment variable set in next.config.js
  return process.env.APP_VERSION || '0.0.0';
};
