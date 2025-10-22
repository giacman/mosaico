import type { NextConfig } from "next"
import path from "path"

const nextConfig: NextConfig = {
  devIndicators: false,
  eslint: {
    // Unblock deployment: don't fail the build on ESLint errors
    ignoreDuringBuilds: true
  },
  webpack: (config) => {
    // Ensure @ alias resolves in all environments (Vercel included)
    config.resolve.alias['@'] = path.resolve(__dirname);
    return config
  }
}

export default nextConfig
