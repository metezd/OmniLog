import { describe, expect, it } from "vitest";

import { cn } from "@/lib/utils";

describe("cn", () => {
  it("joins class names and skips empty values", () => {
    expect(cn("a", false, undefined, null, "b")).toBe("a b");
  });

  it("keeps only the last of two conflicting Tailwind classes", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });

  it("accepts conditional objects and arrays", () => {
    expect(cn("base", { active: true, hidden: false }, ["x", "y"])).toBe("base active x y");
  });
});
