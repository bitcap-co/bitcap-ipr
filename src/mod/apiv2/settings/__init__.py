# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuthPassword(BaseModel):
    alt: str
    default: str

    def as_list(self) -> list[str]:
        return [self.alt, self.default]


class AuthConfig(BaseModel):
    antminer: AuthPassword = AuthPassword(alt="", default="root")
    iceriver: AuthPassword = AuthPassword(alt="", default="12345678")
    goldshell: AuthPassword = AuthPassword(alt="", default="123456789")
    sealminer: AuthPassword = AuthPassword(alt="", default="seal")
    elphapex: AuthPassword = AuthPassword(alt="", default="root")
    volcminer: AuthPassword = AuthPassword(alt="", default="ltc@dog")
    vnish: AuthPassword = AuthPassword(alt="", default="admin")
    whatsminer: AuthPassword = AuthPassword(alt="", default="admin")
    whatsminer_v3: AuthPassword = AuthPassword(alt="", default="super")


_auth_config = AuthConfig()


def get_auth(key: str) -> AuthPassword | None:
    try:
        return getattr(_auth_config, key)
    except AttributeError:
        if hasattr(_auth_config, "__dict__") and key in _auth_config.__dict__:
            return _auth_config.__dict__[key]
        return None


def get_auth_list(key: str) -> list[str]:
    a = get_auth(key)
    if a is not None:
        return a.as_list()
    return []


def set_auth_alt(key: str, alt: str) -> None:
    a = get_auth(key)
    if a is not None:
        a.alt = alt
        if hasattr(_auth_config, key):
            setattr(_auth_config, key, a)


class Settings(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)
    http_request_timeout: float = Field(default=5.0)
    rpc_blocking_timeout: float = Field(default=10.0)
    tcp_blocking_timeout: float = Field(default=10.0)
    locate_duration_ms: int = Field(default=10000)


_settings = Settings()


def get(key: str, other: Any | None = None) -> Any:
    try:
        return getattr(_settings, key)
    except AttributeError:
        if hasattr(_settings, "__dict__") and key in _settings.__dict__:
            return _settings.__dict__[key]
        return other


def update(key: str, val: Any) -> None:
    if hasattr(_settings, key):
        setattr(_settings, key, val)
    else:
        _settings.__dict__[key] = val
