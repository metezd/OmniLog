"""Security headers on every answer of the API (#220, #304, #394).

On Render there is no proxy of ours, so the API sets them itself. A pure ASGI middleware is used,
because it also sees the answer to an unhandled error: Starlette makes that 500 outside of the
`@app.middleware("http")` functions, so it had no headers before (penetration check CONF-05).
"""
import json
import logging

logger = logging.getLogger(__name__)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    # The API answers JSON and is never shown in a frame
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}

# Sent by the API itself when the request came over HTTPS (#394). On Render the API has no proxy of
# ours. Behind Caddy (docker-compose.prod.yml) the proxy removes this one and sets its own, so a
# browser never gets it twice.
HSTS_VALUE = "max-age=31536000"

# Every answer that does not set its own Cache-Control gets this one (#394). Answers of the library,
# the lists, the diary and the statistics hold the data of one user, so a browser or a proxy must
# not keep them. An endpoint can set its own header (the catalog does, #250). /auth/* always
# gets it, because those answers can hold a token.
NO_STORE = "no-store"

# The interactive documentation (ENABLE_DOCS=true, development only) loads its scripts and styles
# from a CDN, so the strict policy above would break it
_DOCS_PATHS = ("/docs", "/redoc")


def _is_auth(path: str) -> bool:
    return path == "/auth" or path.startswith("/auth/")


def _came_over_https(scope) -> bool:
    """True for a direct HTTPS request, or when the proxy in front says it was HTTPS."""
    if scope.get("scheme") == "https":
        return True
    for name, value in scope.get("headers", []):
        if name.lower() == b"x-forwarded-proto":
            # A chain of proxies can send "https, http". The first value is the one of the client.
            first = value.decode("latin-1").split(",")[0].strip().lower()
            return first == "https"
    return False


def _headers_for(scope) -> dict[str, str]:
    path = scope.get("path", "")
    headers = dict(SECURITY_HEADERS)
    if path.startswith(_DOCS_PATHS):
        headers.pop("Content-Security-Policy")
    headers["Cache-Control"] = NO_STORE
    if _came_over_https(scope):
        headers["Strict-Transport-Security"] = HSTS_VALUE
    return headers


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        wanted = _headers_for(scope)
        # The Cache-Control of an /auth answer replaces the one that the endpoint set
        forced = {b"cache-control"} if _is_auth(scope.get("path", "")) else set()
        started = False

        async def send_with_headers(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                kept = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() not in forced
                ]
                present = {name.lower() for name, _ in kept}
                # Keep a header that the endpoint set itself (one value only, never twice)
                extra = [
                    (name.lower().encode(), value.encode())
                    for name, value in wanted.items()
                    if name.lower().encode() not in present
                ]
                message = {**message, "headers": kept + extra}
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        except Exception:
            if started:
                raise
            # Answer the error here, with the headers, and let the server log it
            body = json.dumps({"detail": "Internal Server Error"}).encode()
            await send_with_headers(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
                }
            )
            await send_with_headers({"type": "http.response.body", "body": body})
            raise
