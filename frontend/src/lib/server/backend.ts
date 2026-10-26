import "server-only";

// The browser never calls the backend. Server code (Server Actions and Server Components) does,
// with this client. The login token stays on the server, in an httpOnly cookie.

/** Longest wait for an answer of the backend. */
const DEFAULT_TIMEOUT_MS = 10_000;

/**
 * A call to the backend did not succeed.
 *
 * `status` is the HTTP status of the answer, or 0 when there was no answer (the backend cannot be
 * reached or did not answer in time). `fieldErrors` holds the message for each form field when the
 * backend rejected the data (status 422), for example { password: "String should have at least
 * 8 characters" }.
 */
export class BackendError extends Error {
  readonly status: number;
  readonly fieldErrors: Record<string, string>;

  constructor(
    status: number,
    message: string,
    fieldErrors: Record<string, string> = {},
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = "BackendError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

export type BackendFetchOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** The login token. It is sent as a Bearer token and is never written to a message. */
  token?: string;
  /** Sent as JSON. */
  body?: unknown;
  timeoutMs?: number;
};

/** The address of the backend, without a slash at the end. */
function backendBaseUrl(): string {
  const configured = process.env.BACKEND_URL?.trim();
  if (!configured) {
    // A wrong default inside a container would send every call to nowhere, so production
    // refuses to guess.
    if (process.env.NODE_ENV === "production") {
      throw new Error("BACKEND_URL is not set");
    }
    return "http://localhost:8000";
  }
  // "backend:8000" is a valid URL for the URL class (the scheme is "backend:"), but it is a
  // mistake here. Only http and https are accepted.
  let protocol: string;
  try {
    protocol = new URL(configured).protocol;
  } catch {
    protocol = "";
  }
  if (protocol !== "http:" && protocol !== "https:") {
    throw new Error("BACKEND_URL is not a valid URL. Start it with http:// or https://");
  }
  return configured.replace(/\/+$/, "");
}

/** Message and field messages of an error answer of the backend (FastAPI). */
function describeError(
  status: number,
  body: unknown,
): { message: string; fieldErrors: Record<string, string> } {
  const fieldErrors: Record<string, string> = {};
  const fallback = `Request failed with status ${status}`;

  const detail = typeof body === "object" && body !== null ? (body as { detail?: unknown }).detail : undefined;

  if (typeof detail === "string") {
    return { message: detail, fieldErrors };
  }

  if (Array.isArray(detail)) {
    let general: string | undefined;
    for (const issue of detail) {
      if (typeof issue !== "object" || issue === null) continue;
      const { loc, msg } = issue as { loc?: unknown; msg?: unknown };
      if (typeof msg !== "string") continue;
      // "Value error, ..." is the prefix of Pydantic for a rule of ours. The user does not need it.
      const text = msg.replace(/^Value error, /, "");

      if (Array.isArray(loc) && loc[0] === "body" && loc.length > 1) {
        const field = loc.slice(1).join(".");
        fieldErrors[field] ??= text; // the first message of a field is kept
      } else {
        general ??= text;
      }
    }
    return {
      message: general ?? (Object.keys(fieldErrors).length > 0 ? "The request is not valid" : fallback),
      fieldErrors,
    };
  }

  return { message: fallback, fieldErrors };
}

/**
 * Call the backend and return the JSON answer. An answer that is not a success throws a
 * BackendError. A missing or wrong BACKEND_URL throws a plain Error, because that is a mistake of
 * the setup and not an answer of the backend.
 *
 * The answers are never cached (cache: "no-store"). They belong to one user.
 */
export async function backendFetch<T = unknown>(
  path: string,
  { method = "GET", token, body, timeoutMs = DEFAULT_TIMEOUT_MS }: BackendFetchOptions = {},
): Promise<T> {
  if (!path.startsWith("/")) {
    throw new TypeError("The path must start with /");
  }
  const url = `${backendBaseUrl()}${path}`;

  const headers = new Headers({ Accept: "application/json" });
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (body !== undefined) headers.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (cause) {
    const timedOut = cause instanceof DOMException && cause.name === "TimeoutError";
    throw new BackendError(
      0,
      timedOut ? "The server did not answer in time" : "The server cannot be reached",
      {},
      { cause },
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  let parsed: unknown;
  let isJson = true;
  try {
    parsed = text === "" ? undefined : JSON.parse(text);
  } catch {
    isJson = false;
  }

  if (!response.ok) {
    const { message, fieldErrors } = describeError(response.status, isJson ? parsed : undefined);
    throw new BackendError(response.status, message, fieldErrors);
  }
  if (!isJson) {
    throw new BackendError(response.status, "The server sent an answer that is not JSON");
  }
  return parsed as T;
}
