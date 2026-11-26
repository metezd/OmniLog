import "server-only";

import { backendFetch } from "./backend";

// A free backend on Render sleeps when nobody uses it, and its first answer can take about a
// minute. The login and register pages call warmUpBackend(), so the backend starts while the user
// fills in the form and the login itself does not wait (#250). The browser never calls the backend
// (see backend.ts), so the ping is sent from this server.

/** At most one ping a minute, so many page views do not send many requests to the backend. */
export const WARMUP_INTERVAL_MS = 60_000;

/** A sleeping backend can need this long to answer. Nobody waits for it. */
const WARMUP_TIMEOUT_MS = 60_000;

let lastPing: number | null = null;

/**
 * Sends GET /health to the backend without waiting for the answer. Returns false when a ping was
 * already sent within the last minute. It never throws: a backend that is down only means the
 * login waits longer, and the login page shows its own error then.
 */
export function warmUpBackend(now: number = Date.now()): boolean {
  if (lastPing !== null && now - lastPing < WARMUP_INTERVAL_MS) {
    return false;
  }
  lastPing = now;
  void backendFetch("/health", { timeoutMs: WARMUP_TIMEOUT_MS }).catch(() => undefined);
  return true;
}

/** Forgets the last ping. For the tests only. */
export function resetWarmUp(): void {
  lastPing = null;
}
