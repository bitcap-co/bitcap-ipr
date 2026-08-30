# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for miner action orchestration and the retained pool bridge."""

import asyncio
import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock, call

import config  # noqa: F401  # initialize Pydantic before importing PySide-backed IPR
from mod.ipr_asic import MinerResult
from mod.ipr_asic.data import MinerFirmware, MinerType
from mod.ipr_asic.errors import APIError
from ui.widgets import MinerActionController, MinerConfiguratorController


class _ControlFacade:
    def __init__(self, result: MinerResult | None = None) -> None:
        self.result = result or MinerResult(data={"success": True})
        self.calls: list[tuple[str, MinerType, str, str | None]] = []

    async def start_miner(self, miner_type, ip, alt_pwd=None):
        self.calls.append(("start", miner_type, ip, alt_pwd))
        return self.result

    async def reboot_miner(self, miner_type, ip, alt_pwd=None):
        self.calls.append(("reboot", miner_type, ip, alt_pwd))
        return self.result


class TestMinerActionController(unittest.IsolatedAsyncioTestCase):
    async def test_single_control_forwards_target_and_auth(self):
        facade = _ControlFacade()
        subject: Any = SimpleNamespace(
            _asic=facade,
            _table_controller=SimpleNamespace(
                miner_target=Mock(
                    return_value=(
                        "10.0.0.1",
                        MinerType.ANTMINER,
                        MinerFirmware.STOCK,
                    )
                )
            ),
            _auth_provider=Mock(return_value="secret"),
            notification_requested=Mock(),
        )

        await MinerActionController.control_miner(subject, 4, "start")

        subject._table_controller.miner_target.assert_called_once_with(4)
        subject._auth_provider.assert_called_once_with(MinerType.ANTMINER.value)
        self.assertEqual(
            facade.calls,
            [("start", MinerType.ANTMINER, "10.0.0.1", "secret")],
        )
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Successfully completed start for 10.0.0.1.",
            3000,
        )

    async def test_single_control_reports_facade_error(self):
        error = APIError("command failed")
        facade = _ControlFacade(MinerResult(error=error))
        subject: Any = SimpleNamespace(
            _asic=facade,
            _table_controller=SimpleNamespace(
                miner_target=Mock(
                    return_value=(
                        "10.0.0.2",
                        MinerType.ANTMINER,
                        MinerFirmware.STOCK,
                    )
                )
            ),
            _auth_provider=Mock(return_value=None),
            notification_requested=Mock(),
        )

        await MinerActionController.control_miner(subject, 1, "start")

        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Failed to start 10.0.0.2: command failed",
            5000,
        )

    async def test_bulk_control_uses_shared_bulk_engine(self):
        facade = _ControlFacade()
        run_bulk_action = AsyncMock()
        subject: Any = SimpleNamespace(
            _asic=facade,
            run_bulk_action=run_bulk_action,
        )

        await MinerActionController.bulk_control_miners(subject, "reboot", [2, 5])

        run_bulk_action.assert_awaited_once()
        awaited = run_bulk_action.await_args
        if awaited is None:
            self.fail("bulk action was not awaited")
        action, rows, make_coro = awaited.args
        self.assertEqual(action, "Reboot")
        self.assertEqual(rows, [2, 5])

        result = await make_coro(
            2,
            "10.0.0.3",
            MinerType.ANTMINER,
            MinerFirmware.STOCK,
            "secret",
        )
        self.assertTrue(result.ok)
        self.assertEqual(
            facade.calls,
            [("reboot", MinerType.ANTMINER, "10.0.0.3", "secret")],
        )

    async def test_bulk_action_maps_rows_auth_and_results(self):
        success = MinerResult(data={"success": True})
        failure = MinerResult(error=APIError("offline"))
        table_controller = SimpleNamespace(
            miner_target=Mock(
                side_effect=[
                    ("10.0.0.10", MinerType.ANTMINER, MinerFirmware.STOCK),
                    ("10.0.0.11", MinerType.VNISH, MinerFirmware.VNISH),
                ]
            )
        )
        auth_provider = Mock(side_effect=["ant-secret", "vnish-secret"])
        coroutine_factory = Mock(
            side_effect=[
                self._result(success),
                self._result(failure),
            ]
        )
        on_success = Mock()
        subject: Any = SimpleNamespace(
            _table_controller=table_controller,
            _auth_provider=auth_provider,
            _locate_duration_ms=5000,
            _stopping=False,
            notification_requested=Mock(),
        )

        await MinerActionController.run_bulk_action(
            subject,
            "Refresh",
            [2, 6],
            coroutine_factory,
            on_success=on_success,
        )

        self.assertEqual(
            table_controller.miner_target.call_args_list,
            [call(2), call(6)],
        )
        self.assertEqual(
            auth_provider.call_args_list,
            [
                call(MinerType.ANTMINER.value),
                call(MinerType.VNISH.value),
            ],
        )
        on_success.assert_called_once_with(2, "10.0.0.10", success)
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Refresh failed for ['10.0.0.11'].", 5000
        )

    @staticmethod
    async def _result(result: MinerResult) -> MinerResult:
        return result

    async def test_refresh_updates_source_row_and_reports_success(self):
        result = MinerResult(data={"mac": "AA:BB:CC:DD:EE:FF"})
        table_controller = SimpleNamespace(
            miner_target=Mock(
                return_value=(
                    "10.0.0.12",
                    MinerType.VNISH,
                    MinerFirmware.VNISH,
                )
            ),
            populate_data=Mock(),
        )
        asic = SimpleNamespace(
            _parse_http_type=AsyncMock(return_value=MinerType.ANTMINER),
            get_miner_data=AsyncMock(return_value=result),
        )
        subject: Any = SimpleNamespace(
            _asic=asic,
            _table_controller=table_controller,
            _auth_provider=Mock(return_value="secret"),
            _update_refreshed_row=lambda row, ip, refreshed: (
                MinerActionController._update_refreshed_row(subject, row, ip, refreshed)
            ),
            notification_requested=Mock(),
        )

        await MinerActionController.refresh_miner(subject, 8)

        subject._auth_provider.assert_called_once_with(MinerType.ANTMINER.value)
        asic.get_miner_data.assert_awaited_once_with(
            MinerType.ANTMINER,
            "10.0.0.12",
            alt_pwd="secret",
        )
        table_controller.populate_data.assert_called_once()
        populated_data, source_row = table_controller.populate_data.call_args.args
        self.assertEqual(source_row, 8)
        self.assertEqual(populated_data["ip"], "10.0.0.12")
        self.assertEqual(populated_data["mac"], "aa:bb:cc:dd:ee:ff")
        self.assertIsInstance(populated_data["recv_at"], int)
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Successfully refreshed 10.0.0.12 miner data.", 3000
        )

    async def test_unsupported_locate_is_skipped(self):
        run_bulk_action = AsyncMock()
        subject: Any = SimpleNamespace(
            _asic=SimpleNamespace(locate_miner=Mock()),
            run_bulk_action=run_bulk_action,
            notification_requested=Mock(),
        )

        await MinerActionController._locate_rows(subject, [4])

        awaited = run_bulk_action.await_args
        if awaited is None:
            self.fail("locate bulk action was not awaited")
        action, rows, make_coro = awaited.args
        self.assertEqual(action, "Locate")
        self.assertEqual(rows, [4])
        operation = make_coro(
            4,
            "10.0.0.13",
            MinerType.IPOLLO,
            MinerFirmware.STOCK,
            None,
        )
        self.assertIsNone(operation)
        subject._asic.locate_miner.assert_not_called()
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Skipping 10.0.0.13: Ipollo locate is not supported.",
            5000,
        )

    async def test_stop_cancels_locate_and_scheduled_tasks(self):
        loop = asyncio.get_running_loop()
        locate_task = loop.create_task(self._wait_forever())
        scheduled_task = loop.create_task(self._wait_forever())
        subject: Any = SimpleNamespace(
            _stopping=False,
            _control_popup=None,
            _locate_task=locate_task,
            _tasks={scheduled_task},
        )

        MinerActionController.stop(subject)
        await asyncio.sleep(0)

        self.assertTrue(subject._stopping)
        self.assertTrue(locate_task.cancelled())
        self.assertTrue(scheduled_task.cancelled())

    @staticmethod
    async def _wait_forever() -> None:
        await asyncio.Event().wait()

    async def test_bulk_refresh_redetects_type_and_auth_before_fetch(self):
        result = MinerResult(data={"type": "antminer", "mac": "N/A"})
        asic = SimpleNamespace(
            _parse_http_type=AsyncMock(return_value=MinerType.ANTMINER),
            get_miner_data=AsyncMock(return_value=result),
        )
        run_bulk_action = AsyncMock()
        subject: Any = SimpleNamespace(
            _asic=asic,
            _auth_provider=Mock(return_value="antminer-secret"),
            run_bulk_action=run_bulk_action,
        )

        await MinerActionController.bulk_refresh_miners(subject, [3])

        awaited = run_bulk_action.await_args
        if awaited is None:
            self.fail("bulk refresh was not awaited")
        action, rows, make_coro = awaited.args
        self.assertEqual(action, "Refresh")
        self.assertEqual(rows, [3])

        refresh_result = await make_coro(
            3,
            "10.0.0.4",
            MinerType.VNISH,
            MinerFirmware.VNISH,
            "vnish-secret",
        )

        self.assertIs(refresh_result, result)
        asic._parse_http_type.assert_awaited_once_with("10.0.0.4")
        subject._auth_provider.assert_called_once_with(MinerType.ANTMINER.value)
        asic.get_miner_data.assert_awaited_once_with(
            MinerType.ANTMINER,
            "10.0.0.4",
            alt_pwd="antminer-secret",
        )


