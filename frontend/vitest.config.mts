import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // The same "@/*" alias as in tsconfig.json. It is written out here, because the Vite
      // option that reads it from tsconfig.json exists only in new versions of Vite.
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      // Next.js handles `import "server-only"` itself. In tests an empty file takes its place.
      "server-only": fileURLToPath(new URL("./tests/mocks/server-only.ts", import.meta.url)),
    },
  },
  test: {
    // Components run in a simulated browser. A test that needs plain Node (server code) starts
    // with the line: // @vitest-environment node
    environment: "jsdom",
    include: ["tests/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/setup.ts"],
    // Every test starts with fresh mocks: no calls and no answers left over from the test before
    clearMocks: true,
    mockReset: true,
    restoreMocks: true,
    // vi.stubEnv() changes are undone after each test
    unstubEnvs: true,
  },
});
