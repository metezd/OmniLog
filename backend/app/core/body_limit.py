"""A size limit for request bodies (#302, penetration finding F6).

The largest real body of the API is a review of 5000 characters, far under 1 MB. Without a limit
the API read any body in full before the schema refused it. This middleware answers:

- 400 when Content-Length is not a whole number,
- 413 when Content-Length is over the limit, before the body is read,
- 413 when a body without Content-Length (chunked) grows over the limit while it is read.

Caddy has the same limit (`request_body { max_size 1MB }` in docker/Caddyfile).
"""
import json

MAX_BODY_BYTES = 1024 * 1024


class BodyTooLarge(Exception):
    pass


class BodySizeLimitMiddleware:
    """A pure ASGI middleware, so it can stop a request before the body is read."""

    def __init__(self, app, max_bytes: int = MAX_BODY_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        lengths = [value for name, value in scope.get("headers", []) if name == b"content-length"]
        if lengths:
            text = lengths[0].decode("latin-1").strip()
            if len(lengths) > 1 or not text.isdigit():
                await self._answer(send, 400, "Content-Length must be a whole number")
                return
            if int(text) > self.max_bytes:
                await self._answer(send, 413, "The request body is too large")
                return

        received = 0
        started = False

        async def counting_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise BodyTooLarge
            return message

        async def tracking_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, counting_receive, tracking_send)
        except BodyTooLarge:
            if not started:
                await self._answer(send, 413, "The request body is too large")

    @staticmethod
    async def _answer(send, status: int, detail: str) -> None:
        body = json.dumps({"detail": detail}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
            }
        )
        await send({"type": "http.response.body", "body": body})
