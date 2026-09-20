# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import QFile, QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QLineEdit,
    QTabWidget,
    QWidget,
)

from mod.ipr_asic import ASICClient, MinerResult
from mod.ipr_asic import settings as api_settings
from mod.ipr_asic.data import MinerFirmware, MinerType
from mod.ipr_asic.errors import APIError, UnknownClientError
from mod.ipr_asic.firmware import BitmainFirmwareImage, FirmwareImageError
from mod.ipr_asic.schemas.antminer import VersionInfo as AntminerVersionInfo

from ..message import IPRMessage
from .action_controller import MinerActionController
from .controller import IPRTableController
from .model import COL_IP

logger = logging.getLogger(__name__)

AuthProvider = Callable[[str], str | None]
PresetWriter = Callable[[], object]


class PoolConfiguratorWidgets(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    preset: QComboBox
    urls: tuple[QLineEdit, QLineEdit, QLineEdit]
    users: tuple[QLineEdit, QLineEdit, QLineEdit]
    passwords: tuple[QLineEdit, QLineEdit, QLineEdit]
    automatic_worker_names: QCheckBox


class PasswordConfiguratorWidgets(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    current: QLineEdit
    new: QLineEdit
    confirm: QLineEdit
    use_non_default: QCheckBox
    use_antminer_login: QCheckBox
    alternatives: dict[MinerType, QLineEdit]


class FirmwareConfiguratorWidgets(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    firmware_path: QLineEdit
    enforce_compatibility: QCheckBox
    keep_settings: QCheckBox


class MinerConfiguratorWidgets(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    panel: QWidget
    tabs: QTabWidget
    show_action: QAction
    get_pool_action: QAction
    set_pool_action: QAction
    pools: PoolConfiguratorWidgets
    passwords: PasswordConfiguratorWidgets
    firmware: FirmwareConfiguratorWidgets


class MinerConfiguratorDependencies(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    table_controller: IPRTableController
    action_controller: MinerActionController
    asic: ASICClient
    auth_provider: AuthProvider
    write_pool_preset: PresetWriter


class MinerConfiguratorController(QObject):
    """Coordinates the pool and password configurator workflows."""

    notification_requested: Signal = Signal(str, int)

    def __init__(
        self,
        parent: QWidget,
        widgets: MinerConfiguratorWidgets,
        dependencies: MinerConfiguratorDependencies,
    ) -> None:
        super().__init__(parent)
        self._window: QWidget = parent
        self._widgets: MinerConfiguratorWidgets = widgets
        self._table_controller: IPRTableController = dependencies.table_controller
        self._action_controller: MinerActionController = dependencies.action_controller
        self._asic: ASICClient = dependencies.asic
        self._auth_provider: AuthProvider = dependencies.auth_provider
        self._write_pool_preset: PresetWriter = dependencies.write_pool_preset
        self._toggling: bool = False

    def set_enabled(self, enabled: bool) -> None:
        self._widgets.get_pool_action.setEnabled(enabled)
        self._widgets.set_pool_action.setEnabled(enabled)
        self.set_visible(enabled)

    def set_visible(self, visible: bool = False) -> None:
        if self._toggling:
            return
        self._toggling = True
        try:
            self._widgets.show_action.setChecked(visible)
            self._table_controller.set_configurator_visible(visible)
            panel = self._widgets.panel
            if visible == (not panel.isHidden()):
                return

            delta = panel.sizeHint().height()
            panel.setVisible(visible)
            if self._window.isVisible() and not (
                self._window.isMaximized() or self._window.isFullScreen()
            ):
                if visible:
                    screen = self._window.screen()
                    available = screen.availableGeometry().height()
                    height = min(self._window.height() + delta, available)
                else:
                    height = max(
                        self._window.height() - delta,
                        self._window.minimumHeight(),
                    )
                self._window.resize(self._window.width(), height)
        finally:
            self._toggling = False

    def apply_configuration(self) -> None:
        match self._widgets.tabs.currentIndex():
            case 0:
                self._table_controller.request_pool_update()
            case 1:
                passwords = self._widgets.passwords
                if not self.validate_password_fields():
                    return
                if (
                    passwords.use_non_default.isChecked()
                    and passwords.current.text() == passwords.new.text()
                ):
                    self.notification_requested.emit(
                        "Status :: Failed action: Current password cannot be the same as the new password",
                        5000,
                    )
                    return
                self.update_miner_passwords()
            case 2:
                self.update_miner_firmware()
            case _:
                return

    def validate_password_fields(self) -> bool:
        passwords = self._widgets.passwords
        if not passwords.new.text() or not passwords.confirm.text():
            self.notification_requested.emit(
                "Status :: Failed action: Password fields are required", 5000
            )
            return False
        if passwords.confirm.text() != passwords.new.text():
            self.notification_requested.emit(
                "Status :: Failed action: Password fields do not match", 5000
            )
            return False
        return True

    def update_alternative_passwords(self) -> None:
        rows = self._table_controller.selected_source_rows(COL_IP)
        if not rows:
            self.notification_requested.emit(
                "Status :: Failed action: no selected IPs.", 5000
            )
            return
        if not self.validate_password_fields():
            return

        selected_types = {self._table_controller.miner_target(row)[1] for row in rows}
        type_names = sorted(miner_type.value for miner_type in selected_types)
        if len(selected_types) > 1:
            confirm = IPRMessage(
                self._window,
                "Confirm Alternative Password Update",
                "Update alternative password for selected "
                f"{', '.join(type_names)} miner types?",
                action_text="Update",
            )
            if confirm.exec() != QDialog.DialogCode.Accepted:
                return

        passwords = self._widgets.passwords
        new_password = passwords.new.text()
        for miner_type in selected_types:
            if miner_type == MinerType.VNISH:
                if (
                    MinerType.ANTMINER in selected_types
                    and passwords.use_antminer_login.isChecked()
                ):
                    continue
                if passwords.use_antminer_login.isChecked():
                    passwords.use_antminer_login.setChecked(False)
            field = passwords.alternatives.get(miner_type)
            if field is not None:
                field.setText(new_password)

        self.notification_requested.emit(
            "Status :: updated alternative password for "
            f"{', '.join(type_names)} in settings.",
            3000,
        )

    def get_miner_pool(self, source_row: int) -> None:
        self._action_controller.schedule(self._get_miner_pool(source_row))

    async def _get_miner_pool(self, source_row: int) -> None:
        ip_addr, miner_type, _ = self._table_controller.miner_target(source_row)
        alt_pwd = self._auth_provider(miner_type.value)
        result = await self._asic.get_miner_pool_conf(
            miner_type, ip_addr, alt_pwd=alt_pwd
        )
        if isinstance(result.error, UnknownClientError):
            logger.error(f"get_miner_pool : {result.error!s}")
            self.notification_requested.emit(
                f"Status :: Failed action: {result.error!s}", 5000
            )
            return
        if result.error:
            self.notification_requested.emit(
                f"Status :: Failed to get pool config: {result.error!s}", 5000
            )
            return

        pools = self._widgets.pools
        for field, value in zip(pools.urls, result.data.urls):
            field.setText(value)
        for field, value in zip(pools.users, result.data.users):
            field.setText(value)
        for field, value in zip(pools.passwords, result.data.passwds):
            field.setText(value)
        self._write_pool_preset()
        self.notification_requested.emit(
            f"Status :: Updated {pools.preset.currentText()} preset from {ip_addr}.",
            3000,
        )

    def update_miner_pools(self, rows: list[int]) -> None:
        self._action_controller.schedule(self._update_miner_pools(rows))

    async def _update_miner_pools(self, rows: list[int]) -> None:
        pools = self._widgets.pools
        urls = [field.text() for field in pools.urls]
        base_users = [field.text() for field in pools.users]
        passwords = [field.text() for field in pools.passwords]

        def make_coro(
            row: int,
            ip_addr: str,
            miner_type: MinerType,
            _firmware: MinerFirmware,
            alt_pwd: str | None,
        ) -> Awaitable[MinerResult]:
            users = base_users.copy()
            if pools.automatic_worker_names.isChecked():
                miner = self._table_controller.miner_at(row)
                worker_name = ""
                if miner.serial and miner.serial not in ("N/A", "Unknown"):
                    worker_name = f".{miner.serial[-5:]}"
                elif miner.mac and miner.mac != "N/A":
                    worker_name = f".{miner.mac.replace(':', '')[-5:]}"
                if worker_name:
                    users = [user + worker_name if user else user for user in users]
                else:
                    logger.warning(
                        "update_miner_pools : failed to find applicable worker name. Continuing.."
                    )
            return self._asic.update_miner_pools(
                miner_type,
                ip_addr,
                urls.copy(),
                users,
                passwords.copy(),
                alt_pwd=alt_pwd,
            )

        await self._action_controller.run_bulk_action("Update Pools", rows, make_coro)

    def update_miner_passwords(self) -> None:
        rows = self._table_controller.selected_source_rows_for_action(
            "update_miner_passwds", column=COL_IP
        )
        if not rows:
            self.notification_requested.emit(
                "Status :: Failed action: no selected IPs.", 5000
            )
            return
        self._action_controller.schedule(self._update_miner_passwords(rows))

    async def _update_miner_passwords(self, rows: list[int]) -> None:
        password_widgets = self._widgets.passwords
        current_text = password_widgets.current.text()
        new_text = password_widgets.new.text()

        def make_coro(
            _row: int,
            ip_addr: str,
            miner_type: MinerType,
            _firmware: MinerFirmware,
            _alt_pwd: str | None,
        ) -> Awaitable[MinerResult] | None:
            if miner_type in (
                MinerType.HAMMER,
                MinerType.GOLDSHELL,
                MinerType.VOLCMINER,
                MinerType.HIVEGPU,
            ):
                logger.error(
                    f"update_passwd : {miner_type.value} is currently not supported."
                )
                self.notification_requested.emit(
                    f"Status :: Skipping {ip_addr}: "
                    f"{miner_type.value.capitalize()} update password is not supported.",
                    5000,
                )
                return None

            current_password = current_text
            if not password_widgets.use_non_default.isChecked():
                default_auth = api_settings.get_auth(miner_type.value)
                if default_auth is None:
                    logger.error(
                        f"update_passwd : no default authentication for {miner_type.value}."
                    )
                    return None
                current_password = default_auth.default
            return self._asic.update_miner_passwd(
                miner_type,
                ip_addr,
                current_password,
                current_password,
                new_text,
            )

        await self._action_controller.run_bulk_action(
            "Update Passwords", rows, make_coro
        )

    def update_firmware_path(self) -> None:
        fd, _ = QFileDialog.getOpenFileName(
            self._window,
            "Select firmware file",
            str(self._widgets.firmware.firmware_path.text()),
            "Firmware Files (*.bmu *.bin)",
        )
        if not fd:
            return

        fw_file = QFile(fd)
        self._widgets.firmware.firmware_path.setText(fw_file.fileName())
        return

    def update_miner_firmware(self) -> None:
        rows = self._table_controller.selected_source_rows_for_action(
            "update_miner_firmware", column=COL_IP
        )
        if not rows:
            self.notification_requested.emit(
                "Status :: Failed action: no selected IPs.", 5000
            )
            return

        firmware_path = Path(self._widgets.firmware.firmware_path.text())
        try:
            firmware = BitmainFirmwareImage.from_path(firmware_path)
        except FirmwareImageError as e:
            logger.error(f"update_firmware : failed to load firmware image: {e!s}")
            self.notification_requested.emit(
                f"Status :: Invalid firmware image: {e!s}", 5000
            )
            return

        confirm = IPRMessage(
            self._window,
            "Confirm Miner Firmware Update",
            f"Update firmware for selected {len(rows)} miner(s)?",
            action_text="Update Firmware",
        )
        if confirm.exec() != QDialog.DialogCode.Accepted:
            return
        self._action_controller.schedule(self._update_miner_firmware(rows, firmware))

    async def _update_miner_firmware(
        self, rows: list[int], firmware: BitmainFirmwareImage
    ) -> None:
        firmware_widgets = self._widgets.firmware
        enforce_compatibility = firmware_widgets.enforce_compatibility.isChecked()
        keep_settings = firmware_widgets.keep_settings.isChecked()

        def make_coro(
            _row: int,
            ip_addr: str,
            miner_type: MinerType,
            _firmware: MinerFirmware,
            alt_pwd: str | None,
        ) -> Awaitable[MinerResult] | None:
            if miner_type is not MinerType.ANTMINER:
                logger.error(
                    f"update_firmware : {miner_type.value} is currently not supported."
                )
                self.notification_requested.emit(
                    f"Status :: Skipping {ip_addr}: "
                    f"{miner_type.value.capitalize()} firmware update is not supported.",
                    5000,
                )
                return None

            async def update() -> MinerResult:
                version_result = await self._asic.get_miner_version_info(
                    miner_type, ip_addr, alt_pwd=alt_pwd
                )
                if version_result.error is not None:
                    return version_result
                version_data = version_result.data
                if (
                    not isinstance(version_data, tuple)
                    or len(version_data) != 2
                    or not isinstance(version_data[1], AntminerVersionInfo)
                ):
                    return MinerResult(
                        error=APIError("Miner returned invalid version information")
                    )
                miner_info = version_data[1].miner_info
                if miner_info is None:
                    return MinerResult(
                        error=APIError(
                            "Miner did not report model and control board information"
                        )
                    )
                try:
                    payload = firmware.payload_for(
                        miner_info.miner_type,
                        miner_info.subtype,
                        enforce_compatibility=enforce_compatibility,
                    )
                except FirmwareImageError as e:
                    return MinerResult(error=e)
                return await self._asic.update_miner_firmware(
                    miner_type,
                    ip_addr,
                    payload.data,
                    keep_settings=keep_settings,
                    alt_pwd=alt_pwd,
                )

            return update()

        await self._action_controller.run_bulk_action(
            "Update Firmware", rows, make_coro
        )

    def reset_miner_firmware(self) -> None:
        rows = self._table_controller.selected_source_rows_for_action(
            "reset_miner_firmware", column=COL_IP
        )
        if not rows:
            self.notification_requested.emit(
                "Status :: Failed action: no selected IPs.", 5000
            )
            return
        confirm = IPRMessage(
            self._window,
            "Confirm Miner Firmware Reset",
            f"Reset firmware for selected {len(rows)} miner(s)?",
            action_text="Reset Firmware",
        )
        if confirm.exec() != QDialog.DialogCode.Accepted:
            return
        self._action_controller.schedule(self._reset_miner_firmware(rows))

    async def _reset_miner_firmware(self, rows: list[int]) -> None:
        def make_coro(
            _row: int,
            ip_addr: str,
            miner_type: MinerType,
            _firmware: MinerFirmware,
            alt_pwd: str | None,
        ) -> Awaitable[MinerResult] | None:
            if miner_type in (
                MinerType.HAMMER,
                MinerType.GOLDSHELL,
                MinerType.VOLCMINER,
                MinerType.IPOLLO,
                MinerType.HIVEGPU,
            ):
                logger.error(
                    f"reset_firmware : {miner_type.value} is currently not supported."
                )
                self.notification_requested.emit(
                    f"Status :: Skipping {ip_addr}: "
                    f"{miner_type.value.capitalize()} reset firmware is not supported.",
                    5000,
                )
                return None
            return self._asic.reset_miner_firmware(miner_type, ip_addr, alt_pwd=alt_pwd)

        await self._action_controller.run_bulk_action("Reset Firmware", rows, make_coro)

    def rollback_miner_firmware(self) -> None:
        rows = self._table_controller.selected_source_rows_for_action(
            "rollback_miner_firmware", column=COL_IP
        )
        if not rows:
            self.notification_requested.emit(
                "Status :: Failed action: no selected IPs.", 5000
            )
            return
        confirm = IPRMessage(
            self._window,
            "Confirm Miner Firmware Rollback",
            f"Rollback firmware back to stock firmware for selected {len(rows)} miner(s)?",
            action_text="Rollback",
        )
        if confirm.exec() != QDialog.DialogCode.Accepted:
            return
        self._action_controller.schedule(self._rollback_miner_firmware(rows))

    async def _rollback_miner_firmware(self, rows: list[int]) -> None:
        def make_coro(
            _row: int,
            ip_addr: str,
            miner_type: MinerType,
            _firmware: MinerFirmware,
            alt_pwd: str | None,
        ) -> Awaitable[MinerResult] | None:
            if miner_type not in (MinerType.VNISH, MinerType.LUX_OS):
                logger.error(
                    f"rollback_firmware : {miner_type.value} is currently not supported."
                )
                self.notification_requested.emit(
                    f"Status :: Skipping {ip_addr}: "
                    f"{miner_type.value.capitalize()} rollback firmware is not supported.",
                    5000,
                )
                return None
            return self._asic.rollback_miner_firmware(
                miner_type, ip_addr, alt_pwd=alt_pwd
            )

        await self._action_controller.run_bulk_action(
            "Rollback Firmware", rows, make_coro
        )
