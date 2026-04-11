# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import collections.abc
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from platformdirs import user_data_dir, user_log_dir
from PySide6.QtCore import qVersion

CURR_PLATFORM = sys.platform
BASEDIR = os.path.dirname(__file__)
IPR_THEME = Path(BASEDIR, "ui", "theme.qss")
IPR_DEFAULT_CONFIG = Path(BASEDIR, "resources", "app", "config.json.default")
IPR_METADATA = {
    "name": "BitCap IPReporter",
    "appname": "BitCapIPR",
    "appversion": "1.2.9",
    "qt": qVersion(),
    "python": ".".join(map(str, sys.version_info[:3])),
    "appauthor": "BitCap",
    "author": "MatthewWertman",
    "source": "https://github.com/bitcap-co/bitcap-ipr",
    "company": "Bit Capital Group",
    "desc": "cross-platform IP reporter that listens for AntMiner, IceRiver, and Whatsminer ASICs.",
}
MAX_ROTATE_LOG_FILES = 4


def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), dict(v))
        # elif isinstance(v, list):
        #     d[k] = (d.get(k, []) + v)
        else:
            d[k] = v
    return d


def get_config_dir() -> str:
    if os.path.exists(Path(BASEDIR, "..", "README.md")):
        cd = Path(BASEDIR, "..").as_posix()
    else:
        cd = user_data_dir(IPR_METADATA["appname"], IPR_METADATA["appauthor"])
    return cd


def get_config_file_path() -> Path:
    return Path(get_config_dir(), "config.json")


def read_config(fp: Path) -> Dict[str, Any]:
    with open(fp, "r") as f:
        c = json.load(f)
    return c


def write_config(fp: Path, conf: Dict[str, Any]) -> None:
    config = json.dumps(conf, indent=2)
    with open(fp, "w") as f:
        f.write(config)


def get_log_dir() -> str:
    if os.path.exists(Path(BASEDIR, "..", "README.md")):
        ld = Path(BASEDIR, "..", "Logs").as_posix()
    else:
        ld = user_log_dir(IPR_METADATA["appname"], IPR_METADATA["appauthor"])
    return ld


def get_log_file_path() -> Path:
    return Path(get_log_dir(), "ipr.log")


def flush_log():
    with open(get_log_file_path(), "r+") as f:
        f.truncate(0)
        f.seek(0)
