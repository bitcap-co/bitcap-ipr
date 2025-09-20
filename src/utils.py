import os
import sys
import json
import collections.abc
from pathlib import Path
from platformdirs import user_data_dir, user_log_dir
from PySide6.QtCore import __version__ as QT_VERSION

APP_INFO = {
    "name": "BitCap IPReporter",
    "appname": "BitCapIPR",
    "appversion": "1.2.8",
    "qt": QT_VERSION,
    "python": ".".join(map(str, sys.version_info[:3])),
    "appauthor": "BitCap",
    "author": "MatthewWertman",
    "source": "https://github.com/bitcap-co/bitcap-ipr",
    "company": "Bit Capital Group",
    "desc": "cross-platform IP reporter that listens for AntMiner, IceRiver, and Whatsminer ASICs.",
}
BASEDIR = os.path.dirname(__file__)
CURR_PLATFORM = sys.platform
MAX_ROTATE_LOG_FILES = 4


def deep_update(d: dict, u: dict) -> dict:
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        # elif isinstance(v, list):
        #     d[k] = (d.get(k, []) + v)
        else:
            d[k] = v
    return d


def get_stylesheet():
    return Path(BASEDIR, "ui", "theme.qss")


def get_default_config():
    return Path(BASEDIR, "resources", "app", "config.json.default")


def get_config_dir() -> str:
    if os.path.exists(Path(BASEDIR, "..", "README.md")):
        cd = Path(BASEDIR, "..").as_posix()
    else:
        cd = user_data_dir(APP_INFO["appname"], APP_INFO["appauthor"])
    return cd


def get_config_file_path() -> Path:
    return Path(get_config_dir(), "config.json")


def read_config(cp: Path) -> dict:
    with open(cp, "r") as f:
        c = json.load(f)
    return c


def write_config(cp: Path, content: dict):
    config = json.dumps(content, indent=2)
    with open(cp, "w") as f:
        f.write(config)


def get_log_dir() -> str:
    if os.path.exists(Path(BASEDIR, "..", "README.md")):
        ld = Path(BASEDIR, "..", "Logs").as_posix()
    else:
        ld = user_log_dir(APP_INFO["appname"], APP_INFO["appauthor"])
    return ld


def get_log_file_path() -> Path:
    return Path(get_log_dir(), "ipr.log")


def flush_log():
    with open(get_log_file_path(), "r+") as f:
        f.truncate(0)
        f.seek(0)


def get_miner_url(ip_addr: str, miner_type: str) -> str:
    port = 80
    match miner_type:
        case "dragonball":
            port = 16666
    return f"http://{ip_addr}:{port}/"
