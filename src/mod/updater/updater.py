# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import logging
import os
import platform
import re
import subprocess

import requests
from PySide6.QtCore import QObject, QThread, Signal

from utils import CURR_PLATFORM

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
REPO = "bitcap-co/bitcap-ipr"
LATEST_RELEASE_URL = f"{GITHUB_API}/repos/{REPO}/releases/latest"
RELEASES_URL = f"{GITHUB_API}/repos/{REPO}/releases"
REQUEST_TIMEOUT = 10
DOWNLOAD_CHUNK_SIZE = 1024 * 64

# Preferred installer file extension per platform. Assets ending with the
# matching extension are treated as installers and preferred over portable
# archives when selecting a download.
INSTALLER_EXTS = {
    "windows": ".exe",
    "macos": ".dmg",
    "linux": ".deb",
}

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")
# Pre-release tag marker used by this project: a base version followed by a
# '-rp-<feature>' suffix, e.g. 'v1.4.2-rp-hivegpu'. The suffix is free text
# (a feature name), so previews of the same base have no order among
# themselves; each is a preview of that upcoming base version.
_PRERELEASE_RE = re.compile(r"-rp-\S+", re.IGNORECASE)


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


def is_prerelease(version: str) -> bool:
    """Whether a version tag is a pre-release preview ('-rp-<feature>').

    Args:
        version (str): the version string to inspect.

    Returns:
        bool: True if the tag carries a '-rp-' pre-release suffix.
    """
    return bool(_PRERELEASE_RE.search(version or ""))


def version_key(version: str) -> tuple[tuple[int, ...], int]:
    """Build a sortable key for a version tag, pre-release aware.

    Orders by numeric base version first, then places pre-release previews
    (e.g. 'v1.4.2-rp-hivegpu') before the matching final release of the same
    base. Previews of the same base have equal keys; callers relying on this
    for selection should break ties by source order (newest first).

    Args:
        version (str): the version string to key.

    Returns:
        tuple: a key suitable for sorting / max().
    """
    return (parse_version(version), 0 if is_prerelease(version) else 1)


