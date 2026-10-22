import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Vite reads the "@/*" alias from tsconfig.json, so tests import files like the app does
  resolve: { tsconfigPaths: true },
  test: {
    // Components run in a simulated browser. A test that needs plain Node (server code) starts
    // with the line: // @vitest-environment node
    environment: "jsdom",
    include: ["tests/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/setup.ts"],
    restoreMocks: true,
  },
});
