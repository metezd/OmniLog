import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./mocks/server";

// A request without a handler fails the test. Nothing in a test may reach a real server.
// MSW 3 calls this option onUnhandledFrame and MSW 2 calls it onUnhandledRequest, and each version
// ignores the name of the other one. Both are given, so it is strict with either version. (The
// options are in a variable, so the type check accepts the name that the installed version does
// not know.)
const strict = { onUnhandledRequest: "error", onUnhandledFrame: "error" } as const;
beforeAll(() => server.listen(strict));

afterEach(() => {
  cleanup(); // removes the rendered components (Vitest has no globals, so this is not automatic)
  server.resetHandlers(); // handlers that a test added do not leak into the next test
});

afterAll(() => server.close());
