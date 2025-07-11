/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    APP_VERSION: process.env.npm_package_version,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;