import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Vite reads the "@/*" alias from tsconfig.json, so tests import files like the app does
    tsconfigPaths: true,
    alias: {
      // Next.js handles this import itself. In tests an empty file takes its place.
      "server-only": fileURLToPath(new URL("./tests/mocks/server-only.ts", import.meta.url)),
    },
  },
  test: {
    // Components run in a simulated browser. A test that needs plain Node (server code) starts
    // with the line: // @vitest-environment node
    environment: "jsdom",
    include: ["tests/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/setup.ts"],
    restoreMocks: true,
    // vi.stubEnv() changes are undone after each test
    unstubEnvs: true,
  },
});
