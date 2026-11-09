import { setupServer } from "msw/node";

// The fake backend of the tests. The default has no handlers: each test adds the answers that it
// needs with server.use(http.get(...)).
export const server = setupServer();
