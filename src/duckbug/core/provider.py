from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol, runtime_checkable


@runtime_checkable
class Provider(Protocol):
    def quack(
        self, exception: BaseException, context: Optional[Mapping[str, Any]] = None
    ) -> None: ...

    def log(
        self, level: Any, message: str, context: Optional[Mapping[str, Any]] = None
    ) -> None: ...


class LoggerMixin:
    """
    Convenience methods similar to PSR LoggerTrait: debug/info/warning/... that call .log(...)
    """

    def log(
        self, level: Any, message: str, context: Optional[Mapping[str, Any]] = None
    ) -> None:
        raise NotImplementedError

    def debug(self, message: str, context: Optional[Mapping[str, Any]] = None) -> None:
        self.log("debug", message, context)

    def info(self, message: str, context: Optional[Mapping[str, Any]] = None) -> None:
        self.log("info", message, context)

    def notice(self, message: str, context: Optional[Mapping[str, Any]] = None) -> None:
        self.log("notice", message, context)

    def warning(self, message: str, context: Optional[Mapping[str, Any]] = None) -> None:
        self.log("warning", message, context)

    def error(self, message: str, context: Optional[Mapping[str, Any]] = None) -> None:
        self.log("error", message, context)

    def critical(self, message: str, context: Optional[Mapping[str, Any]] = None) -> None:
        self.log("critical", message, context)

    def alert(self, message: str, context: Optional[Mapping[str, Any]] = None) -> None:
        self.log("alert", message, context)

    def emergency(
        self, message: str, context: Optional[Mapping[str, Any]] = None
    ) -> None:
        self.log("emergency", message, context)
