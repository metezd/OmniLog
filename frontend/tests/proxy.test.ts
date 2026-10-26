// @vitest-environment node
import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

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
