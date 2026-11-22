import asyncio
import sys
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duckbug.context import get_request_context  # noqa: E402
from duckbug.integrations.asgi import DuckBugASGIMiddleware  # noqa: E402


class AsgiIntegrationTest(TestCase):
    def test_context_is_set_and_reset(self) -> None:
        seen = {}

        async def app(scope, receive, send):
            # Ensure body is replayed to downstream
            msg = await receive()
            self.assertEqual("http.request", msg["type"])
            self.assertTrue(msg["body"].startswith(b"{"))

            ctx = get_request_context()
            self.assertIsNotNone(ctx)
            assert ctx is not None
            seen["ip"] = ctx.ip
            seen["url"] = ctx.url
            seen["method"] = ctx.method
            seen["headers"] = ctx.headers
            seen["query_params"] = ctx.query_params
            seen["body_params"] = ctx.body_params
            seen["cookies"] = ctx.cookies

            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok", "more_body": False})

        middleware = DuckBugASGIMiddleware(app)

        scope = {
            "type": "http",
            "method": "POST",
            "scheme": "https",
            "server": ("example.com", 443),
            "path": "/test",
            "query_string": b"a=1&password=secret",
            "headers": [
                (b"host", b"example.com"),
                (b"content-type", b"application/json"),
                (b"cookie", b"session=abc123"),
            ],
            "client": ("192.168.0.1", 12345),
        }

        messages = [
            {"type": "http.request", "body": b'{"token":"secret","x":1}', "more_body": False},
        ]

        async def receive():
            if messages:
                return messages.pop(0)
            return {"type": "http.request", "body": b"", "more_body": False}

        sent = []

        async def send(message):
            sent.append(message)

        asyncio.run(middleware(scope, receive, send))

        self.assertEqual("192.168.0.1", seen["ip"])
        self.assertEqual("POST", seen["method"])
        self.assertTrue(seen["url"].startswith("https://example.com/test"))
        self.assertIn("host", (seen["headers"] or {}))
        self.assertEqual({"session": "abc123"}, seen["cookies"])
        self.assertEqual({"a": ["1"], "password": ["secret"]}, seen["query_params"])
        self.assertEqual({"token": "secret", "x": 1}, seen["body_params"])

        # Context is reset after request
        self.assertIsNone(get_request_context())
