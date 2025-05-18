import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["http://localhost:3000"],
  trailingSlash: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/:path*'
      },
      {
        source: '/videos/:path*',
        destination: 'http://backend:8000/videos/:path*'
      }
    ];
  }
};

export default nextConfig;
