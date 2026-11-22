from __future__ import annotations

from typing import Any, ClassVar, List, Mapping, Optional, Sequence

from duckbug.core.provider_setup import ProviderSetup
from duckbug.pond import Pond


class Duck:
    _duck: ClassVar[Optional["Duck"]] = None
    _pond: ClassVar[Optional[Pond]] = None

    def __init__(
        self, setups: Optional[Sequence[ProviderSetup]] = None, sensitive_fields: Sequence[str] = ()
    ) -> None:
        self._setups: List[ProviderSetup] = list(setups or [])
        Duck._pond = Pond.ripple(list(sensitive_fields))

    @classmethod
    def wake(
        cls,
        setups: Optional[Sequence[ProviderSetup]] = None,
        sensitive_fields: Optional[Sequence[str]] = None,
    ) -> "Duck":
        if sensitive_fields is None:
            sensitive_fields = ["password", "token", "api_key"]

        cls._duck = cls(setups=setups or [], sensitive_fields=sensitive_fields)
        return cls._duck

    @classmethod
    def sleep(cls) -> None:
        """
        Resets the singleton instance (useful for tests).
        """

        cls._duck = None
        cls._pond = None

    @classmethod
    def get(cls) -> "Duck":
        if cls._duck is None:
            raise RuntimeError("Duck.get() was called before Duck.wake()")
        return cls._duck

    @classmethod
    def get_pond(cls) -> Pond:
        if cls._pond is None:
            cls._pond = Pond.ripple()
        return cls._pond

    def quack(self, exception: BaseException, context: Optional[Mapping[str, Any]] = None) -> None:
        ctx = dict(context) if context else {}
        for setup in self._setups:
            if not setup.enabled_throwable:
                continue
            setup.provider.quack(exception, ctx)

    def log(
        self, level: Any, message: str, context: Optional[Mapping[str, Any]] = None
    ) -> None:
        ctx = dict(context) if context else {}
        key = str(level).lower()

        for setup in self._setups:
            is_enabled = False

            if key == "debug":
                is_enabled = setup.enabled_debug
            elif key == "info":
                is_enabled = setup.enabled_info
            elif key == "notice":
                is_enabled = setup.enabled_notice
            elif key == "warning":
                is_enabled = setup.enabled_warning
            elif key == "error":
                is_enabled = setup.enabled_error
            elif key == "critical":
                is_enabled = setup.enabled_critical
            elif key == "alert":
                is_enabled = setup.enabled_alert
            elif key == "emergency":
                is_enabled = setup.enabled_emergency

            if not is_enabled:
                continue

            setup.provider.log(level, message, ctx)

    # Logger-like convenience methods
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

    def emergency(self, message: str, context: Optional[Mapping[str, Any]] = None) -> None:
        self.log("emergency", message, context)
