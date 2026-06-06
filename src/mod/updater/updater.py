# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import logging
import re

import requests
from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
REPO = "bitcap-co/bitcap-ipr"
LATEST_RELEASE_URL = f"{GITHUB_API}/repos/{REPO}/releases/latest"
REQUEST_TIMEOUT = 10

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a version string into a comparable tuple of ints.

    Leading non-numeric characters (e.g. a 'v' tag prefix) and any
    pre-release/build suffix are ignored. 'v1.3.1' -> (1, 3, 1).

    Args:
        version (str): the version string to parse.

    Returns:
        tuple[int, ...]: the numeric version components. Empty if none found.
    """
    if not version:
        return ()
    match = _VERSION_RE.search(version)
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(latest: str, current: str) -> bool:
    """Check if latest is a strictly newer version than current.

    Args:
        latest (str): the candidate (remote) version string.
        current (str): the running (local) version string.

    Returns:
        bool: True if latest is newer than current, otherwise False.
    """
    latest_v, current_v = parse_version(latest), parse_version(current)
    if not latest_v:
        return False
    length = max(len(latest_v), len(current_v))
    latest_v += (0,) * (length - len(latest_v))
    current_v += (0,) * (length - len(current_v))
    return latest_v > current_v


def fetch_latest_release(timeout: int = REQUEST_TIMEOUT) -> dict:
    """Fetch the latest release from the GitHub repository.

    Args:
        timeout (int): request timeout in seconds.

    Returns:
        dict: release info with keys 'tag', 'name', 'url' and 'body'.

    Raises:
        requests.RequestException: on network or HTTP errors.
    """
    resp = requests.get(
        LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    tag = data.get("tag_name", "")
    return {
        "tag": tag,
        "name": data.get("name") or tag,
        "url": data.get("html_url", ""),
        "body": data.get("body") or "",
    }


class UpdateChecker(QThread):
    """Checks GitHub for a newer release in a background thread.

    Runs a single check on start() and emits exactly one of its result
    signals. Network work happens off the UI thread so the app stays
    responsive while the check is in flight.

    Args:
        current_version (str): the running version to compare against.
        parent (QObject) : parent object.

    Signals:
        update_available (dict): emits release info when a newer version exists.
        up_to_date (str): emits the current version when already up to date.
        error (str): emits the error message when the check fails.
    """

    # Signals
    update_available = Signal(dict)
    up_to_date = Signal(str)
    error = Signal(str)

    def __init__(self, current_version: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._current = current_version

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}"

    def run(self) -> None:
        logger.info(" checking for updates...")
        try:
            release = fetch_latest_release()
        except requests.RequestException as exc:
            logger.error(f" update check failed: {exc}")
            self.error.emit(str(exc))
            return
        if is_newer(release["tag"], self._current):
            logger.info(f" update available: {release['tag']}")
            self.update_available.emit(release)
        else:
            logger.info(" no update available.")
            self.up_to_date.emit(self._current)
