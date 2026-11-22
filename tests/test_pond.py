import sys
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duckbug import Pond  # noqa: E402
from duckbug.context import RequestContext, request_context  # noqa: E402


class PondTest(TestCase):
    def test_getters(self) -> None:
        pond = Pond.ripple(
            ["password", "token"],
            env={"TOKEN": "secret_token", "APP_ENV": "testing"},
        )

        ctx = RequestContext(
            method="POST",
            url="https://example.com/test",
            headers={"Authorization": "Bearer secret"},
            ip="192.168.0.1",
            cookies={"session": "abc123"},
            session={"user_id": 42},
            files={
                "file": {
                    "name": "file.txt",
                    "type": "text/plain",
                    "tmp_name": "/tmp/file",
                    "error": 0,
                    "size": 123,
                }
            },
        )

        with request_context(ctx):
            self.assertEqual("POST", pond.get_method())
            self.assertEqual("https://example.com/test", pond.get_url())

            headers = pond.get_headers()
            self.assertIsInstance(headers, dict)
            self.assertIn("Authorization", headers)

            self.assertEqual({"session": "abc123"}, pond.get_cookies())
            self.assertEqual({"user_id": 42}, pond.get_session())
            self.assertIn("file", pond.get_files() or {})
            self.assertEqual("192.168.0.1", pond.get_user_ip())

            env = pond.get_env()
            self.assertEqual({"TOKEN": "***", "APP_ENV": "testing"}, env)

    def test_mask_sensitive_data(self) -> None:
        pond = Pond.ripple(["password", "token"])
        data = {
            "password": "secret",
            "token": "123456",
            "other": "visible",
            "nested": {"password": "secret"},
        }

        result = pond._mask_sensitive_data(data)  # noqa: SLF001
        self.assertEqual("***", result["password"])
        self.assertEqual("***", result["token"])
        self.assertEqual("visible", result["other"])
        self.assertEqual("***", result["nested"]["password"])

    def test_empty_context(self) -> None:
        pond = Pond.ripple(["password", "token"], env={})

        with request_context(RequestContext()):
            self.assertIsNone(pond.get_headers())
            self.assertIsNone(pond.get_cookies())
            self.assertIsNone(pond.get_session())
            self.assertIsNone(pond.get_files())
            self.assertIsNone(pond.get_env())

    def test_deep_nested_sensitive_masking(self) -> None:
        pond = Pond.ripple(["password", "token"])
        data = {"a": {"b": {"password": "deep-secret"}}}
        result = pond._mask_sensitive_data(data)  # noqa: SLF001
        self.assertEqual("***", result["a"]["b"]["password"])

    def test_non_sensitive_data_not_masked(self) -> None:
        pond = Pond.ripple(["password", "token"])
        data = {"email": "test@example.com"}
        result = pond._mask_sensitive_data(data)  # noqa: SLF001
        self.assertEqual("test@example.com", result["email"])
