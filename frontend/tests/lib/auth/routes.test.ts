// @vitest-environment node
import { describe, expect, it } from "vitest";

import { isProtectedPath, PROTECTED_PREFIXES } from "@/lib/auth/routes";

describe("isProtectedPath", () => {
  it.each(PROTECTED_PREFIXES)("protects %s and the pages below it", (prefix) => {
    expect(isProtectedPath(prefix)).toBe(true);
    expect(isProtectedPath(`${prefix}/12`)).toBe(true);
  });

  it.each(["/", "/login", "/register", "/friends", "/session-expired"])("leaves %s open", (path) => {
    expect(isProtectedPath(path)).toBe(false);
  });

  it("does not protect a path that only starts with the same letters", () => {
    expect(isProtectedPath("/library-of-alexandria")).toBe(false);
    expect(isProtectedPath("/searching")).toBe(false);
  });
});
