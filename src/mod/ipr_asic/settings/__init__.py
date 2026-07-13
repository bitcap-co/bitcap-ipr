from ssl import SSLContext
from typing import Any

import httpx
from httpx import AsyncHTTPTransport
from pydantic import BaseModel, ConfigDict, Field


class AuthPassword(BaseModel):
    alt: str
    default: str

    def as_list(self) -> list[str]:
        return [self.alt, self.default]


class AuthConfig(BaseModel):
    antminer: AuthPassword = AuthPassword(alt="", default="root")


_auth_config = AuthConfig()


def get_auth(key: str) -> AuthPassword | None:
    """get_auth returns AuthPassword of key if exists."""
    try:
        return getattr(_auth_config, key)
    except AttributeError:
        if hasattr(_auth_config, "__dict__") and key in _auth_config.__dict__:
            return _auth_config.__dict__[key]
        return None


def get_auth_list(key: str) -> list[str]:
    """get_auth_list returns stored alt & default passwords for key as list. Returns empty if key is not found."""
    a = get_auth(key)
    if a is not None:
        return a.as_list()
    return []


def set_alt_auth(key: str, alt: str) -> None:
    """set_alt_auth sets alt as alternative password for key."""
    a = get_auth(key)
    if a is not None:
        a.alt = alt
        if hasattr(_auth_config, key):
            setattr(_auth_config, key, a)


class Settings(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)
    discover_get_retries: int = Field(default=1)
    discover_get_timeout: int = Field(default=3)
    get_data_retries: int = Field(default=1)
    api_function_timeout: int = Field(default=5)
    led_locate_duration_ms: int = Field(default=10000)


_settings = Settings()

ssl_cxt = httpx.create_ssl_context()


def transport(verify: str | bool | SSLContext = ssl_cxt):
    return AsyncHTTPTransport(verify=verify)


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
