"use client";

import { useSyncExternalStore } from "react";

import { formatApiTime, parseApiTime } from "@/lib/time";

// Nothing changes later, so there is nothing to subscribe to
const subscribe = () => () => {};

/**
 * A time of the API in the time zone of the user (#383).
 *
 * The page is made on the server, which does not know the time zone of the user. So the render on
 * the server and the first render in the browser show the time in UTC with the label "UTC". Right
 * after that, React renders again in the browser with its local time. useSyncExternalStore does
 * this switch without a hydration mismatch.
 */
export default function LocalTime({ iso, className }: { iso: string; className?: string }) {
  const inBrowser = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
  const date = parseApiTime(iso);

  let text = iso;
  if (date) text = inBrowser ? formatApiTime(iso) : `${formatApiTime(iso, "UTC")} UTC`;

  return (
    <time className={className} dateTime={date ? date.toISOString() : iso}>
      {text}
    </time>
  );
}
