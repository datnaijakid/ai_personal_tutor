import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/upload",
        destination: "http://127.0.0.1:8000/upload",
      },
      {
        source: "/chat",
        destination: "http://127.0.0.1:8000/chat",
      },
      {
        source: "/search",
        destination: "http://127.0.0.1:8000/search",
      },
    ];
  },
};

export default nextConfig;
