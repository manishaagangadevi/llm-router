import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // self-contained server output, used by the Docker image
  output: "standalone",
};

export default nextConfig;
