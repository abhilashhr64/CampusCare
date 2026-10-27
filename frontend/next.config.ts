import type { NextConfig } from "next";

const isMobile = process.env.BUILD_TARGET?.trim() === "mobile";

const nextConfig: NextConfig = {
  output: isMobile ? "export" : "standalone",
  images: {
    unoptimized: true,
  },
  ...(isMobile
    ? {}
    : {
        cacheComponents: true,
        partialPrefetching: true,
      }),
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
