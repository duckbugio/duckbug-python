from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any, Iterator, Mapping, Optional


@dataclass(frozen=True)
class RequestContext:
    ip: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Mapping[str, str]] = None
    query_params: Optional[Mapping[str, Any]] = None
    body_params: Optional[Mapping[str, Any]] = None
    cookies: Optional[Mapping[str, Any]] = None
    session: Optional[Mapping[str, Any]] = None
    files: Optional[Mapping[str, Any]] = None


_request_context: ContextVar[Optional[RequestContext]] = ContextVar(
    "duckbug_request_context", default=None
)


def set_request_context(context: Optional[RequestContext]) -> Token[Optional[RequestContext]]:
    return _request_context.set(context)


def reset_request_context(token: Token[Optional[RequestContext]]) -> None:
    _request_context.reset(token)


def get_request_context() -> Optional[RequestContext]:
    return _request_context.get()


@contextmanager
def request_context(context: Optional[RequestContext]) -> Iterator[None]:
    token = set_request_context(context)
    try:
        yield
    finally:
        reset_request_context(token)
