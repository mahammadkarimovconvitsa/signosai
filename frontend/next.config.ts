import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // cacheComponents/partialPrefetching are experimental canary caching
  // features (default from the original create-next-app scaffold) that
  // aggressively remount client boundaries. That's incompatible with
  // react-leaflet's MapContainer, which does imperative, non-idempotent DOM
  // setup (L.map(container)) and isn't built to survive being torn down and
  // recreated mid-render -- causes "Cannot read properties of undefined
  // (reading 'appendChild')" when TileLayer mounts into a map whose
  // container got swapped out from under it. This app doesn't need these
  // perf features, so they're off rather than patched around.
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
