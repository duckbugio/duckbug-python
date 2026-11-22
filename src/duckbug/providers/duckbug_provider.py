from __future__ import annotations

import time
import traceback
from typing import Any, Mapping, Optional

from duckbug.core.provider import LoggerMixin, Provider
from duckbug.duck import Duck
from duckbug.http_client.http_client import HttpClient
from duckbug.http_client.interface import HttpClientInterface


class DuckBugProvider(LoggerMixin, Provider):
    def __init__(
        self,
        client: HttpClientInterface,
        dsn: str,
        enable_env_logging: bool,
        enable_request_context_logging: bool,
    ) -> None:
        self._dsn = dsn
        self._enable_env_logging = enable_env_logging
        self._enable_request_context_logging = enable_request_context_logging
        self._client = client

    @classmethod
    def create(
        cls,
        dsn: str,
        enable_env_logging: bool = False,
        enable_request_context_logging: bool = True,
        timeout: int = 5,
        connection_timeout: int = 3,
    ) -> "DuckBugProvider":
        return cls(
            HttpClient(timeout=timeout, connection_timeout=connection_timeout),
            dsn=dsn,
            enable_env_logging=enable_env_logging,
            enable_request_context_logging=enable_request_context_logging,
        )

    def log(
        self, level: Any, message: str, context: Optional[Mapping[str, Any]] = None
    ) -> None:
        data: dict = {
            "time": self._get_micro_time_ms(),
            "level": self._get_level(str(level)),
            "message": message,
            "context": dict(context) if context else {},
        }

        pond = Duck.get_pond()

        if self._enable_request_context_logging:
            data.update(
                {
                    "ip": pond.get_user_ip(),
                    "url": pond.get_url(),
                    "method": pond.get_method(),
                    "headers": pond.get_headers(),
                    "queryParams": pond.get_query_params(),
                    "bodyParams": pond.get_body_params(),
                    "cookies": pond.get_cookies(),
                    "session": pond.get_session(),
                    "files": pond.get_files(),
                }
            )

        if self._enable_env_logging:
            data["env"] = pond.get_env()

        self._client.send(self._dsn, "logs", data)

    def quack(
        self, exception: BaseException, context: Optional[Mapping[str, Any]] = None
    ) -> None:
        tb = exception.__traceback__
        frames = traceback.extract_tb(tb) if tb is not None else []

        file = frames[-1].filename if frames else None
        line = frames[-1].lineno if frames else None

        data: dict = {
            "time": self._get_micro_time_ms(),
            "file": file,
            "line": line,
            "message": str(exception),
            "stacktrace": [
                {
                    "file": f.filename,
                    "line": f.lineno,
                    "function": f.name,
                    "code": f.line,
                }
                for f in frames
            ],
            "stacktraceAsString": "".join(
                traceback.format_exception(type(exception), exception, tb)
            ),
            "context": dict(context) if context else {},
        }

        # In the PHP SDK exceptions always include request context
        pond = Duck.get_pond()
        data.update(
            {
                "ip": pond.get_user_ip(),
                "url": pond.get_url(),
                "method": pond.get_method(),
                "headers": pond.get_headers(),
                "queryParams": pond.get_query_params(),
                "bodyParams": pond.get_body_params(),
                "cookies": pond.get_cookies(),
                "session": pond.get_session(),
                "files": pond.get_files(),
            }
        )

        if self._enable_env_logging:
            data["env"] = pond.get_env()

        self._client.send(self._dsn, "errors", data)

    @staticmethod
    def _get_micro_time_ms() -> int:
        return int(round(time.time() * 1000))

    @staticmethod
    def _get_level(level: str) -> str:
        level_norm = level.strip().upper()

        mapping = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "NOTICE": "INFO",
            "WARNING": "WARN",
            "ERROR": "ERROR",
            "CRITICAL": "FATAL",
            "ALERT": "FATAL",
            "EMERGENCY": "FATAL",
        }
        return mapping.get(level_norm, "INFO")
