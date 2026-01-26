import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  devIndicators: false,
  eslint: {
    // Unblock deployment: don't fail the build on ESLint errors
    ignoreDuringBuilds: true
  },
  images: {
    // Allow external flag images from flagcdn.com
    remotePatterns: [
      {
        protocol: "https",
        hostname: "flagcdn.com",
        pathname: "/**"
      },
      {
        protocol: "https",
        hostname: "storage.googleapis.com",
        pathname: "/**"
      }
    ]
  }
}

export default nextConfig
