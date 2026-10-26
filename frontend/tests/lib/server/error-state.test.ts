// @vitest-environment node
import { describe, expect, it } from "vitest";

import { BackendError } from "@/lib/server/backend";
import { toErrorState } from "@/lib/server/error-state";

describe("toErrorState", () => {
  it("maps a 404 to not_found", () => {
    expect(toErrorState(new BackendError(404, "Title not found")).kind).toBe("not_found");
  });

  it.each([
    [0, "no answer"],
    [503, "service unavailable"],
  ])("maps status %i (%s) to unavailable", (status) => {
    expect(toErrorState(new BackendError(status, "x")).kind).toBe("unavailable");
  });

  it.each([400, 409, 422, 500, 502])("maps status %i to error", (status) => {
    expect(toErrorState(new BackendError(status, "x")).kind).toBe("error");
  });

  it("never shows the text of the backend error to the user", () => {
    const state = toErrorState(new BackendError(500, 'relation "users" does not exist'));

    expect(state.message).not.toContain("relation");
  });

  it("throws anything that is not a BackendError again, so redirects keep working", () => {
    const redirectSignal = new Error("NEXT_REDIRECT /login");

    expect(() => toErrorState(redirectSignal)).toThrow(redirectSignal);
    expect(() => toErrorState("text")).toThrow();
  });
});