def is_newer(latest: str, current: str) -> bool:
    """Check if latest is a strictly newer version than current.

    A pre-release tag (e.g. 'v1.4.2-rp-hivegpu') previews an upcoming base
    version, so it is newer than any older release and is itself superseded
    by the matching final release. Two different previews of the same base
    are not comparable and never report newer than one another.

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
    if latest_v != current_v:
        return latest_v > current_v
    # same base version: only a final release supersedes a preview of it.
    return not is_prerelease(latest) and is_prerelease(current)


_GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _release_info(data: dict) -> dict:
    """Normalize a GitHub release payload into our release info shape."""
    tag = data.get("tag_name", "")
    return {
        "tag": tag,
        "name": data.get("name") or tag,
        "url": data.get("html_url", ""),
        "body": data.get("body") or "",
        "prerelease": bool(data.get("prerelease")),
        "assets": [
            {
                "name": asset.get("name", ""),
                "url": asset.get("browser_download_url", ""),
                "size": asset.get("size", 0),
            }
            for asset in data.get("assets", [])
        ],
    }


def fetch_latest_release(
    include_prereleases: bool = False, timeout: int = REQUEST_TIMEOUT
) -> dict:
    """Fetch the latest release from the GitHub repository.

    By default only published, non-pre-release versions are considered (the
    'releases/latest' endpoint). When include_prereleases is True the full
    release list is fetched and the highest version is chosen, so a newer
    pre-release preview (e.g. 'vX.Y.Z-rp-N') is picked up when one exists.

    Args:
        include_prereleases (bool): also consider pre-release versions.
        timeout (int): request timeout in seconds.

    Returns:
        dict: release info with keys 'tag', 'name', 'url', 'body',
        'prerelease' and 'assets'. Empty 'tag' when nothing is found.

    Raises:
        requests.RequestException: on network or HTTP errors.
    """
    if not include_prereleases:
        resp = requests.get(
            LATEST_RELEASE_URL, headers=_GITHUB_HEADERS, timeout=timeout
        )
        resp.raise_for_status()
        return _release_info(resp.json())

    resp = requests.get(RELEASES_URL, headers=_GITHUB_HEADERS, timeout=timeout)
    resp.raise_for_status()
    # GitHub returns releases newest-first; max() keeps the first of any tie,
    # so competing previews of the same base resolve to the most recent one.
    releases = [
        release for release in resp.json() if not release.get("draft")
    ]
    if not releases:
        return _release_info({})
    latest = max(releases, key=lambda r: version_key(r.get("tag_name", "")))
    return _release_info(latest)


def get_platform() -> tuple[str, bool]:
    """Resolve the running platform and architecture.

    Returns:
        tuple[str, bool]: the platform name ('windows', 'macos' or 'linux')
        and whether the machine is ARM-based.
    """
    machine = platform.machine().lower()
    is_arm = machine in ("arm64", "aarch64")
    if CURR_PLATFORM.startswith("win"):
        return "windows", is_arm
    if CURR_PLATFORM == "darwin":
        return "macos", is_arm
    return "linux", is_arm


def _matches_os(name: str, os_name: str) -> bool:
    name = name.lower()
    if os_name == "windows":
        return "win" in name
    if os_name == "macos":
        return any(token in name for token in ("macos", "darwin", "osx"))
    return any(token in name for token in ("ubuntu", "linux", "debian"))


def _matches_arch(name: str, is_arm: bool) -> bool:
    name = name.lower()
    has_arm = "arm64" in name or "aarch64" in name
    if is_arm:
        return has_arm
    if has_arm:
        return False
    return any(token in name for token in ("x64", "amd64", "x86_64", "intel"))


def select_asset(
    assets: list[dict],
    os_name: str,
    is_arm: bool,
    prefer_installer: bool = True,
) -> dict | None:
    """Pick the best release asset for the given platform.

    Filters assets to those matching the platform and architecture, then
    ranks them so an installer is preferred over a portable archive (or the
    reverse when prefer_installer is False). Ties break on asset name so the
    selection is deterministic.

    Args:
        assets (list[dict]): release assets with 'name', 'url' and 'size'.
        os_name (str): platform name ('windows', 'macos' or 'linux').
        is_arm (bool): whether the target machine is ARM-based.
        prefer_installer (bool): prefer an installer over a portable archive.

    Returns:
        dict | None: the chosen asset, or None if nothing matches.
    """
    ext = INSTALLER_EXTS.get(os_name, "")
    candidates = [
        asset
        for asset in assets
        if asset.get("name")
        and _matches_os(asset["name"], os_name)
        and _matches_arch(asset["name"], is_arm)
    ]
    if not candidates:
        return None

    def rank(asset: dict) -> tuple[int, str]:
        is_installer = bool(ext) and asset["name"].lower().endswith(ext)
        return (1 if is_installer == prefer_installer else 0, asset["name"].lower())

    return max(candidates, key=rank)


class UpdateChecker(QThread):
    """Checks GitHub for a newer release in a background thread.

    Runs a single check on start() and emits exactly one of its result
    signals. Network work happens off the UI thread so the app stays
    responsive while the check is in flight.

    Args:
        current_version (str): the running version to compare against.
        include_prereleases (bool): also consider pre-release versions.
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

    def __init__(
        self,
        current_version: str,
        include_prereleases: bool = False,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._current = current_version
        self._include_prereleases = include_prereleases

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}"

    def run(self) -> None:
        logger.info(" checking for updates...")
        try:
            release = fetch_latest_release(self._include_prereleases)
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


