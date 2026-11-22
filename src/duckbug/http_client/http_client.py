from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Mapping

from duckbug.http_client.interface import HttpClientInterface


class HttpClient(HttpClientInterface):
    def __init__(self, timeout: int = 5, connection_timeout: int = 3) -> None:
        self._timeout = timeout
        # urllib doesn't separate connect/read timeouts cleanly; keep the value for API parity
        self._connection_timeout = connection_timeout

    def send(self, dsn: str, type: str, data: Mapping[str, Any]) -> int:
        url = dsn.rstrip("/") + "/" + type.lstrip("/")

        try:
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        except Exception:
            # If data is not JSON serializable, fail quietly like the PHP client (it returns 0 on error)
            return 0

        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return int(getattr(resp, "status", 0) or 0)
        except urllib.error.HTTPError as e:
            return int(getattr(e, "code", 0) or 0)
        except Exception:
            return 0
