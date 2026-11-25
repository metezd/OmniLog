"""Security headers on every answer of the API (#220, #304).

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

# The interactive documentation (ENABLE_DOCS=true, development only) loads its scripts and styles
# from a CDN, so the strict policy above would break it
_DOCS_PATHS = ("/docs", "/redoc")


def _headers_for(path: str) -> dict[str, str]:
    headers = dict(SECURITY_HEADERS)
    if path.startswith(_DOCS_PATHS):
        headers.pop("Content-Security-Policy")
    # Answers of /auth/* can hold a token or user data, so they must never be cached
    if path == "/auth" or path.startswith("/auth/"):
        headers["Cache-Control"] = "no-store"
    return headers


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        wanted = _headers_for(scope.get("path", ""))
        started = False

        async def send_with_headers(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                present = {name.lower() for name, _ in message.get("headers", [])}
                extra = [
                    (name.lower().encode(), value.encode())
                    for name, value in wanted.items()
                    # Keep a header that the endpoint set itself, except Cache-Control of /auth
                    if name.lower().encode() not in present or name == "Cache-Control"
                ]
                kept = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if not (name.lower() == b"cache-control" and "Cache-Control" in wanted)
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