class UpdateDownloader(QThread):
    """Downloads a release asset to disk in a background thread.

    Streams the asset to dest_path, emitting progress as it goes. The
    download can be cancelled; a partial or cancelled download is removed.

    Args:
        url (str): the asset download URL.
        dest_path (str): the local file path to write to.
        parent (QObject): parent object.

    Signals:
        progress (int, int): emits (bytes received, total bytes). total is 0
            when the server does not report a content length.
        completed (str): emits the saved file path on success.
        error (str): emits the error message on failure.
    """

    # Signals
    progress = Signal(int, int)
    completed = Signal(str)
    error = Signal(str)

    def __init__(self, url: str, dest_path: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._url = url
        self._dest = dest_path
        self._cancelled = False

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}"

    def cancel(self) -> None:
        """Request cancellation of the in-progress download."""
        self._cancelled = True

    def _cleanup(self) -> None:
        try:
            if os.path.exists(self._dest):
                os.remove(self._dest)
        except OSError as exc:
            logger.warning(f" failed to remove partial download: {exc}")

    def run(self) -> None:
        logger.info(f" downloading update from {self._url}")
        try:
            with requests.get(self._url, stream=True, timeout=REQUEST_TIMEOUT) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("Content-Length", 0))
                received = 0
                with open(self._dest, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                        if self._cancelled:
                            logger.info(" download cancelled.")
                            break
                        if chunk:
                            f.write(chunk)
                            received += len(chunk)
                            self.progress.emit(received, total)
        except (requests.RequestException, OSError) as exc:
            logger.error(f" download failed: {exc}")
            self._cleanup()
            self.error.emit(str(exc))
            return
        if self._cancelled:
            self._cleanup()
            return
        logger.info(f" download complete: {self._dest}")
        self.completed.emit(self._dest)


class DebInstaller(QThread):
    """Installs a .deb package via pkexec in a background thread.

    Runs `pkexec dpkg -i <deb>`, which raises a graphical polkit prompt for
    authentication and then installs as root. dpkg is used directly because
    the package is standalone and declares no dependencies. After install the
    package version is queried and compared against the version in the .deb to
    confirm the upgrade actually took effect. UI work stays off the main
    thread so the app does not freeze while installing.

    Args:
        deb_path (str): path to the .deb package to install.
        parent (QObject): parent object.

    Signals:
        completed (str): emits the installed package version on success.
        error (str): emits the error message when the install fails.
    """

    PACKAGE_NAME = "bitcap-ipr"

    # Signals
    completed = Signal(str)
    error = Signal(str)

    def __init__(self, deb_path: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._deb = deb_path

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}"

    @staticmethod
    def _query(args: list[str]) -> str:
        try:
            proc = subprocess.run(args, capture_output=True, text=True)
        except OSError:
            return ""
        return proc.stdout.strip() if proc.returncode == 0 else ""

    def run(self) -> None:
        logger.info(f" installing {self._deb} via pkexec dpkg")
        # version the package will install to (read from the .deb, no root).
        expected = self._query(["dpkg-deb", "-f", self._deb, "Version"])
        try:
            proc = subprocess.run(
                ["pkexec", "dpkg", "-i", self._deb],
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            logger.error(f" install failed: {exc}")
            self.error.emit(str(exc))
            return
        if proc.returncode != 0:
            # pkexec returns 126 when authentication is dismissed/denied.
            message = proc.stderr.strip() or (
                f"dpkg exited with code {proc.returncode}"
            )
            logger.error(f" install failed: {message}")
            self.error.emit(message)
            return
        # confirm the installed version now matches the package version.
        installed = self._query(
            ["dpkg-query", "-W", "-f=${Version}", self.PACKAGE_NAME]
        )
        if expected and installed != expected:
            message = (
                f"install reported success but the installed version "
                f"'{installed or 'unknown'}' does not match the expected "
                f"version '{expected}'."
            )
            logger.error(f" install verification failed: {message}")
            self.error.emit(message)
            return
        logger.info(f" install complete; verified version {installed}.")
        self.completed.emit(installed)
