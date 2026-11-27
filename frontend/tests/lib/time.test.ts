import { describe, expect, it } from "vitest";

import { formatApiTime, parseApiTime } from "@/lib/time";

// The example of #383: 19:34 UTC is 22:34 in Turkey (UTC+3)
const UTC_TIME = "2026-11-26T19:34:34.794654Z";

describe("parseApiTime", () => {
  it("reads a time with Z as UTC", () => {
    expect(parseApiTime(UTC_TIME)?.toISOString()).toBe("2026-11-26T19:34:34.794Z");
  });

  it("reads a time without an offset as UTC, not as local time", () => {
    expect(parseApiTime("2026-11-26T19:34:34.794654")?.toISOString()).toBe("2026-11-26T19:34:34.794Z");
  });

  it("keeps another offset", () => {
    expect(parseApiTime("2026-11-26T22:34:34+03:00")?.toISOString()).toBe("2026-11-26T19:34:34.000Z");
  });

  it("gives null for a text that is not a time", () => {
    expect(parseApiTime("not a time")).toBeNull();
  });
});

describe("formatApiTime", () => {
  it("shows the time of Turkey in Istanbul", () => {
    expect(formatApiTime(UTC_TIME, "Europe/Istanbul")).toBe("Nov 26, 2026, 10:34 PM");
  });

  it("shows the same moment in UTC", () => {
    expect(formatApiTime(UTC_TIME, "UTC")).toBe("Nov 26, 2026, 07:34 PM");
  });

  it("gives the same result for a time without an offset", () => {
    expect(formatApiTime("2026-11-26T19:34:34.794654", "Europe/Istanbul")).toBe("Nov 26, 2026, 10:34 PM");
  });

  it("gives a text that is not a time back as it is", () => {
    expect(formatApiTime("soon", "UTC")).toBe("soon");
  });
});
