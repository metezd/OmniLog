// Helpers to make login tokens for tests. The backend makes three parts, and the middle part holds
// the claims. The signature is not checked by the frontend, so a fixed text is enough.

export function makeToken(claims: Record<string, unknown>): string {
  const encode = (value: unknown) => Buffer.from(JSON.stringify(value)).toString("base64url");
  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(claims)}.signature`;
}

/** A token that ends the given number of seconds from now (the default is one hour). */
export function liveToken(seconds = 3600): string {
  return makeToken({ sub: "7", exp: Math.floor(Date.now() / 1000) + seconds });
}

/** A token that ended a minute ago. */
export function endedToken(): string {
  return makeToken({ sub: "7", exp: Math.floor(Date.now() / 1000) - 60 });
}
