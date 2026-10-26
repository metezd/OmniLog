// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

import { GET } from "@/app/session-expired/route";
import { cookieStore } from "../mocks/cookie-store";
import { liveToken } from "../mocks/token";

vi.mock("next/headers", async () => {
  const { cookieStore } = await import("../mocks/cookie-store");
  return { cookies: async () => cookieStore };
});
vi.mock("next/navigation", async () => await import("../mocks/next-navigation"));

describe("GET /session-expired", () => {
  it("removes the session cookie and sends the user to the login page with a note", async () => {
    cookieStore.set("omnilog_session", liveToken());

    await expect(GET()).rejects.toMatchObject({ url: "/login?expired=1" });
    expect(cookieStore.has("omnilog_session")).toBe(false);
  });
});
