// @vitest-environment node
import { describe, expect, it } from "vitest";

import { GET } from "@/app/api/health/route";
import { isProtectedPath } from "@/lib/auth/routes";

describe("GET /api/health", () => {
  it("answers 200 with a short body and is never cached", async () => {
    const response = GET();

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ status: "ok" });
    expect(response.headers.get("Cache-Control")).toBe("no-store");
  });

  it("is not behind the login, so the host can reach it", () => {
    expect(isProtectedPath("/api/health")).toBe(false);
  });
});
