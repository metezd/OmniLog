/**
 * Why a page has no data to show. unavailable: the backend or an outside service does not answer,
 * so trying again can help. not_found: the thing does not exist. error: anything else.
 */
export type ErrorKind = "unavailable" | "not_found" | "error";
