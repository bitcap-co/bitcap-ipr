# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QToolButton, QWidget

from mod.ipr_asic import ASICClient, MinerResult
from mod.ipr_asic.data import MinerFirmware, MinerType
from mod.ipr_asic.errors import UnknownClientError

from .controller import IPRTableController
from .controlpopup import MinerControlPopup

logger = logging.getLogger(__name__)

AuthProvider = Callable[[str], str | None]
ActionCoroutine = Callable[
    [int, str, MinerType, MinerFirmware, str | None],
    Awaitable[MinerResult] | None,
]
ActionSuccess = Callable[[int, str, MinerResult], None]

_CONTROL_ACTIONS = {"start", "stop", "restart", "reboot"}


class MinerActionDependencies(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )

    table_controller: IPRTableController
    asic: ASICClient
    auth_provider: AuthProvider
    bulk_control_button: QToolButton
    locate_duration_ms: int


class MinerActionController(QObject):
    """Coordinates generic miner control, refresh, and locate operations."""

    notification_requested: Signal = Signal(str, int)

    def __init__(
        self,
        parent: QWidget,
        dependencies: MinerActionDependencies,
    ) -> None:
        super().__init__(parent)
        self._window: QWidget = parent
        self._table_controller: IPRTableController = dependencies.table_controller
        self._asic: ASICClient = dependencies.asic
        self._auth_provider: AuthProvider = dependencies.auth_provider
        self._bulk_control_button: QToolButton = dependencies.bulk_control_button
        self._locate_duration_ms: int = dependencies.locate_duration_ms
        self._locate_task: asyncio.Task[None] | None = None
        self._tasks: set[asyncio.Task[None]] = set()
        self._control_popup: MinerControlPopup | None = None
        self._stopping: bool = False

    def set_locate_duration_ms(self, duration_ms: int) -> None:
        self._locate_duration_ms = duration_ms

    def open_miner_control(self, source_row: int) -> None:
        popup = MinerControlPopup(self._window)
        popup.action_selected.connect(
            lambda key, row=source_row: self.dispatch_miner_control(row, key)
        )
        popup.destroyed.connect(self._clear_control_popup)
        self._control_popup = popup
        popup.show_at(self._table_controller.action_anchor(source_row))

    def open_bulk_control(self, *_args: object) -> None:
        popup = MinerControlPopup(self._window)
        popup.action_selected.connect(self._table_controller.request_bulk_action)
        popup.destroyed.connect(self._clear_control_popup)
        self._control_popup = popup
        button = self._bulk_control_button
        popup.show_at(button.mapToGlobal(button.rect().bottomLeft()))

    def _clear_control_popup(self, *_args: object) -> None:
        self._control_popup = None

    def dispatch_miner_control(self, source_row: int, key: str) -> None:
        if key == "refresh":
            self._schedule(self.refresh_miner(source_row))
        elif key == "locate":
            self._schedule(self.locate_miner(source_row))
        elif key in _CONTROL_ACTIONS:
            self._schedule(self.control_miner(source_row, key))
        else:
            logger.warning(f"dispatch_miner_control : unknown action '{key}'.")

    def dispatch_bulk_control(self, key: str, rows: list[int]) -> None:
        if key == "refresh":
            self._schedule(self.bulk_refresh_miners(rows))
        elif key == "locate":
            self._schedule(self.bulk_locate_miners(rows))
        elif key in _CONTROL_ACTIONS:
            self._schedule(self.bulk_control_miners(key, rows))
        else:
            logger.warning(f"dispatch_bulk_control : unknown action '{key}'.")

    def _schedule(self, coroutine: Coroutine[Any, Any, None]) -> None:
        if self._stopping:
            coroutine.close()
            return
        task = asyncio.ensure_future(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)

    def _on_task_done(self, task: asyncio.Task[None]) -> None:
        self._tasks.discard(task)
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            logger.error(
                f"miner action task failed: {error!s}",
                exc_info=(type(error), error, error.__traceback__),
            )

    async def control_miner(self, source_row: int, key: str) -> None:
        if key not in _CONTROL_ACTIONS:
            logger.warning(f"control_miner : unknown action '{key}'.")
            return
        ip_addr, miner_type, _ = self._table_controller.miner_target(source_row)
        logger.info(f"control_miner : '{key}' requested for {ip_addr}.")
        alt_pwd = self._auth_provider(miner_type.value)
        operation = getattr(self._asic, f"{key}_miner")
        result: MinerResult = await operation(miner_type, ip_addr, alt_pwd=alt_pwd)
        if result.error:
            logger.error(f"control_miner : {key} failed for {ip_addr}: {result.error}")
            self.notification_requested.emit(
                f"Status :: Failed to {key} {ip_addr}: {result.error!s}",
                5000,
            )
            return
        self.notification_requested.emit(
            f"Status :: Successfully completed {key} for {ip_addr}.",
            3000,
        )

    async def bulk_control_miners(self, key: str, rows: list[int]) -> None:
        if key not in _CONTROL_ACTIONS:
            logger.warning(f"bulk_control_miners : unknown action '{key}'.")
            return
        operation = getattr(self._asic, f"{key}_miner")

        def make_coro(
            _row: int,
            ip_addr: str,
            miner_type: MinerType,
            _firmware: MinerFirmware,
            alt_pwd: str | None,
        ) -> Awaitable[MinerResult]:
            return operation(miner_type, ip_addr, alt_pwd=alt_pwd)

        await self.run_bulk_action(key.capitalize(), rows, make_coro)

    async def run_bulk_action(
        self,
        action: str,
        rows: list[int],
        coroutine_factory: ActionCoroutine,
        *,
        on_success: ActionSuccess | None = None,
    ) -> None:
        ips: list[str] = []
        task_rows: list[int] = []
        operations: list[Awaitable[MinerResult]] = []
        for row in rows:
            ip_addr, miner_type, firmware = self._table_controller.miner_target(row)
            alt_pwd = self._auth_provider(miner_type.value)
            operation = coroutine_factory(row, ip_addr, miner_type, firmware, alt_pwd)
            if operation is None:
                continue
            ips.append(ip_addr)
            task_rows.append(row)
            operations.append(operation)
        if not operations:
            return

        if action == "Locate":
            self.notification_requested.emit(
                f"Status :: {action} started for {self._locate_duration_ms / 1000}s.",
                self._locate_duration_ms,
            )
        results = await asyncio.gather(*operations, return_exceptions=True)
        if self._stopping:
            return

        passed: list[str] = []
        failed: list[str] = []
        for row, ip_addr, result in zip(task_rows, ips, results):
            if isinstance(result, BaseException) or result.error is not None:
                error = result if isinstance(result, BaseException) else result.error
                logger.error(f"{action} : {ip_addr} : {error!s}")
                failed.append(ip_addr)
                continue
            if on_success is not None:
                on_success(row, ip_addr, result)
            passed.append(ip_addr)

        logger.info(
            f"status for action '{action}': passed - {passed}, failed - {failed}"
        )
        if failed:
            self.notification_requested.emit(
                f"Status :: {action} failed for {failed}.", 5000
            )
            return
        self.notification_requested.emit(
            f"Status :: {action} succeeded for {len(passed)} miners.", 3000
        )

    async def _locate_rows(self, rows: list[int]) -> None:
        def make_coro(
            _row: int,
            ip_addr: str,
            miner_type: MinerType,
            _firmware: MinerFirmware,
            alt_pwd: str | None,
        ) -> Awaitable[MinerResult] | None:
            if miner_type in (
                MinerType.VOLCMINER,
                MinerType.HIVEGPU,
                MinerType.IPOLLO,
            ):
                logger.error(f"locate : {miner_type.value} is currently not supported.")
                self.notification_requested.emit(
                    f"Status :: Skipping {ip_addr}: "
                    f"{miner_type.value.capitalize()} locate is not supported.",
                    5000,
                )
                return None
            return self._asic.locate_miner(miner_type, ip_addr, alt_pwd=alt_pwd)

        await self.run_bulk_action("Locate", rows, make_coro)

    async def _start_locate(self, rows: list[int]) -> None:
        if not rows:
            return
        if self._locate_task and not self._locate_task.done():
            self._locate_task.cancel()
            try:
                await self._locate_task
            except asyncio.CancelledError:
                pass
        self._locate_task = asyncio.ensure_future(self._locate_rows(rows))
        try:
            await self._locate_task
        except asyncio.CancelledError:
            return
        finally:
            self._locate_task = None

    async def locate_miner(self, source_row: int) -> None:
        await self._start_locate([source_row])

    async def bulk_locate_miners(self, rows: list[int]) -> None:
        await self._start_locate(rows)

    async def refresh_miner(self, source_row: int) -> None:
        ip_addr, miner_type, _ = self._table_controller.miner_target(source_row)
        logger.info(f"refresh_miner : refresh miner {ip_addr}.")
        updated_type = await self._asic._parse_http_type(ip_addr)
        if updated_type is not None and updated_type != miner_type:
            miner_type = updated_type
        alt_pwd = self._auth_provider(miner_type.value)
        result = await self._asic.get_miner_data(miner_type, ip_addr, alt_pwd=alt_pwd)
        if isinstance(result.error, UnknownClientError):
            logger.error(f"refresh_miner : {result.error!s}")
            self.notification_requested.emit(
                f"Status :: Failed action: {result.error!s}", 5000
            )
            return
        if result.error:
            self.notification_requested.emit(
                f"Status :: Failed to get complete miner data {ip_addr}: "
                f"{result.error!s}",
                5000,
            )
            return
        self._update_refreshed_row(source_row, ip_addr, result)
        self.notification_requested.emit(
            f"Status :: Successfully refreshed {ip_addr} miner data.", 3000
        )

    async def bulk_refresh_miners(self, rows: list[int]) -> None:
        async def make_coro(
            _row: int,
            ip_addr: str,
            miner_type: MinerType,
            _firmware: MinerFirmware,
            alt_pwd: str | None,
        ) -> MinerResult:
            updated_type = await self._asic._parse_http_type(ip_addr)
            if updated_type is not None and updated_type != miner_type:
                miner_type = updated_type
                alt_pwd = self._auth_provider(miner_type.value)
            return await self._asic.get_miner_data(
                miner_type,
                ip_addr,
                alt_pwd=alt_pwd,
            )

        def on_success(row: int, ip_addr: str, result: MinerResult) -> None:
            self._update_refreshed_row(row, ip_addr, result)

        await self.run_bulk_action("Refresh", rows, make_coro, on_success=on_success)

    def _update_refreshed_row(
        self, source_row: int, ip_addr: str, result: MinerResult
    ) -> None:
        miner_data = result.data
        miner_data["recv_at"] = int(time.time())
        miner_data["ip"] = ip_addr
        miner_data["mac"] = (
            miner_data["mac"].lower() if miner_data["mac"] != "N/A" else "N/A"
        )
        self._table_controller.populate_data(miner_data, source_row)

    def stop(self) -> None:
        self._stopping = True
        if self._control_popup is not None:
            self._control_popup.close()
            self._control_popup = None
        if self._locate_task is not None and not self._locate_task.done():
            self._locate_task.cancel()
        for task in tuple(self._tasks):
            task.cancel()
