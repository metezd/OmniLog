// @vitest-environment node
import { describe, expect, it } from "vitest";

import nextConfig from "../next.config";

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
