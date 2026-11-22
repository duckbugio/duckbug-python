from __future__ import annotations

import json
from http.cookies import SimpleCookie
from typing import Any, Awaitable, Callable, Dict, List, Mapping, Optional, Tuple
from urllib.parse import parse_qs, urlencode

from duckbug.context import RequestContext, reset_request_context, set_request_context


Scope = Dict[str, Any]
Message = Dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def _headers_to_dict(headers: List[Tuple[bytes, bytes]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for raw_name, raw_value in headers:
        name = raw_name.decode("latin-1")
        value = raw_value.decode("latin-1")
        if name in result:
            result[name] = result[name] + ", " + value
        else:
            result[name] = value
    return result


def _get_header(headers: Mapping[str, str], name: str) -> Optional[str]:
    # case-insensitive lookup
    lname = name.lower()
    for k, v in headers.items():
        if k.lower() == lname:
            return v
    return None


def _parse_cookies(cookie_header: Optional[str]) -> Optional[Dict[str, str]]:
    if not cookie_header:
        return None
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    if not cookie:
        return None
    return {k: morsel.value for k, morsel in cookie.items()}


def _build_url(scope: Scope, headers: Mapping[str, str]) -> Optional[str]:
    scheme = scope.get("scheme") or "http"
    server = scope.get("server")
    host_header = _get_header(headers, "host")

    if host_header:
        host = host_header
    elif isinstance(server, (tuple, list)) and len(server) >= 1 and server[0]:
        host = str(server[0])
        port = server[1] if len(server) > 1 else None
        # Add port only when it's non-standard (best-effort)
        if port and ((scheme == "http" and int(port) != 80) or (scheme == "https" and int(port) != 443)):
            host = f"{host}:{port}"
    else:
        return None

    path = scope.get("path") or ""
    query_string = scope.get("query_string") or b""
    try:
        qs = query_string.decode("latin-1")
    except Exception:
        qs = ""

    url = f"{scheme}://{host}{path}"
    if qs:
        url = url + "?" + qs
    return url


def _parse_query_params(scope: Scope) -> Optional[Dict[str, Any]]:
    raw = scope.get("query_string") or b""
    if not raw:
        return None
    try:
        qs = raw.decode("latin-1")
    except Exception:
        return None
    parsed = parse_qs(qs, keep_blank_values=True)
    return parsed if parsed else None


def _is_json_content_type(content_type: Optional[str]) -> bool:
    if not content_type:
        return False
    ct = content_type.split(";", 1)[0].strip().lower()
    return ct == "application/json" or ct.endswith("+json")


def _parse_json_body(body: bytes) -> Optional[Any]:
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


class DuckBugASGIMiddleware:
    """
    Framework-agnostic ASGI middleware.

    Works with FastAPI/Starlette:
        app.add_middleware(DuckBugASGIMiddleware)
    """

    def __init__(self, app: ASGIApp, *, capture_body: bool = True) -> None:
        self.app = app
        self.capture_body = capture_body

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = _headers_to_dict(scope.get("headers") or [])
        method = scope.get("method")
        url = _build_url(scope, headers)
        query_params = _parse_query_params(scope)
        cookies = _parse_cookies(_get_header(headers, "cookie"))

        client = scope.get("client")
        ip: Optional[str] = None
        if isinstance(client, (tuple, list)) and client:
            ip = str(client[0]) if client[0] else None

        body_bytes = b""
        body_params: Optional[Any] = None

        if self.capture_body:
            content_type = _get_header(headers, "content-type")
            if _is_json_content_type(content_type):
                chunks: List[bytes] = []
                more = True
                while more:
                    message = await receive()
                    if message.get("type") != "http.request":
                        break
                    chunk = message.get("body") or b""
                    if chunk:
                        chunks.append(chunk)
                    more = bool(message.get("more_body"))
                body_bytes = b"".join(chunks)
                body_params = _parse_json_body(body_bytes)

                # Replay the body downstream
                sent = False

                async def replay_receive() -> Message:
                    nonlocal sent
                    if not sent:
                        sent = True
                        return {"type": "http.request", "body": body_bytes, "more_body": False}
                    return {"type": "http.request", "body": b"", "more_body": False}

                downstream_receive = replay_receive
            else:
                downstream_receive = receive
        else:
            downstream_receive = receive

        token = set_request_context(
            RequestContext(
                ip=ip,
                url=url,
                method=method,
                headers=headers or None,
                query_params=query_params,
                body_params=body_params if isinstance(body_params, Mapping) else None,
                cookies=cookies,
            )
        )

        try:
            await self.app(scope, downstream_receive, send)
        finally:
            reset_request_context(token)
