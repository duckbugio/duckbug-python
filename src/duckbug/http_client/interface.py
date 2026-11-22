from __future__ import annotations

from typing import Any, Mapping, Protocol


class HttpClientInterface(Protocol):
    def send(self, dsn: str, type: str, data: Mapping[str, Any]) -> int: ...
