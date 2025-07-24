from typing import Any

# global default api settings
_gs = {
    "http_max_retries": 3,
    "http_max_delay": 5,
    "http_jitter_delay": False,
    "http_request_timeout": 5.0,
    "rpc_request_timeout": 10.0,
    "locate_duration_ms": 10000,
    # default authentication
    "default_bitmain_passwd": "root",
    "default_vnish_passwd": "admin",
    "default_whatsminer_passwd": "admin",
    "default_iceriver_passwd": "12345678",
    "default_pbfarmer_auth": "5b281acc-de86-41bb-b14d-e266d9c9edbd",
    "default_goldshell_passwd": "123456789",
    "default_volcminer_passwd": "ltc@dog",
    "default_sealminer_passwd": "seal",
    "default_elphapex_passwd": "root",
    "default_dragonball_passwd": "dragonball",
}


def get(k: str, default: Any = None) -> Any:
    return _gs.get(k, default)


def update(k: str, v: Any) -> Any:
    _gs[k] = v
