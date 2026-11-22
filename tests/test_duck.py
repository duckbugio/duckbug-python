import sys
from pathlib import Path
from typing import Any, Mapping, Optional
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from duckbug import Duck, ProviderSetup  # noqa: E402


class _Provider:
    def __init__(self) -> None:
        self.called_quack = False
        self.called_log = False
        self.last_level: Optional[Any] = None
        self.last_message: Optional[str] = None
        self.last_context: Optional[Mapping[str, Any]] = None

    def quack(self, exception: BaseException, context: Optional[Mapping[str, Any]] = None) -> None:
        self.called_quack = True

    def log(
        self, level: Any, message: str, context: Optional[Mapping[str, Any]] = None
    ) -> None:
        self.called_log = True
        self.last_level = level
        self.last_message = message
        self.last_context = context


class DuckTest(TestCase):
    def tearDown(self) -> None:
        Duck.sleep()

    def test_singleton_instance(self) -> None:
        duck = Duck.wake()
        self.assertIsInstance(duck, Duck)
        self.assertIs(duck, Duck.get())

    def test_get_raises_before_wake(self) -> None:
        Duck.sleep()
        with self.assertRaises(RuntimeError):
            Duck.get()

    def test_quack_called_if_enabled(self) -> None:
        provider = _Provider()
        duck = Duck.wake([ProviderSetup(provider, enabled_throwable=True)], sensitive_fields=["password"])
        duck.quack(Exception("Test"))
        self.assertTrue(provider.called_quack)

    def test_quack_not_called_if_disabled(self) -> None:
        provider = _Provider()
        duck = Duck.wake([ProviderSetup(provider, enabled_throwable=False)], sensitive_fields=["password"])
        duck.quack(Exception("Test"))
        self.assertFalse(provider.called_quack)

    def test_multiple_providers_are_called(self) -> None:
        called = []

        class P:
            def __init__(self, id_: str) -> None:
                self._id = id_

            def quack(self, exception: BaseException, context=None) -> None:
                called.append(self._id)

            def log(self, level, message, context=None) -> None:
                pass

        duck = Duck.wake([ProviderSetup(P("A")), ProviderSetup(P("B"))])
        duck.quack(Exception("Test"))
        self.assertEqual(["A", "B"], called)

    def test_log_respects_level_flags(self) -> None:
        levels = {
            "debug": "enabled_debug",
            "info": "enabled_info",
            "notice": "enabled_notice",
            "warning": "enabled_warning",
            "error": "enabled_error",
            "critical": "enabled_critical",
            "alert": "enabled_alert",
            "emergency": "enabled_emergency",
        }

        for level, flag in levels.items():
            provider = _Provider()
            setup_kwargs = {
                "enabled_throwable": False,
                "enabled_debug": flag == "enabled_debug",
                "enabled_info": flag == "enabled_info",
                "enabled_notice": flag == "enabled_notice",
                "enabled_warning": flag == "enabled_warning",
                "enabled_error": flag == "enabled_error",
                "enabled_critical": flag == "enabled_critical",
                "enabled_alert": flag == "enabled_alert",
                "enabled_emergency": flag == "enabled_emergency",
            }
            duck = Duck.wake([ProviderSetup(provider, **setup_kwargs)])
            duck.log(level.upper(), "msg", {"a": 1})

            self.assertTrue(provider.called_log, f"provider should be called for level={level}")
            self.assertEqual(level.upper(), provider.last_level)
            self.assertEqual("msg", provider.last_message)
            self.assertEqual({"a": 1}, provider.last_context)

    def test_log_skips_when_level_disabled(self) -> None:
        provider = _Provider()
        setup = ProviderSetup(
            provider,
            enabled_throwable=False,
            enabled_debug=False,
            enabled_info=False,
            enabled_notice=False,
            enabled_warning=False,
            enabled_error=False,
            enabled_critical=False,
            enabled_alert=False,
            enabled_emergency=False,
        )
        duck = Duck.wake([setup])
        duck.log("debug", "should not log")
        self.assertFalse(provider.called_log)

    def test_unknown_log_level_is_ignored(self) -> None:
        provider = _Provider()
        duck = Duck.wake([ProviderSetup(provider)])
        duck.log("unknownLevel", "msg")
        self.assertFalse(provider.called_log)
