// Load environment variables from both root and frontend .env files
const { config: loadEnvConfig } = require('dotenv');
const path = require('path');

// Load environment variables
loadEnvConfig({ path: path.resolve(process.cwd(), '../.env') });
loadEnvConfig({ path: path.resolve(process.cwd(), '.env') });
loadEnvConfig({ path: path.resolve(process.cwd(), '.env.local') });

// List of environment variables to expose to the browser
const publicEnvVars = [
  'NEXT_PUBLIC_API_BASE_URL',
  'NEXT_PUBLIC_APP_NAME',
  'NEXT_PUBLIC_APP_ENV',
  'NEXT_PUBLIC_ENABLE_ANALYTICS',
  'NEXT_PUBLIC_ENABLE_DEBUG',
  'NEXT_PUBLIC_GOOGLE_ANALYTICS_ID',
  'NEXT_PUBLIC_DEFAULT_MODEL',
  'NEXT_PUBLIC_DEFAULT_API_VERSION',
];

// Create an object with the environment variables to expose
const env = publicEnvVars.reduce((acc, key) => {
  // Get the value from process.env
  let value = process.env[key];
  
  // Set default for API base URL if not found
  if (key === 'NEXT_PUBLIC_API_BASE_URL' && !value) {
    value = 'http://localhost:8000';
  }
  
  if (value !== undefined) {
    acc[key] = value;
  }
  return acc;
}, {
  // Add any non-NEXT_PUBLIC_ variables that should be exposed
  APP_VERSION: process.env.npm_package_version,
});

// Log environment variables for debugging
console.log('Environment variables being exposed to the client:');
console.log(env);

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Environment variables available at build time and runtime
  env,
  
  // Server-side only environment variables
  serverRuntimeConfig: {
    // Will only be available on the server side
    authSecret: process.env.NEXTAUTH_SECRET,
  },
  
  // API rewrites
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '/:path*',
      },
    ];
  },
  
  // Enable React Strict Mode
  reactStrictMode: true,
  
  // Enable source maps in production for better error reporting
  productionBrowserSourceMaps: process.env.NEXT_PUBLIC_ENABLE_DEBUG === 'true',
};

module.exports = nextConfig;