class TestMinerConfiguratorController(unittest.IsolatedAsyncioTestCase):
    async def test_update_pools_uses_action_controller_bulk_engine(self):
        result = MinerResult(data={"success": True})
        asic = SimpleNamespace(update_miner_pools=AsyncMock(return_value=result))
        run_bulk_action = AsyncMock()

        def field(value):
            widget = Mock()
            widget.text.return_value = value
            return widget

        pool_widgets = SimpleNamespace(
            urls=(
                field("stratum://pool-1"),
                field("stratum://pool-2"),
                field(""),
            ),
            users=(field("account.worker"), field("backup"), field("")),
            passwords=(field("x"), field("y"), field("")),
            automatic_worker_names=Mock(),
        )
        subject: Any = SimpleNamespace(
            _asic=asic,
            _action_controller=SimpleNamespace(run_bulk_action=run_bulk_action),
            _table_controller=SimpleNamespace(miner_at=Mock()),
            _widgets=SimpleNamespace(pools=pool_widgets),
        )
        subject._table_controller.miner_at.return_value = SimpleNamespace(
            serial="ANTMINER12345",
            mac="aa:bb:cc:dd:ee:ff",
        )
        pool_widgets.automatic_worker_names.isChecked.return_value = True

        await MinerConfiguratorController._update_miner_pools(subject, [7])

        awaited = run_bulk_action.await_args
        if awaited is None:
            self.fail("pool update bulk action was not awaited")
        action, rows, make_coro = awaited.args
        self.assertEqual(action, "Update Pools")
        self.assertEqual(rows, [7])

        update_result = await make_coro(
            7,
            "10.0.0.5",
            MinerType.ANTMINER,
            MinerFirmware.STOCK,
            "secret",
        )

        self.assertIs(update_result, result)
        asic.update_miner_pools.assert_awaited_once_with(
            MinerType.ANTMINER,
            "10.0.0.5",
            ["stratum://pool-1", "stratum://pool-2", ""],
            ["account.worker.12345", "backup.12345", ""],
            ["x", "y", ""],
            alt_pwd="secret",
        )

    async def test_get_pool_populates_fields_and_writes_preset(self):
        def fields():
            return tuple(Mock() for _ in range(3))

        urls = fields()
        users = fields()
        passwords = fields()
        pools = SimpleNamespace(
            preset=Mock(),
            urls=urls,
            users=users,
            passwords=passwords,
        )
        pools.preset.currentText.return_value = "Production"
        result = SimpleNamespace(
            error=None,
            data=SimpleNamespace(
                urls=["url-1", "url-2", "url-3"],
                users=["user-1", "user-2", "user-3"],
                passwds=["pass-1", "pass-2", "pass-3"],
            ),
        )
        subject: Any = SimpleNamespace(
            _table_controller=SimpleNamespace(
                miner_target=Mock(
                    return_value=(
                        "10.0.0.20",
                        MinerType.ANTMINER,
                        MinerFirmware.STOCK,
                    )
                )
            ),
            _auth_provider=Mock(return_value="secret"),
            _asic=SimpleNamespace(get_miner_pool_conf=AsyncMock(return_value=result)),
            _widgets=SimpleNamespace(pools=pools),
            _write_pool_preset=Mock(),
            notification_requested=Mock(),
        )

        await MinerConfiguratorController._get_miner_pool(subject, 3)

        for field, value in zip(urls, result.data.urls):
            field.setText.assert_called_once_with(value)
        for field, value in zip(users, result.data.users):
            field.setText.assert_called_once_with(value)
        for field, value in zip(passwords, result.data.passwds):
            field.setText.assert_called_once_with(value)
        subject._write_pool_preset.assert_called_once_with()
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Updated Production preset from 10.0.0.20.", 3000
        )

    def test_password_validation_rejects_mismatched_fields(self):
        new = Mock()
        confirm = Mock()
        new.text.return_value = "new-password"
        confirm.text.return_value = "different-password"
        subject: Any = SimpleNamespace(
            _widgets=SimpleNamespace(
                passwords=SimpleNamespace(new=new, confirm=confirm)
            ),
            notification_requested=Mock(),
        )

        valid = MinerConfiguratorController.validate_password_fields(subject)

        self.assertFalse(valid)
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Failed action: Password fields do not match", 5000
        )

    def test_update_pools_is_scheduled_by_action_controller(self):
        scheduled = []

        def schedule(coroutine):
            scheduled.append(coroutine)

        async def update(rows):
            return None

        subject: Any = SimpleNamespace(
            _action_controller=SimpleNamespace(schedule=schedule),
            _update_miner_pools=update,
        )

        MinerConfiguratorController.update_miner_pools(subject, [1, 4])

        self.assertEqual(len(scheduled), 1)
        scheduled[0].close()


if __name__ == "__main__":
    unittest.main()
