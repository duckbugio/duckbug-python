from __future__ import annotations

import json
from typing import Any, Callable, Mapping, Optional

from duckbug.context import RequestContext, reset_request_context, set_request_context


class DuckBugDjangoMiddleware:
    """
    Django middleware (no hard dependency at import time).

    Add to settings.py:
        MIDDLEWARE = [
            ...,
            "duckbug.integrations.django.DuckBugDjangoMiddleware",
        ]
    """

    def __init__(self, get_response: Callable[[Any], Any], *, capture_body: bool = True) -> None:
        self.get_response = get_response
        self.capture_body = capture_body

    def __call__(self, request: Any) -> Any:
        token = set_request_context(
            RequestContext(
                ip=_get_django_user_ip(request),
                url=_get_django_url(request),
                method=getattr(request, "method", None),
                headers=_get_django_headers(request),
                query_params=_get_django_query_params(request),
                body_params=_get_django_body_params(request) if self.capture_body else None,
                cookies=dict(getattr(request, "COOKIES", {}) or {}) or None,
                session=_get_django_session(request),
                files=_get_django_files(request),
            )
        )
        try:
            return self.get_response(request)
        finally:
            reset_request_context(token)


def _get_django_headers(request: Any) -> Optional[dict]:
    try:
        headers = getattr(request, "headers", None)
        if headers is None:
            return None
        d = dict(headers)
        return d or None
    except Exception:
        return None


def _get_django_query_params(request: Any) -> Optional[dict]:
    try:
        get = getattr(request, "GET", None)
        if not get:
            return None
        # QueryDict: allow multiple values per key
        result = {k: get.getlist(k) for k in get.keys()}
        return result or None
    except Exception:
        return None


def _get_django_body_params(request: Any) -> Optional[Mapping[str, Any]]:
    try:
        content_type = getattr(request, "content_type", None)
        if not content_type:
            return None
        ct = content_type.split(";", 1)[0].strip().lower()
        if ct != "application/json" and not ct.endswith("+json"):
            return None
        body = getattr(request, "body", b"") or b""
        if not body:
            return None
        parsed = json.loads(body.decode("utf-8"))
        return parsed if isinstance(parsed, Mapping) else None
    except Exception:
        return None


def _get_django_session(request: Any) -> Optional[dict]:
    try:
        session = getattr(request, "session", None)
        if session is None:
            return None
        items = dict(session.items())  # type: ignore[attr-defined]
        return items or None
    except Exception:
        return None


def _get_django_files(request: Any) -> Optional[dict]:
    try:
        files = getattr(request, "FILES", None)
        if not files:
            return None
        result: dict = {}
        for key in files.keys():
            f = files.get(key)
            if f is None:
                continue
            result[key] = {
                "name": getattr(f, "name", None),
                "content_type": getattr(f, "content_type", None),
                "size": getattr(f, "size", None),
            }
        return result or None
    except Exception:
        return None


def _get_django_url(request: Any) -> Optional[str]:
    try:
        build = getattr(request, "build_absolute_uri", None)
        if callable(build):
            return build()
        return None
    except Exception:
        return None


def _get_django_user_ip(request: Any) -> Optional[str]:
    # Try common proxy headers (same spirit as the PHP version)
    try:
        meta = getattr(request, "META", {}) or {}
        keys = [
            "HTTP_CLIENT_IP",
            "HTTP_X_FORWARDED_FOR",
            "HTTP_X_FORWARDED",
            "HTTP_X_CLUSTER_CLIENT_IP",
            "HTTP_FORWARDED_FOR",
            "HTTP_FORWARDED",
            "HTTP_CF_CONNECTING_IP",
            "REMOTE_ADDR",
        ]
        for key in keys:
            value = meta.get(key)
            if not value:
                continue
            if isinstance(value, str):
                ips = [ip.strip() for ip in value.split(",") if ip.strip()]
                if ips:
                    return ips[0]
        return None
    except Exception:
        return None
