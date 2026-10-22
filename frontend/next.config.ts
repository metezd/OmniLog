import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A small server for Docker: .next/standalone has only the files that the app needs
  output: "standalone",
};

export default nextConfig;
