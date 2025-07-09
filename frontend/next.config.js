/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:9003/api/:path*', // Cambiato su 9003
        },
      ];
    },
  };
  
  module.exports = nextConfig;