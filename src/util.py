import sys
from platformdirs import *

curr_platform = sys.platform

app_info = {
    "name": "BitCap IPReporter",
    "appname": "BitCapIPR",
    "version": "1.1.0",
    "appauthor": "BitCap",
    "author": "MatthewWertman",
    "source": "https://github.com/bitcap-co/bitcap-ipr",
    "company": "Bit Capital Group",
    "desc": "cross-platform IP\nReporter that listens for AntMiners, IceRivers,\nand Whatsminers.",
}

config_path = user_data_dir(app_info["appname"], app_info["appauthor"])
log_path = user_log_dir(app_info["appname"], app_info["appauthor"])
