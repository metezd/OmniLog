// @vitest-environment node
import { NextRequest } from "next/server";
import { describe, expect, it, vi } from "vitest";

import { proxy } from "@/proxy";
import { endedToken, liveToken } from "./mocks/token";

function request(path: string, token?: string): NextRequest {
  return new NextRequest(`http://localhost:3000${path}`, {
    headers: token ? { cookie: `omnilog_session=${token}` } : {},
  });
}

function redirectTarget(response: Response): string | null {
  return response.status === 307 ? new URL(response.headers.get("location") ?? "").pathname : null;
}

describe("proxy", () => {
  it("sends a visitor from a protected page to the login page", () => {
    expect(redirectTarget(proxy(request("/library")))).toBe("/login");
    expect(redirectTarget(proxy(request("/title/5")))).toBe("/login");
  });

  it("sends a user with an ended token to the login page", () => {
    expect(redirectTarget(proxy(request("/library", endedToken())))).toBe("/login");
  });

  it("lets a user with a live token through", () => {
    const response = proxy(request("/library", liveToken()));

    expect(response.status).toBe(200);
    expect(response.headers.get("x-middleware-next")).toBe("1");
  });

  it.each(["/", "/login", "/register", "/session-expired"])("lets a visitor open %s", (path) => {
    const response = proxy(request(path));

    expect(response.headers.get("x-middleware-next")).toBe("1");
  });
});

describe("Content-Security-Policy (#303)", () => {
  function policyOf(response: Response): Map<string, string[]> {
    const header =
      response.headers.get("content-security-policy") ??
      response.headers.get("content-security-policy-report-only") ??
      "";
    return new Map(
      header
        .split(";")
        .map((part) => part.trim().split(/\s+/))
        .filter((words) => words[0])
        .map(([name, ...values]) => [name, values]),
    );
  }

  it("is set on public pages, protected pages and redirects", () => {
    expect(policyOf(proxy(request("/login"))).size).toBeGreaterThan(0);
    expect(policyOf(proxy(request("/library", liveToken()))).size).toBeGreaterThan(0);
    expect(policyOf(proxy(request("/library"))).size).toBeGreaterThan(0);
  });

  it("allows images only from this site, data: and the TMDB and IGDB image hosts", () => {
    const images = policyOf(proxy(request("/login"))).get("img-src");

    expect(new Set(images)).toEqual(
      new Set(["'self'", "data:", "blob:", "https://image.tmdb.org", "https://images.igdb.com"]),
    );
  });

  it("allows scripts only with a nonce, never with unsafe-inline", () => {
    const scripts = policyOf(proxy(request("/login"))).get("script-src") ?? [];

    expect(scripts.some((value) => /^'nonce-[A-Za-z0-9+/=]{16,}'$/.test(value))).toBe(true);
    expect(scripts).not.toContain("'unsafe-inline'");
  });

  it("uses a new nonce for every request and gives it to Next.js", () => {
    const first = proxy(request("/login"));
    const second = proxy(request("/login"));
    const nonce = (response: Response) =>
      policyOf(response).get("script-src")?.find((value) => value.startsWith("'nonce-"));

    expect(nonce(first)).not.toBe(nonce(second));
    // Next.js reads the policy from the request headers to put the nonce on its own scripts
    expect(first.headers.get("x-middleware-request-content-security-policy")).toContain(nonce(first) ?? "missing");
  });

  it("blocks plugins, framing and foreign form targets", () => {
    const policy = policyOf(proxy(request("/login")));

    expect(policy.get("object-src")).toEqual(["'none'"]);
    expect(policy.get("frame-ancestors")).toEqual(["'none'"]);
    expect(policy.get("base-uri")).toEqual(["'self'"]);
    expect(policy.get("form-action")).toEqual(["'self'"]);
  });

  it("can run as report-only while a change is tried out", () => {
    vi.stubEnv("CSP_REPORT_ONLY", "true");

    const response = proxy(request("/login"));

    expect(response.headers.get("content-security-policy")).toBeNull();
    expect(response.headers.get("content-security-policy-report-only")).toContain("img-src");
  });
});
