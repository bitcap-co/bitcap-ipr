import os
import sys
from pathlib import Path
from platformdirs import user_data_dir, user_log_dir

curr_platform = sys.platform

app_info = {
    "name": "BitCap IPReporter",
    "appname": "BitCapIPR",
    "version": "1.1.0",
    "appauthor": "BitCap",
    "author": "MatthewWertman",
    "source": "https://github.com/bitcap-co/bitcap-ipr",
    "company": "Bit Capital Group",
    "desc": "cross-platform IP reporter that listens for AntMiner, IceRiver, and Whatsminer ASICs.",
}

basedir = os.path.dirname(__file__)

def get_config_path():
    if os.path.exists(Path(basedir, "..", "README.md")):
        cp = Path(basedir, "..")
    else:
        cp = user_data_dir(app_info["appname"], app_info["appauthor"])
    return cp

def get_log_path():
    if os.path.exists(Path(basedir, "..", "README.md")):
        lp = Path(basedir, "..", "Logs")
    else:
        lp = user_log_dir(app_info["appname"], app_info["appauthor"])
    return lp