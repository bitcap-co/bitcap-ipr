# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
import os
import shlex
import shutil
import subprocess
import webbrowser
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QWidget

from ui.widgets.ipr import IPRMessage, IPRProgress
from utils import CURR_PLATFORM, IPR_METADATA, get_download_dir

from .updater import (
    DebInstaller,
    IPRReleaseInfo,
    UpdateChecker,
    UpdateDownloader,
    get_platform,
    select_asset,
)

logger = logging.getLogger(__name__)


class UpdateController(QObject):
    """Coordinates update checks, downloads, installation, and update dialogs."""

    notification_requested: Signal = Signal(str, int)
    status_clear_requested: Signal = Signal()
    check_enabled_changed: Signal = Signal(bool)
    quit_requested: Signal = Signal()

    def __init__(
        self,
        parent: QWidget,
        current_version: str,
        include_prereleases: Callable[[], bool],
    ) -> None:
        super().__init__(parent)
        self._window: QWidget = parent
        self._current_version: str = current_version
        self._include_prereleases: Callable[[], bool] = include_prereleases
        self._check_silent: bool = False
        self._checker: UpdateChecker | None = None
        self._downloader: UpdateDownloader | None = None
        self._download_dialog: IPRProgress | None = None
        self._installer: DebInstaller | None = None
        self._install_dialog: IPRProgress | None = None

    def check_for_updates(self, silent: bool = False) -> None:
        if self._checker and self._checker.isRunning():
            return
        self._check_silent = silent
        self.check_enabled_changed.emit(False)
        self._checker = UpdateChecker(
            self._current_version,
            self._include_prereleases(),
            self,
        )
        self._checker.update_available.connect(self._on_update_available)
        self._checker.up_to_date.connect(self._on_up_to_date)
        self._checker.error.connect(self._on_update_error)
        self._checker.finished.connect(lambda: self.check_enabled_changed.emit(True))
        self.notification_requested.emit("Status :: Checking for updates...", 3000)
        self._checker.start()

    def _on_update_available(self, release: IPRReleaseInfo) -> None:
        self.status_clear_requested.emit()
        kind = "pre-release" if release.prerelease else "version"
        status_kind = "Pre-release" if release.prerelease else "Update"
        self.notification_requested.emit(f"Status :: {status_kind} available!", 3000)
        dialog = IPRMessage(
            self._window,
            "Update Available",
            f"A new {kind} of {IPR_METADATA['name']} is available: {release.name}\n"
            f"You are currently running {self._current_version}.",
            action_text="Download",
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.download_update(release)

    def download_update(self, release: IPRReleaseInfo) -> None:
        os_name, is_arm = get_platform()
        asset = select_asset(release.assets, os_name, is_arm)
        if not asset:
            logger.warning(" no matching release asset; opening release page.")
            webbrowser.open(
                release.url or f"{IPR_METADATA['source']}/releases/latest", new=2
            )
            return

        destination = Path(get_download_dir(), asset.name)
        logger.info(f" downloading update asset {asset.name} to {destination}")
        self._download_dialog = IPRProgress(
            self._window,
            "Downloading Update",
            f"Downloading {asset.name}...",
        )
        self._download_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._downloader = UpdateDownloader(asset.url, str(destination), self)
        self._downloader.progress.connect(self._download_dialog.set_progress)
        self._downloader.completed.connect(self._on_download_complete)
        self._downloader.error.connect(self._on_download_error)
        self._download_dialog.cancelled.connect(self._downloader.cancel)
        self.notification_requested.emit("Status :: Downloading update...", 3000)
        self._downloader.start()
        self._download_dialog.show()

    def _close_download_dialog(self) -> None:
        if self._download_dialog:
            self._download_dialog.close()
            self._download_dialog = None

    def _on_download_complete(self, path: str) -> None:
        self._close_download_dialog()
        self.notification_requested.emit("Status :: Update downloaded.", 3000)
        dialog = IPRMessage(
            self._window,
            "Download Complete",
            f"The update was saved to:\n{path}\n\n"
            "Install now? The application will close to complete installation.",
            action_text="Install",
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.install_update(path)

    def _on_download_error(self, error: str) -> None:
        self._close_download_dialog()
        logger.error(f" failed to download update: {error}")
        self.notification_requested.emit("Status :: Download failed.", 5000)
        IPRMessage(
            self._window,
            "Download Failed",
            f"Could not download the update. Please try again later.\n\n{error}",
        ).exec()

    def install_update(self, path: str) -> None:
        logger.info(f" installing update from {path}")
        if CURR_PLATFORM.startswith("win") and path.lower().endswith(".exe"):
            self._install_windows(path)
        elif (
            CURR_PLATFORM.startswith("linux")
            and path.lower().endswith(".deb")
            and shutil.which("pkexec")
            and shutil.which("apt-get")
        ):
            self._install_deb(path)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            self.quit_requested.emit()

    def _install_windows(self, path: str) -> None:
        subprocess.Popen(
            [path, "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
            close_fds=True,
        )
        self.quit_requested.emit()

    def _install_deb(self, path: str) -> None:
        self._install_dialog = IPRProgress(
            self._window,
            "Installing Update",
            "Installing update... You may be prompted for your password.",
            cancellable=False,
        )
        self._install_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._installer = DebInstaller(path, self)
        self._installer.completed.connect(self._on_install_complete)
        self._installer.error.connect(self._on_install_error)
        self.notification_requested.emit("Status :: Installing update...", 3000)
        self._installer.start()
        self._install_dialog.show()

    def _close_install_dialog(self) -> None:
        if self._install_dialog:
            self._install_dialog.close()
            self._install_dialog = None

    def _on_install_complete(self, version: str) -> None:
        self._close_install_dialog()
        self.notification_requested.emit("Status :: Update installed.", 3000)
        installed = f" (version {version})" if version else ""
        dialog = IPRMessage(
            self._window,
            "Update Installed",
            f"The update was installed successfully{installed}.\n\n"
            "Restart now to use the new version?",
            action_text="Restart",
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._relaunch()
            self.quit_requested.emit()

    def _on_install_error(self, error: str) -> None:
        self._close_install_dialog()
        logger.error(f" failed to install update: {error}")
        self.notification_requested.emit("Status :: Install failed.", 5000)
        IPRMessage(
            self._window,
            "Install Failed",
            f"Could not install the update.\n\n{error}",
        ).exec()

    def _relaunch(self) -> None:
        bin_path = "/opt/bitcap-ipr/BitCapIPR"
        if not os.path.exists(bin_path):
            logger.info(" installed binary not found; skipping relaunch.")
            return
        try:
            subprocess.Popen(
                ["sh", "-c", f"sleep 1; exec {shlex.quote(bin_path)}"],
                close_fds=True,
            )
        except OSError as exc:
            logger.warning(f" failed to relaunch app: {exc}")

    def _on_up_to_date(self, current: str) -> None:
        self.status_clear_requested.emit()
        self.notification_requested.emit("Status :: Up to date.", 3000)
        if not self._check_silent:
            IPRMessage(
                self._window,
                "No Updates",
                f"You are running the latest version ({current}).",
            ).exec()

    def _on_update_error(self, error: str) -> None:
        self.status_clear_requested.emit()
        self.notification_requested.emit("Status :: Failed to check for updates.", 5000)
        logger.error(f" failed to check for updates: {error}")
        if not self._check_silent:
            IPRMessage(
                self._window,
                "Update Check Failed",
                f"Could not check for updates. Please try again later.\n\n{error}",
            ).exec()

    def stop(self) -> None:
        """Stop or wait for updater threads before application shutdown."""
        if self._downloader and self._downloader.isRunning():
            logger.info(" cancelling in-progress update download.")
            self._downloader.cancel()
            if not self._downloader.wait(5000):
                self._downloader.terminate()
                self._downloader.wait()
        if self._checker and self._checker.isRunning():
            logger.info(" waiting for update check to finish.")
            if not self._checker.wait(3000):
                self._checker.terminate()
                self._checker.wait()
        if self._installer and self._installer.isRunning():
            logger.info(" waiting for update install to finish.")
            if not self._installer.wait(3000):
                self._installer.terminate()
                self._installer.wait()
