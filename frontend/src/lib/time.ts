// Times of the API (#383). The backend sends UTC with a "Z", for example
// "2026-11-26T19:34:34.794654Z". An older answer, or a cached one, may still have no offset. It is
// UTC too, so a "Z" is added: `new Date()` would read it as local time and be off by the offset of
// the user (3 hours in Turkey).

const HAS_OFFSET = /(Z|[+-]\d{2}:?\d{2})$/i;

/** The time of an API answer, or null when the text is not a time. */
export function parseApiTime(iso: string): Date | null {
  const text = iso.trim();
  const date = new Date(HAS_OFFSET.test(text) ? text : `${text}Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

const FORMAT: Intl.DateTimeFormatOptions = {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
};

/**
 * The time as "Nov 26, 2026, 10:34 PM" in a time zone. Without `timeZone` it is the time zone of
 * the place where the code runs: the browser of the user in a client component, the server in a
 * Server Component. A text that is not a time is given back as it is.
 */
export function formatApiTime(iso: string, timeZone?: string): string {
  const date = parseApiTime(iso);
  if (!date) return iso;
  return date.toLocaleString("en-US", { ...FORMAT, timeZone });
}
