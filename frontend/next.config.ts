import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["localhost", "127.0.0.1"],
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
      {
        source: "/quiz",
        destination: "http://127.0.0.1:8000/quiz",
      },
      {
        source: "/flashcards",
        destination: "http://127.0.0.1:8000/flashcards",
      },
      {
        source: "/summary",
        destination: "http://127.0.0.1:8000/summary",
      },
      { source: "/documents/:path*", destination: "http://127.0.0.1:8000/documents/:path*" },
      { source: "/courses/:path*", destination: "http://127.0.0.1:8000/courses/:path*" },
      { source: "/conversations/:path*", destination: "http://127.0.0.1:8000/conversations/:path*" },
    ];
  },
};

export default nextConfig;
