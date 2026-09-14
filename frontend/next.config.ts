import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The Docker image copies .next/standalone rather than installing
  // node_modules in the final stage; see frontend/Dockerfile.
  output: "standalone",
};

export default nextConfig;
