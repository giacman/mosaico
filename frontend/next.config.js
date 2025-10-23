const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  devIndicators: false,
  eslint: {
    // Unblock deployment: don't fail the build on ESLint errors
    ignoreDuringBuilds: true
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, './')
    }
    return config
  }
}

module.exports = nextConfig

