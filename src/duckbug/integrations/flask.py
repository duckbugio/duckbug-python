from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from duckbug.context import RequestContext, reset_request_context, set_request_context


class DuckBugFlask:
    """
    Flask integration (no hard dependency at import time).

    Usage:
        from duckbug.integrations.flask import DuckBugFlask
        DuckBugFlask(app)
    """

    def __init__(self, app: Optional[object] = None, *, capture_body: bool = True) -> None:
        self.capture_body = capture_body
        if app is not None:
            self.init_app(app)

    def init_app(self, app: object) -> None:
        # Lazy imports to avoid requiring Flask unless integration is used
        from flask import g, request

        @app.before_request  # type: ignore[attr-defined]
        def _duckbug_before_request() -> None:
            body_params = None
            if self.capture_body:
                try:
                    body_params = request.get_json(silent=True)
                except Exception:
                    body_params = None

            headers = dict(request.headers) if request.headers else None

            token = set_request_context(
                RequestContext(
                    ip=request.remote_addr,
                    url=request.url,
                    method=request.method,
                    headers=headers,
                    query_params=request.args.to_dict(flat=False) if request.args else None,
                    body_params=body_params if isinstance(body_params, Mapping) else None,
                    cookies=dict(request.cookies) if request.cookies else None,
                    session=dict(getattr(request, "session", {}) or {}) or None,
                    files=_extract_flask_files(request.files),
                )
            )
            g._duckbug_token = token  # type: ignore[attr-defined]

        @app.teardown_request  # type: ignore[attr-defined]
        def _duckbug_teardown_request(exc: Optional[BaseException] = None) -> None:
            token = getattr(g, "_duckbug_token", None)
            if token is not None:
                reset_request_context(token)


def _extract_flask_files(files: Any) -> Optional[dict]:
    try:
        if not files:
            return None
        result: dict = {}
        for key in files:
            storage = files.get(key)
            if storage is None:
                continue
            result[key] = {
                "name": getattr(storage, "filename", None),
                "content_type": getattr(storage, "content_type", None),
                "size": getattr(storage, "content_length", None),
            }
        return result or None
    except Exception:
        return None
