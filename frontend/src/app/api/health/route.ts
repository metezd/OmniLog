// Health check for the host (for example Render). It answers without calling the backend, so a
// backend outage does not make the frontend look dead. It is not a protected page, see
// lib/auth/routes.ts.
export const dynamic = "force-dynamic";

export function GET() {
  return Response.json({ status: "ok" }, { headers: { "Cache-Control": "no-store" } });
}
