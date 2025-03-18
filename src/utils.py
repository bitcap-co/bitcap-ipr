import os
import sys
import json
from pathlib import Path
from platformdirs import user_data_dir, user_log_dir
from PySide6.QtCore import __version__ as QT_VERSION

APP_INFO = {
    "name": "BitCap IPReporter",
    "appname": "BitCapIPR",
    "appversion": "1.2.3",
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


def get_stylesheet():
    return Path(BASEDIR, "ui", "theme.qss")


def get_default_config():
    return Path(BASEDIR, "resources", "app", "config.json.default")


def get_config_path():
    if os.path.exists(Path(BASEDIR, "..", "README.md")):
        cp = Path(BASEDIR, "..").as_posix()
    else:
        cp = user_data_dir(APP_INFO["appname"], APP_INFO["appauthor"])
    return cp


def get_config(cp: Path) -> dict:
    with open(cp, "r") as f:
        c = json.load(f)
    return c


def get_log_path():
    if os.path.exists(Path(BASEDIR, "..", "README.md")):
        lp = Path(BASEDIR, "..", "Logs").as_posix()
    else:
        lp = user_log_dir(APP_INFO["appname"], APP_INFO["appauthor"])
    return lp


def flush_log(p: Path):
    with open(p, "r+") as f:
        f.truncate(0)
        f.seek(0)
