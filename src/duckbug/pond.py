from __future__ import annotations

import os
from typing import Any, Mapping, Optional, Sequence, Set, Union

from duckbug.context import get_request_context


JsonLike = Union[
    None,
    bool,
    int,
    float,
    str,
    Mapping[str, Any],
    list,
]


class Pond:
    def __init__(
        self, sensitive_fields: Optional[Sequence[str]] = None, *, env: Optional[Mapping[str, str]] = None
    ) -> None:
        self._sensitive_fields: Set[str] = {s.lower() for s in (sensitive_fields or [])}
        self._env = env if env is not None else os.environ

    @classmethod
    def ripple(
        cls, sensitive_fields: Optional[Sequence[str]] = None, *, env: Optional[Mapping[str, str]] = None
    ) -> "Pond":
        return cls(sensitive_fields=sensitive_fields, env=env)

    def get_user_ip(self) -> Optional[str]:
        ctx = get_request_context()
        if ctx is None:
            return None

        if ctx.ip:
            return ctx.ip

        headers = ctx.headers or {}
        lowered = {str(k).lower(): v for k, v in headers.items()} if isinstance(headers, Mapping) else {}
        # Best-effort fallback if only headers are provided
        for key in [
            "CF-Connecting-IP",
            "X-Forwarded-For",
            "X-Real-IP",
            "Client-IP",
            "Forwarded",
        ]:
            value = lowered.get(key.lower())
            if not value:
                continue

            if key == "X-Forwarded-For" and "," in value:
                return value.split(",", 1)[0].strip() or None
            return value

        return None

    def get_url(self) -> Optional[str]:
        ctx = get_request_context()
        return None if ctx is None else ctx.url

    def get_headers(self) -> Optional[dict]:
        ctx = get_request_context()
        if ctx is None or not ctx.headers:
            return None

        headers = dict(ctx.headers)
        return headers if headers else None

    def get_method(self) -> Optional[str]:
        ctx = get_request_context()
        return None if ctx is None else ctx.method

    def get_query_params(self) -> Optional[dict]:
        ctx = get_request_context()
        if ctx is None or not ctx.query_params:
            return None
        masked = self._mask_sensitive_data(dict(ctx.query_params))
        return masked if masked else None

    def get_body_params(self) -> Optional[dict]:
        ctx = get_request_context()
        if ctx is None or not ctx.body_params:
            return None
        masked = self._mask_sensitive_data(dict(ctx.body_params))
        return masked if masked else None

    def get_cookies(self) -> Optional[dict]:
        ctx = get_request_context()
        if ctx is None or not ctx.cookies:
            return None
        cookies = dict(ctx.cookies)
        return cookies if cookies else None

    def get_session(self) -> Optional[dict]:
        ctx = get_request_context()
        if ctx is None or not ctx.session:
            return None
        session = dict(ctx.session)
        return session if session else None

    def get_files(self) -> Optional[dict]:
        ctx = get_request_context()
        if ctx is None or not ctx.files:
            return None
        files = dict(ctx.files)
        return files if files else None

    def get_env(self) -> Optional[dict]:
        env_dict = dict(self._env) if self._env is not None else {}
        if not env_dict:
            return None
        masked = self._mask_sensitive_data(env_dict)
        return masked if masked else None

    def _mask_sensitive_data(self, data: Any) -> Any:
        if isinstance(data, Mapping):
            result: dict = {}
            for key, value in data.items():
                if isinstance(key, str) and key.lower() in self._sensitive_fields:
                    result[key] = "***"
                    continue
                result[key] = self._mask_sensitive_data(value)
            return result

        if isinstance(data, list):
            return [self._mask_sensitive_data(v) for v in data]

        if isinstance(data, tuple):
            return tuple(self._mask_sensitive_data(v) for v in data)

        return data
