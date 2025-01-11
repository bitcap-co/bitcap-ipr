import os
import sys
import json
from pathlib import Path
from platformdirs import user_data_dir, user_log_dir

BASEDIR = os.path.dirname(__file__)
CURR_PLATFORM = sys.platform
APP_INFO = {
    "name": "BitCap IPReporter",
    "appname": "BitCapIPR",
    "version": "1.2.1",
    "appauthor": "BitCap",
    "author": "MatthewWertman",
    "source": "https://github.com/bitcap-co/bitcap-ipr",
    "company": "Bit Capital Group",
    "desc": "cross-platform IP reporter that listens for AntMiner, IceRiver, and Whatsminer ASICs.",
}
MAX_ROTATE_LOG_FILES = 4
MAX_LOG_SIZE_LIMIT = 4096


def get_default_config():
    return Path(BASEDIR, "resources", "app", "config.json.default")


def get_config_path():
    if os.path.exists(Path(BASEDIR, "..", "README.md")):
        cp = Path(BASEDIR, "..")
    else:
        cp = user_data_dir(APP_INFO["appname"], APP_INFO["appauthor"])
    return cp


def get_config(cp: Path):
    with open(cp, "r") as f:
        config = json.load(f)
    return config


def get_log_path():
    if os.path.exists(Path(BASEDIR, "..", "README.md")):
        lp = Path(BASEDIR, "..", "Logs")
    else:
        lp = user_log_dir(APP_INFO["appname"], APP_INFO["appauthor"])
    return lp


def flush_log(p: Path):
    with open(p, "r+") as f:
        f.truncate(0)
        f.seek(0)
