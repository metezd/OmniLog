import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./mocks/server";

// A request without a handler fails the test. Nothing in a test may reach a real server.
beforeAll(() => server.listen({ onUnhandledFrame: "error" }));

afterEach(() => {
  cleanup(); // removes the rendered components (Vitest has no globals, so this is not automatic)
  server.resetHandlers(); // handlers that a test added do not leak into the next test
});

afterAll(() => server.close());
