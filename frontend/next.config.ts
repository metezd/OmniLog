import type { NextConfig } from "next";

// Browser headers on every page (#304). On Render the frontend has no Caddy in front, so it sends
// them itself. The Content-Security-Policy comes from src/proxy.ts, because it needs a new nonce
// for every request (#303).
const SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
  { key: "X-Frame-Options", value: "DENY" },
];

// HTTPS only, for a year (#425). The login form and the session cookie live on the frontend, so a
// first request over plain HTTP could be kept on HTTP by an attacker (SSL stripping). Only in
// production: `next dev` runs on http://localhost, which must keep working. The same value as the
// API (#394) and Caddy.
// No `includeSubDomains`: on Render the app lives on a shared `onrender.com` name, and the header
// must not speak for other names. No `preload` either: the preload list is hard to leave (#449).
export const HSTS_HEADER = { key: "Strict-Transport-Security", value: "max-age=31536000" };

export function securityHeaders(nodeEnv: string | undefined = process.env.NODE_ENV) {
  return nodeEnv === "production" ? [...SECURITY_HEADERS, HSTS_HEADER] : SECURITY_HEADERS;
}

const nextConfig: NextConfig = {
  // A small server for Docker: .next/standalone has only the files that the app needs
  output: "standalone",
  // No "X-Powered-By: Next.js" (penetration finding F7)
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders() }];
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "image.tmdb.org" },
      { protocol: "https", hostname: "images.igdb.com" },
      { protocol: "https", hostname: "static.tvmaze.com" },
      { protocol: "https", hostname: "shared.akamai.steamstatic.com" },
      { protocol: "https", hostname: "cdn.akamai.steamstatic.com" },
      { protocol: "https", hostname: "is1-ssl.mzstatic.com" },
    ],
  },
};

export default nextConfig;
