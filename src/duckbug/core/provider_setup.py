from __future__ import annotations

from dataclasses import dataclass

from duckbug.core.provider import Provider


@dataclass(frozen=True)
class ProviderSetup:
    provider: Provider
    enabled_throwable: bool = True
    enabled_debug: bool = True
    enabled_info: bool = True
    enabled_notice: bool = True
    enabled_warning: bool = True
    enabled_error: bool = True
    enabled_critical: bool = True
    enabled_alert: bool = True
    enabled_emergency: bool = True
