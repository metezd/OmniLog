// @vitest-environment node
import { describe, expect, it } from "vitest";

import { hasLiveToken, SESSION_COOKIE } from "@/lib/auth/token";
import { endedToken, liveToken, makeToken } from "../../mocks/token";

describe("hasLiveToken", () => {
  it("is true for a token that has not ended", () => {
    expect(hasLiveToken(liveToken())).toBe(true);
  });

  it("is false for a token that has ended", () => {
    expect(hasLiveToken(endedToken())).toBe(false);
  });

  it.each([
    ["undefined", undefined],
    ["null", null],
    ["an empty string", ""],
  ])("is false for %s", (_name, token) => {
    expect(hasLiveToken(token)).toBe(false);
  });

  it("is true for a token without a readable end time, because the backend decides", () => {
    expect(hasLiveToken(makeToken({ sub: "7" }))).toBe(true);
  });
});

describe("SESSION_COOKIE", () => {
  it("keeps the name that the login uses", () => {
    expect(SESSION_COOKIE).toBe("omnilog_session");
  });
});
