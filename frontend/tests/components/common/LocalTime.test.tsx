import { render, screen } from "@testing-library/react";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it } from "vitest";

import LocalTime from "@/components/common/LocalTime";
import { formatApiTime } from "@/lib/time";

const UTC_TIME = "2026-11-26T19:34:34.794654Z";

const ORIGINAL_TZ = process.env.TZ;

describe("LocalTime", () => {
  afterEach(() => {
    process.env.TZ = ORIGINAL_TZ;
  });

  it("shows the time of Turkey in a browser in Istanbul, not 3 hours early", () => {
    process.env.TZ = "Europe/Istanbul";

    render(<LocalTime iso={UTC_TIME} />);

    expect(screen.getByText("Nov 26, 2026, 10:34 PM")).toBeTruthy();
  });

  it("renders UTC with a label on the server, which does not know the time zone of the user", () => {
    const html = renderToString(<LocalTime iso={UTC_TIME} />);

    expect(html).toContain("Nov 26, 2026, 07:34 PM UTC");
    expect(html).toContain('dateTime="2026-11-26T19:34:34.794Z"');
  });

  it("shows the local time of the browser", () => {
    render(<LocalTime iso={UTC_TIME} className="text-xs" />);

    const time = screen.getByText(formatApiTime(UTC_TIME));
    expect(time.tagName).toBe("TIME");
    expect(time.getAttribute("datetime")).toBe("2026-11-26T19:34:34.794Z");
    expect(time.className).toBe("text-xs");
  });

  it("shows a text that is not a time as it is", () => {
    render(<LocalTime iso="unknown" />);

    expect(screen.getByText("unknown")).toBeTruthy();
  });
});
