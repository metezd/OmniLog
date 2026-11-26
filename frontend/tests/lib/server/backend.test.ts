// @vitest-environment node
import { delay, http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { BackendError, backendFetch } from "@/lib/server/backend";
import { server } from "../../mocks/server";

const BASE = "http://backend.test";

function useBackend() {
  vi.stubEnv("BACKEND_URL", BASE);
}

async function failure(call: Promise<unknown>): Promise<BackendError> {
  const error = await call.then(
    () => undefined,
    (caught: unknown) => caught,
  );
  expect(error).toBeInstanceOf(BackendError);
  return error as BackendError;
}

describe("a successful call", () => {
  it("returns the JSON answer", async () => {
    useBackend();
    server.use(http.get(`${BASE}/health`, () => HttpResponse.json({ status: "healthy" })));

    expect(await backendFetch("/health")).toEqual({ status: "healthy" });
  });

  it("sends the token as a Bearer token, and sends none without a token", async () => {
    useBackend();
    const seen: Array<string | null> = [];
    server.use(
      http.get(`${BASE}/auth/me`, ({ request }) => {
        seen.push(request.headers.get("authorization"));
        return HttpResponse.json({ id: 1 });
      }),
    );

    await backendFetch("/auth/me", { token: "abc.def" });
    await backendFetch("/auth/me");

    expect(seen).toEqual(["Bearer abc.def", null]);
  });

  it("sends a body as JSON with the matching headers", async () => {
    useBackend();
    let received: { type: string | null; accept: string | null; body: unknown } | undefined;
    server.use(
      http.post(`${BASE}/auth/login`, async ({ request }) => {
        received = {
          type: request.headers.get("content-type"),
          accept: request.headers.get("accept"),
          body: await request.json(),
        };
        return HttpResponse.json({ access_token: "t", token_type: "bearer" });
      }),
    );

    await backendFetch("/auth/login", { method: "POST", body: { username: "ali", password: "x" } });

    expect(received).toEqual({
      type: "application/json",
      accept: "application/json",
      body: { username: "ali", password: "x" },
    });
  });

  it("never lets Next.js cache the answer, because it belongs to one user", async () => {
    useBackend();
    server.use(http.get(`${BASE}/library`, () => HttpResponse.json([])));
    const spy = vi.spyOn(globalThis, "fetch");

    await backendFetch("/library", { token: "t" });

    expect(spy).toHaveBeenCalledWith(`${BASE}/library`, expect.objectContaining({ cache: "no-store" }));
  });

  it("returns undefined for an answer without content", async () => {
    useBackend();
    server.use(http.delete(`${BASE}/lists/1`, () => new HttpResponse(null, { status: 204 })));

    expect(await backendFetch("/lists/1", { method: "DELETE", token: "t" })).toBeUndefined();
  });
});

describe("an error answer", () => {
  it("carries the status and the detail text of the backend", async () => {
    useBackend();
    server.use(
      http.post(`${BASE}/auth/login`, () => HttpResponse.json({ detail: "Invalid credentials" }, { status: 401 })),
    );

    const error = await failure(backendFetch("/auth/login", { method: "POST", body: {} }));

    expect(error.status).toBe(401);
    expect(error.message).toBe("Invalid credentials");
    expect(error.fieldErrors).toEqual({});
  });

  it("maps a validation error to one message for each field", async () => {
    useBackend();
    server.use(
      http.post(`${BASE}/auth/register`, () =>
        HttpResponse.json(
          {
            detail: [
              { type: "string_too_short", loc: ["body", "password"], msg: "String should have at least 8 characters" },
              { type: "value_error", loc: ["body", "username"], msg: "Value error, must not contain @" },
              { type: "value_error", loc: ["body", "email"], msg: "value is not a valid email address" },
            ],
          },
          { status: 422 },
        ),
      ),
    );

    const error = await failure(backendFetch("/auth/register", { method: "POST", body: {} }));

    expect(error.status).toBe(422);
    expect(error.message).toBe("The request is not valid");
    expect(error.fieldErrors).toEqual({
      password: "String should have at least 8 characters",
      username: "must not contain @", // the prefix "Value error, " is removed
      email: "value is not a valid email address",
    });
  });

  it("keeps the first message of a field and maps a nested field with its path", async () => {
    useBackend();
    server.use(
      http.put(`${BASE}/x`, () =>
        HttpResponse.json(
          {
            detail: [
              { loc: ["body", "rating"], msg: "first" },
              { loc: ["body", "rating"], msg: "second" },
              { loc: ["body", "address", "street"], msg: "nested" },
            ],
          },
          { status: 422 },
        ),
      ),
    );

    const error = await failure(backendFetch("/x", { method: "PUT", body: {} }));

    expect(error.fieldErrors).toEqual({ rating: "first", "address.street": "nested" });
  });

  it("treats a problem outside the body (path or query) as a general message", async () => {
    useBackend();
    server.use(
      http.get(`${BASE}/library/abc`, () =>
        HttpResponse.json(
          { detail: [{ loc: ["path", "entry_id"], msg: "Input should be a valid integer" }] },
          { status: 422 },
        ),
      ),
    );

    const error = await failure(backendFetch("/library/abc", { token: "t" }));

    expect(error.message).toBe("Input should be a valid integer");
    expect(error.fieldErrors).toEqual({});
  });

  it.each([
    ["an HTML page", new HttpResponse("<html>Bad gateway</html>", { status: 502 })],
    ["an empty body", new HttpResponse(null, { status: 500 })],
    ["JSON without detail", HttpResponse.json({ error: "x" }, { status: 500 })],
    ["an unknown detail type", HttpResponse.json({ detail: 42 }, { status: 500 })],
  ])("uses a general message for %s", async (_name, answer) => {
    useBackend();
    server.use(http.get(`${BASE}/boom`, () => answer.clone()));

    const error = await failure(backendFetch("/boom"));

    expect(error.message).toBe(`Request failed with status ${answer.status}`);
    expect(error.fieldErrors).toEqual({});
  });

  it("never puts the token into the error", async () => {
    useBackend();
    server.use(http.get(`${BASE}/boom`, () => HttpResponse.json({ detail: "Not authenticated" }, { status: 401 })));

    const error = await failure(backendFetch("/boom", { token: "secret-token-123" }));

    expect(JSON.stringify({ message: error.message, fields: error.fieldErrors, stack: error.stack })).not.toContain(
      "secret-token-123",
    );
  });
});

describe("a call that gets no usable answer", () => {
  it("reports status 0 when the backend cannot be reached", async () => {
    useBackend();
    server.use(http.get(`${BASE}/health`, () => HttpResponse.error()));

    const error = await failure(backendFetch("/health"));

    expect(error.status).toBe(0);
    expect(error.message).toBe("The server cannot be reached");
    expect(error.cause).toBeDefined();
  });

  it("gives up after the timeout", async () => {
    useBackend();
    server.use(
      http.get(`${BASE}/slow`, async () => {
        await delay(500);
        return HttpResponse.json({});
      }),
    );

    const error = await failure(backendFetch("/slow", { timeoutMs: 20 }));

    expect(error.status).toBe(0);
    expect(error.message).toBe("The server did not answer in time");
  });

  it("reports a successful answer that is not JSON", async () => {
    useBackend();
    server.use(http.get(`${BASE}/odd`, () => new HttpResponse("plain text", { status: 200 })));

    const error = await failure(backendFetch("/odd"));

    expect(error.status).toBe(200);
    expect(error.message).toBe("The server sent an answer that is not JSON");
  });
});

describe("the address of the backend", () => {
  it("ignores slashes at the end", async () => {
    vi.stubEnv("BACKEND_URL", `${BASE}///`);
    server.use(http.get(`${BASE}/health`, () => HttpResponse.json({ ok: true })));

    expect(await backendFetch("/health")).toEqual({ ok: true });
  });

  it("removes a long run of slashes at the end quickly (Sonar S8786)", async () => {
    vi.stubEnv("BACKEND_URL", `${BASE}${"/".repeat(100_000)}`);
    server.use(http.get(`${BASE}/health`, () => HttpResponse.json({ ok: true })));

    const start = performance.now();
    expect(await backendFetch("/health")).toEqual({ ok: true });
    expect(performance.now() - start).toBeLessThan(1000);
  });

  it("falls back to localhost:8000 in development", async () => {
    vi.stubEnv("BACKEND_URL", "");
    vi.stubEnv("NODE_ENV", "development");
    server.use(http.get("http://localhost:8000/health", () => HttpResponse.json({ ok: true })));

    expect(await backendFetch("/health")).toEqual({ ok: true });
  });

  it("refuses to guess in production", async () => {
    vi.stubEnv("BACKEND_URL", "");
    vi.stubEnv("NODE_ENV", "production");

    await expect(backendFetch("/health")).rejects.toThrow("BACKEND_URL is not set");
  });

  it.each(["backend:8000", "backend:8000/", "backend", "ftp://backend", "not a url"])(
    "rejects %j, as a setup mistake and not as a BackendError",
    async (value) => {
      vi.stubEnv("BACKEND_URL", value);

      const error = await backendFetch("/health").catch((caught: unknown) => caught);

      expect(error).toBeInstanceOf(Error);
      expect(error).not.toBeInstanceOf(BackendError);
      expect((error as Error).message).toBe("BACKEND_URL is not a valid URL. Start it with http:// or https://");
    },
  );

  it("accepts https and a port", async () => {
    vi.stubEnv("BACKEND_URL", "https://backend.test:8443");
    server.use(http.get("https://backend.test:8443/health", () => HttpResponse.json({ ok: true })));

    expect(await backendFetch("/health")).toEqual({ ok: true });
  });

  it("rejects a path without a slash at the start", async () => {
    useBackend();

    await expect(backendFetch("health")).rejects.toThrow(TypeError);
  });
});

describe("the address of the browser (#217)", () => {
  async function sentForwardedFor(forwardedFor: string | null | undefined): Promise<string | null> {
    vi.stubEnv("BACKEND_URL", BASE);
    let seen: string | null = "not called";
    server.use(
      http.post(`${BASE}/auth/login`, ({ request }) => {
        seen = request.headers.get("x-forwarded-for");
        return HttpResponse.json({ access_token: "t", token_type: "bearer" });
      }),
    );
    await backendFetch("/auth/login", { method: "POST", body: {}, forwardedFor });
    return seen;
  }

  it("sends an IPv4, an IPv6 address or a list of them as X-Forwarded-For", async () => {
    expect(await sentForwardedFor("203.0.113.7")).toBe("203.0.113.7");
    expect(await sentForwardedFor("2001:db8::1")).toBe("2001:db8::1");
    expect(await sentForwardedFor(" 203.0.113.7, 10.0.0.2 ")).toBe("203.0.113.7, 10.0.0.2");
  });

  it("sends nothing for a missing or empty value", async () => {
    expect(await sentForwardedFor(undefined)).toBeNull();
    expect(await sentForwardedFor(null)).toBeNull();
    expect(await sentForwardedFor("  ")).toBeNull();
  });

  it("sends nothing for a value that is not a list of addresses", async () => {
    expect(await sentForwardedFor("evil.example.com")).toBeNull();
    expect(await sentForwardedFor("1.2.3.4; drop")).toBeNull();
    expect(await sentForwardedFor("1".repeat(600))).toBeNull();
  });
});

describe("the browser address for the backend on Render (#301)", () => {
  async function sentHeaders(forwardedFor: string | null): Promise<Record<string, string | null>> {
    vi.stubEnv("BACKEND_URL", BASE);
    let seen: Record<string, string | null> = {};
    server.use(
      http.post(`${BASE}/auth/login`, ({ request }) => {
        seen = {
          clientIp: request.headers.get("x-client-ip"),
          key: request.headers.get("x-frontend-key"),
          forwardedFor: request.headers.get("x-forwarded-for"),
        };
        return HttpResponse.json({ access_token: "t", token_type: "bearer" });
      }),
    );
    await backendFetch("/auth/login", { method: "POST", body: {}, forwardedFor });
    return seen;
  }

  it("sends the right-most address and the key when FRONTEND_PROXY_SECRET is set", async () => {
    vi.stubEnv("FRONTEND_PROXY_SECRET", "a-shared-secret-of-the-frontend-and-backend");

    const seen = await sentHeaders("198.51.100.1, 203.0.113.7");

    // The proxy in front of the frontend writes the browser address at the right end. The left
    // part was written by the browser and is never used.
    expect(seen.clientIp).toBe("203.0.113.7");
    expect(seen.key).toBe("a-shared-secret-of-the-frontend-and-backend");
    expect(seen.forwardedFor).toBe("198.51.100.1, 203.0.113.7");
  });

  it("sends an IPv6 address as it is", async () => {
    vi.stubEnv("FRONTEND_PROXY_SECRET", "a-shared-secret-of-the-frontend-and-backend");

    expect((await sentHeaders("2001:db8::1")).clientIp).toBe("2001:db8::1");
  });

  it("sends neither header without FRONTEND_PROXY_SECRET", async () => {
    vi.stubEnv("FRONTEND_PROXY_SECRET", "");

    const seen = await sentHeaders("203.0.113.7");

    expect(seen.clientIp).toBeNull();
    expect(seen.key).toBeNull();
  });

  it("sends neither header without a browser address", async () => {
    vi.stubEnv("FRONTEND_PROXY_SECRET", "a-shared-secret-of-the-frontend-and-backend");

    const seen = await sentHeaders(null);

    expect(seen.clientIp).toBeNull();
    expect(seen.key).toBeNull();
  });
});
