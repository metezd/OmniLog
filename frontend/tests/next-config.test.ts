// @vitest-environment node
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

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

// No component uses next/image, so the optimizer /_next/image is off and has no remote hosts (#451).
describe("image optimizer of the frontend (#451)", () => {
  it("is turned off and allows no remote hosts", () => {
    expect(nextConfig.images?.unoptimized).toBe(true);
    expect(nextConfig.images?.remotePatterns).toBeUndefined();
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


// Render has no Caddy in front, so the frontend sends HSTS itself. In the compose setup Caddy sends
// it for the app name and must drop the one of the frontend, so the browser gets one header (#449).
describe("HSTS of the frontend and of Caddy (#449)", () => {
  const caddyfile = readFileSync(fileURLToPath(new URL("../../docker/Caddyfile", import.meta.url)), "utf8");

  it("has no includeSubDomains and no preload", () => {
    expect(HSTS_HEADER.value).not.toMatch(/includeSubDomains|preload/i);
  });

  it("uses the same value in Caddy", () => {
    expect(caddyfile).toContain(`Strict-Transport-Security "${HSTS_HEADER.value}"`);
  });

  it("drops the header of the frontend in Caddy", () => {
    const appSite = caddyfile.split("{$APP_DOMAIN} {")[1]?.split("{$API_DOMAIN} {")[0] ?? "";
    expect(appSite).toMatch(/reverse_proxy frontend:3000 \{[^}]*header_down -Strict-Transport-Security/);
  });
});
