import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duckbug.http_client.interface import HttpClientInterface  # noqa: E402
from duckbug.providers import DuckBugProvider  # noqa: E402


class DuckBugProviderTest(TestCase):
    TEST_DSN = "https://duckbug.io"

    def test_log_sends_correct_payload(self) -> None:
        client = Mock(spec=HttpClientInterface)

        provider = DuckBugProvider.create(
            self.TEST_DSN,
            enable_env_logging=False,
            enable_request_context_logging=True,
            timeout=1,
            connection_timeout=1,
        )
        provider._client = client  # type: ignore[attr-defined]

        provider.log("warning", "Something went wrong", {"foo": "bar"})

        client.send.assert_called_once()
        dsn, typ, data = client.send.call_args.args

        self.assertEqual(self.TEST_DSN, dsn)
        self.assertEqual("logs", typ)
        self.assertEqual("Something went wrong", data["message"])
        self.assertEqual("WARN", data["level"])
        self.assertIsInstance(data["time"], int)
        self.assertEqual({"foo": "bar"}, data["context"])

    def test_quack_sends_exception(self) -> None:
        client = Mock(spec=HttpClientInterface)

        provider = DuckBugProvider.create(
            self.TEST_DSN,
            enable_env_logging=False,
            enable_request_context_logging=True,
            timeout=1,
            connection_timeout=1,
        )
        provider._client = client  # type: ignore[attr-defined]

        try:
            raise Exception("test")
        except Exception as exc:
            provider.quack(exc)

        client.send.assert_called_once()
        dsn, typ, data = client.send.call_args.args

        self.assertEqual(self.TEST_DSN, dsn)
        self.assertEqual("errors", typ)
        self.assertIn("message", data)
        self.assertIn("stacktrace", data)
        self.assertIn("file", data)
        self.assertIn("line", data)
