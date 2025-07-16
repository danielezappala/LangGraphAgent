// Configuration module for frontend environment variables
// Provides type-safe access to environment variables with proper fallbacks

// Get API base URL with proper fallback logic
function getApiBaseUrl(): string {
  // Try different sources for the API base URL
  const sources = [
    process.env.NEXT_PUBLIC_API_BASE_URL,
    typeof window !== 'undefined' ? (window as any).__NEXT_PUBLIC_API_BASE_URL : undefined,
    'http://localhost:8000' // Default fallback
  ];

  for (const source of sources) {
    if (source && typeof source === 'string' && source.trim()) {
      return source.trim();
    }
  }

  return 'http://localhost:8000';
}

// Export configuration object
export const config = {
  get apiBaseUrl() {
    return getApiBaseUrl();
  }
} as const;

// Validation function (non-blocking)
export function validateEnv() {
  if (typeof window === 'undefined') return; // Skip during SSR

  const apiBaseUrl = getApiBaseUrl();

  // Log configuration status for debugging
  console.log('Frontend configuration loaded:', {
    apiBaseUrl,
    nodeEnv: process.env.NODE_ENV,
    envVars: {
      NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL
    }
  });

  // Only show warning if using fallback in production
  if (apiBaseUrl === 'http://localhost:8000' && process.env.NODE_ENV === 'production') {
    console.warn('Using fallback API base URL in production. Please set NEXT_PUBLIC_API_BASE_URL.');
  }
}

// Initialize validation (non-blocking)
if (typeof window !== 'undefined') {
  // Run validation after a short delay to ensure environment is loaded
  setTimeout(validateEnv, 100);
}

// Make config available globally for debugging
if (typeof window !== 'undefined') {
  (window as any).appConfig = config;
}
