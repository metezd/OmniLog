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
    // Components run in a simulated browser. happy-dom is used instead of jsdom because the tests
    // of the forms were about 22% faster with it. Keep it at version 20 or higher: older versions
    // run the scripts of a page by default, and they had serious security problems.
    // A test that needs plain Node (server code) starts with the line: // @vitest-environment node
    environment: "happy-dom",
    environmentOptions: {
      happyDOM: {
        // happy-dom had several security problems that let a page run code on the machine of the
        // developer (see tests/security/happy-dom.test.ts). Version 20 turned these off by
        // default. They are set here too, so a later change of the defaults cannot turn them on.
        // The tests never need them: components are rendered by React, not loaded from a page.
        settings: {
          enableJavaScriptEvaluation: false,
          disableJavaScriptFileLoading: true,
          enableCSSFileLoading: false,
          enableImageFileLoading: false,
          enableIframePageLoading: false,
          enableFileSystemHttpRequests: false,
        },
      },
    },
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
