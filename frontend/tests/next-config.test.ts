// @vitest-environment node
import { describe, expect, it } from "vitest";

import nextConfig, { HSTS_HEADER, securityHeaders } from "../next.config";

// On Render the frontend has no Caddy in front, so it sends the browser headers itself (#304).
// The Content-Security-Policy comes from src/proxy.ts (#303).
describe("security headers of the frontend (#304)", () => {
  it("sends the browser headers on every page", async () => {
    const rules = (await nextConfig.headers?.()) ?? [];
    const everyPage = rules.find((rule) => rule.source === "/:path*");
    const headers = Object.fromEntries((everyPage?.headers ?? []).map(({ key, value }) => [key, value]));

    expect(headers).toEqual({
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
      "X-Frame-Options": "DENY",
    });
  });

  it("does not name the framework", () => {
    expect(nextConfig.poweredByHeader).toBe(false);
  });
});

describe("HSTS of the frontend (#425)", () => {
  it("sends Strict-Transport-Security for a year in production", () => {
    expect(securityHeaders("production")).toContainEqual({ key: "Strict-Transport-Security", value: "max-age=31536000" });
    expect(HSTS_HEADER.value).toBe("max-age=31536000");
  });

  it.each(["development", "test", undefined])("does not send it for %s, so http://localhost works", (env) => {
    expect(securityHeaders(env).map(({ key }) => key)).not.toContain("Strict-Transport-Security");
  });
});

