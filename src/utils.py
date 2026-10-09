# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from platformdirs import user_data_path, user_downloads_path, user_log_path
from PySide6.QtCore import qVersion

from metadata import APP_METADATA

CURR_PLATFORM = sys.platform
BASEDIR = os.path.dirname(__file__)
IPR_THEME = Path(BASEDIR, "ui", "theme.qss")
IPR_METADATA = {
    **APP_METADATA,
    "qt": qVersion(),
    "python": ".".join(map(str, sys.version_info[:3])),
}

MAX_ROTATE_LOG_FILES = 4
MIN_DATETIME = datetime(1, 1, 1, 0, 0, tzinfo=timezone.utc)


def is_portable() -> bool:
    """Returns whether the application is installed as a portable archive."""
    return os.path.exists(Path(BASEDIR, "..", "README.md"))


def get_installed_dir() -> Path:
    """Returns the base directory of the installed application."""
    # Portable: return the parent directory based from current directory of self.
    if is_portable():
        return Path(BASEDIR, "..")
    return user_data_path(IPR_METADATA["appname"], IPR_METADATA["appauthor"])


def get_log_dir() -> Path:
    """Returns the log directory of the installed application."""
    if is_portable():
        return Path(BASEDIR, "..", "Logs")
    return user_log_path(IPR_METADATA["appname"], IPR_METADATA["appauthor"])


def get_config_file() -> Path:
    """Returns the path to the current configuration file."""
    return Path(get_installed_dir(), "config.json")


def get_log_file() -> Path:
    """Returns the path to the current log file."""
    return Path(get_log_dir(), "ipr.log")


def get_download_dir() -> Path:
    """Returns the path to the user's download directory."""
    return user_downloads_path()


def flush_log() -> None:
    """Flushes the current log file."""
    with open(get_log_file(), "r+") as f:
        _ = f.truncate(0)
        _ = f.seek(0)


def normalize_datetime(datetime_obj: datetime | None) -> str:
    """
    Normalize datetime to local string format: YYYY-MM-DD HH:MM:SS.

    Returns "N/A" for the min datetime (1/1/1 00:00:00)
    """
    if datetime_obj is None or datetime_obj == MIN_DATETIME:
        return "N/A"
    return datetime_obj.astimezone().strftime("%Y-%m-%d %H:%M:%S")
